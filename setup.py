"""
KiCad PCB Generator package configuration.
"""
from setuptools import setup, find_packages
import os

# Read version from VERSION file
with open("VERSION", "r") as f:
    version = f.read().strip()

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="kicad-pcb-generator",
    version=version,
    author="KiCad PCB Generator Team",
    author_email="support@kicad-pcb-generator.org",
    description="A tool for automating and validating PCB designs in KiCad",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kicad-pcb-generator/kicad-pcb-generator",
    project_urls={
        "Documentation": "https://kicad-pcb-generator.readthedocs.io/",
        "Source": "https://github.com/kicad-pcb-generator/kicad-pcb-generator",
        "Tracker": "https://github.com/kicad-pcb-generator/kicad-pcb-generator/issues",
        "Discord": "https://discord.gg/kicad-pcb-generator",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
            "pytest-cov>=3.0.0",
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "gui": [
            "wxPython>=4.2.0",
        ],
        "manufacturing": [
            "kikit>=1.0.0",
            "pcbdraw>=0.9.0",
            "gerber2blend>=0.1.0",
        ],
        "simulation": [
            "ngspice>=39.0",
        ],
        "full": [
            "wxPython>=4.2.0",
            "kikit>=1.0.0",
            "pcbdraw>=0.9.0",
            "gerber2blend>=0.1.0",
            "ngspice>=39.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kicad-pcb-generator=kicad_pcb_generator.cli:main",
        ],
        "gui_scripts": [
            "kicad-pcb-generator-gui=kicad_pcb_generator.gui:main",
        ],
    },
    package_data={
        "kicad_pcb_generator": [
            "templates/*",
            "examples/*",
            "docs/*",
            "icons/*",
            "config/*.yaml",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 