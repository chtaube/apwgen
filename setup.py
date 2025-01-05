#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages


setup(
    name="apwgen",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    entry_points={"console_scripts": ["apwgen=apwgen.apwgen:main"]},
)

