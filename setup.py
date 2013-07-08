#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages


def read(name):
    from os import path
    return open(path.join(path.dirname(__file__), name)).read()

setup(
    name='facebook-opengraph-action',
    version='0.2.3',
    maintainer="Tomasz Wysocki",
    maintainer_email="tomasz@wysocki.info",
    packages=find_packages(),
    include_package_data=True,
    long_description=read("README.rst"),
)
