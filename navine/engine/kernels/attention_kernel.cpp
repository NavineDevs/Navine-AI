#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <torch/extension.h>
#include <cmath>

namespace py = pybind11;

torch::Tensor fused_sdpa(
    torch::Tensor q,
    torch::Tensor k,
    torch::Tensor v,
    py::object scale_obj,
    bool causal
) {
    float sc;
    if (scale_obj.is_none()) {
        sc = 1.0f / std::sqrt(static_cast<float>(q.size(-1)));
    } else {
        sc = scale_obj.cast<float>();
    }

    auto scores = torch::matmul(q, k.transpose(-2, -1)) * sc;

    if (causal) {
        int S = scores.size(-1);
        auto mask = torch::ones({S, S}, scores.options()).triu(1).to(torch::kBool);
        scores.masked_fill_(mask, -1e9f);
    }

    auto attn = torch::softmax(scores, -1);
    return torch::matmul(attn, v);
}

PYBIND11_MODULE(_attention_kernel, m) {
    m.def("fused_sdpa", &fused_sdpa,
          py::arg("q"), py::arg("k"), py::arg("v"),
          py::arg("scale") = py::none(), py::arg("causal") = true);
}
