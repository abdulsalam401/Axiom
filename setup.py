#!/usr/bin/env python3
"""
Axiom — Setup Script
Author: Abdul Salam | Salamcs.app
"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="axiom-android",
    version="2.1.0",
    description="Advanced Android Security Assessment Framework (Matrix Cyber HUD Edition)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Abdul Salam",
    author_email="contact@salamcs.app",
    url="https://github.com/abdulsalam401/Axiom",
    py_modules=["axiom", "bt_scanner"],
    packages=find_packages(include=["modules*"]),
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "requests>=2.31.0",
        "colorama>=0.4.6",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "bluetooth": ["bleak>=0.21.0"],
        "full": ["bleak>=0.21.0", "frida-tools>=12.0.0"],
    },
    entry_points={
        "console_scripts": [
            "axiom=axiom:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
    ],
)
