"""Setup file for about-this-mac package."""
from setuptools import setup, find_packages

setup(
    name="about-this-mac",
    version="0.1.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyYAML>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "pylint>=2.17.5",
            "mypy>=1.5.1",
        ],
    },
    python_requires=">=3.8",
) 