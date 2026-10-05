use pyo3::prelude::*;


#[pyfunction]
fn matmul(a: Vec<Vec<f64>>, b: Vec<Vec<f64>>) -> PyResult<Vec<Vec<f64>>> {
    if a.is_empty() || b.is_empty() {
        return Ok(vec![]);
    }
    let cols = b[0].len();
    let mut out = Vec::with_capacity(a.len());
    for row in &a {
        let mut out_row = Vec::with_capacity(cols);
        for j in 0..cols {
            let mut s = 0.0_f64;
            for (k, av) in row.iter().enumerate() {
                if k < b.len() && j < b[k].len() {
                    s += av * b[k][j];
                }
            }
            out_row.push(s);
        }
        out.push(out_row);
    }
    Ok(out)
}

#[pyclass]
struct KvCache {
    capacity: usize,
    items: Vec<(PyObject, PyObject)>,
}

#[pymethods]
impl KvCache {
    #[new]
    fn new(capacity: usize) -> Self {
        Self {
            capacity: capacity.max(1),
            items: Vec::new(),
        }
    }

    fn push(&mut self, key: PyObject, value: PyObject) {
        self.items.push((key, value));
        if self.items.len() > self.capacity {
            let drop_n = self.items.len() - self.capacity;
            self.items.drain(0..drop_n);
        }
    }

    fn len(&self) -> usize {
        self.items.len()
    }

    fn last(&self, py: Python<'_>) -> PyResult<Option<(PyObject, PyObject)>> {
        match self.items.last() {
            Some((k, v)) => Ok(Some((k.clone_ref(py), v.clone_ref(py)))),
            None => Ok(None),
        }
    }
}

#[pymodule]
fn navops(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(matmul, m)?)?;
    m.add_class::<KvCache>()?;
    Ok(())
}
