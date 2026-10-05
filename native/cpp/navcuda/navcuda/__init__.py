"""Pure-Python navcuda API with optional C extension acceleration."""

from __future__ import annotations

import math
from typing import List, Sequence, Union

ArrayLike = Union[float, Sequence[float]]


def make_betas(timesteps: int, beta_start: float, beta_end: float, schedule: str = "linear") -> List[float]:
    t = max(1, int(timesteps))
    schedule = (schedule or "linear").lower()
    if schedule == "cosine":
        s = 0.008

        def alpha_bar(u: float) -> float:
            return math.cos((u + s) / (1.0 + s) * math.pi * 0.5) ** 2

        betas = []
        for i in range(t):
            t1 = i / t
            t2 = (i + 1) / t
            a1 = max(alpha_bar(t1), 1e-8)
            a2 = max(alpha_bar(t2), 1e-8)
            betas.append(min(1.0 - a2 / a1, 0.999))
        return betas
    if schedule == "sigmoid":
        xs = [i / max(t - 1, 1) for i in range(t)]

        def sig(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-12.0 * (x - 0.5)))

        lo, hi = sig(0.0), sig(1.0)
        return [
            float(beta_start + (beta_end - beta_start) * ((sig(x) - lo) / (hi - lo + 1e-12)))
            for x in xs
        ]
    if t == 1:
        return [float(beta_start)]
    return [float(beta_start + (beta_end - beta_start) * i / (t - 1)) for i in range(t)]


def ddim_step(x, alpha_bar_t, alpha_bar_prev, pred_noise):
    try:
        from navcuda import _native  # type: ignore

        return _native.ddim_step(x, alpha_bar_t, alpha_bar_prev, pred_noise)
    except Exception:
        pass
    import torch

    ab_t = alpha_bar_t if isinstance(alpha_bar_t, torch.Tensor) else torch.as_tensor(alpha_bar_t, device=x.device, dtype=x.dtype)
    ab_p = alpha_bar_prev if isinstance(alpha_bar_prev, torch.Tensor) else torch.as_tensor(alpha_bar_prev, device=x.device, dtype=x.dtype)
    pred_x0 = (x - torch.sqrt(1.0 - ab_t) * pred_noise) / torch.sqrt(ab_t + 1e-8)
    pred_x0 = pred_x0.clamp(-1.0, 1.0)
    return torch.sqrt(ab_p) * pred_x0 + torch.sqrt(1.0 - ab_p) * pred_noise
