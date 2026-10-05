from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="navops",
    version="0.1.0",
    rust_extensions=[RustExtension("navops.navops", binding=Binding.PyO3, path="Cargo.toml")],
    packages=["navops"],
    zip_safe=False,
    python_requires=">=3.10",
)
