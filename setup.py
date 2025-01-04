# setup.py
from setuptools import setup, find_packages

setup(
    name="apwgen",
    version="1.1.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["apwgen=apwgen.apwgen:main"]},
)

