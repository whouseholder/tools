from setuptools import setup, find_packages

setup(
    name="iceberg-metadata-sync",
    version="0.1.0",
    description="Incremental metadata sync for Apache Iceberg tables",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pyspark>=3.2.0,<3.6.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "chispa>=0.9.3",
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "iceberg-sync=src.sync_manager:main",
        ]
    },
)

