import glob
import shutil

from setuptools import setup
from setuptools.command import install


setup(
    name="villard",
    version="0.1.1",
    author="Aria Ghora Prabono",
    author_email="hello@ghora.net",
    description="A tiny layer to organize your data science project",
    license="MIT",
    packages=["villard", "villard.explorer"],
    scripts=["bin/villard"],
    include_package_data=True,
)
