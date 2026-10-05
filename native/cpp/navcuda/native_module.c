#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <string.h>

static PyObject *navcuda_make_betas(PyObject *self, PyObject *args) {
    long timesteps;
    double beta_start, beta_end;
    const char *schedule = "linear";
    if (!PyArg_ParseTuple(args, "ldd|s", &timesteps, &beta_start, &beta_end, &schedule)) {
        return NULL;
    }
    if (timesteps < 1) timesteps = 1;
    PyObject *list = PyList_New((Py_ssize_t)timesteps);
    if (!list) return NULL;
    for (long i = 0; i < timesteps; i++) {
        double b;
        if (schedule && strcmp(schedule, "cosine") == 0) {
            double s = 0.008;
            double t1 = (double)i / (double)timesteps;
            double t2 = (double)(i + 1) / (double)timesteps;
            double a1 = cos((t1 + s) / (1.0 + s) * 3.141592653589793 * 0.5);
            double a2 = cos((t2 + s) / (1.0 + s) * 3.141592653589793 * 0.5);
            a1 = a1 * a1; a2 = a2 * a2;
            if (a1 < 1e-8) a1 = 1e-8;
            b = 1.0 - a2 / a1;
            if (b > 0.999) b = 0.999;
        } else if (schedule && strcmp(schedule, "sigmoid") == 0) {
            double x = (timesteps == 1) ? 0.0 : (double)i / (double)(timesteps - 1);
            double sx = 1.0 / (1.0 + exp(-12.0 * (x - 0.5)));
            double lo = 1.0 / (1.0 + exp(6.0));
            double hi = 1.0 / (1.0 + exp(-6.0));
            b = beta_start + (beta_end - beta_start) * ((sx - lo) / (hi - lo + 1e-12));
        } else {
            b = (timesteps == 1) ? beta_start
                : beta_start + (beta_end - beta_start) * (double)i / (double)(timesteps - 1);
        }
        PyList_SET_ITEM(list, (Py_ssize_t)i, PyFloat_FromDouble(b));
    }
    return list;
}

static PyMethodDef Methods[] = {
    {"make_betas", navcuda_make_betas, METH_VARARGS, "Beta schedule values"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_native",
    "Navine/Navine C schedule helpers",
    -1,
    Methods
};

PyMODINIT_FUNC PyInit__native(void) {
    return PyModule_Create(&moduledef);
}
