use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use numpy::{PyArray2, PyReadonlyArray2};

#[pyfunction]
fn apply_rope(
    x: PyReadonlyArray2<f32>,
    cos: PyReadonlyArray2<f32>,
    sin: PyReadonlyArray2<f32>,
) -> PyResult<Py<PyArray2<f32>>> {
    let x = x.as_array();
    let cos = cos.as_array();
    let sin = sin.as_array();

    let (rows, cols) = x.dim();
    if cols % 2 != 0 {
        return Err(PyValueError::new_err("dim must be even"));
    }

    Python::with_gil(|py| {
        let out = PyArray2::<f32>::zeros(py, [rows, cols], false);
        let mut out_rw = unsafe { out.as_array_mut() };

        for r in 0..rows {
            for c in (0..cols).step_by(2) {
                let x1 = x[[r, c]];
                let x2 = x[[r, c + 1]];
                let co = cos[[r, c / 2]];
                let si = sin[[r, c / 2]];
                out_rw[[r, c]] = x1 * co - x2 * si;
                out_rw[[r, c + 1]] = x1 * si + x2 * co;
            }
        }
        Ok(out.into())
    })
}

#[pyfunction]
fn rms_norm(
    x: PyReadonlyArray2<f32>,
    weight: PyReadonlyArray2<f32>,
    eps: f32,
) -> PyResult<Py<PyArray2<f32>>> {
    let x = x.as_array();
    let w = weight.as_array();
    let (rows, cols) = x.dim();

    Python::with_gil(|py| {
        let out = PyArray2::<f32>::zeros(py, [rows, cols], false);
        let mut out_rw = unsafe { out.as_array_mut() };

        for r in 0..rows {
            let mut sq_sum: f32 = 0.0;
            for c in 0..cols {
                sq_sum += x[[r, c]] * x[[r, c]];
            }
            let rms = (sq_sum / cols as f32 + eps).sqrt();
            for c in 0..cols {
                out_rw[[r, c]] = x[[r, c]] / rms * w[[0, c]];
            }
        }
        Ok(out.into())
    })
}

#[pymodule]
fn _fast_ops(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(apply_rope, m)?)?;
    m.add_function(wrap_pyfunction!(rms_norm, m)?)?;
    Ok(())
}
