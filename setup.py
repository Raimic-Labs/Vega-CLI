"""
setup.py — Legacy setup file for compatibility.
Primary build config is in pyproject.toml.
Running `pip install -e .` reads pyproject.toml automatically.
"""

from setuptools import setup

# All configuration is in pyproject.toml.
# This file exists for tools that require setup.py to be present.
setup()
