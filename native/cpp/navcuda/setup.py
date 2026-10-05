from setuptools import Extension, setup

setup(
    name="navcuda",
    version="0.1.0",
    packages=["navcuda"],
    ext_modules=[
        Extension("navcuda._native", sources=["native_module.c"]),
    ],
    python_requires=">=3.10",
    zip_safe=False,
)
