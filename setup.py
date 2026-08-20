import subprocess
import sys
from setuptools import setup, find_packages

# Optional: Run the custom install script for PyTorch if needed
# subprocess.check_call([sys.executable, "app/install.py"])

setup(
    name="photo_template_studio",
    version="1.0.0",
    packages=find_packages(include=["app", "app.*"]),
    install_requires=[
        "PySide6>=6.5.0",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "PyMuPDF>=1.23.0",
        "pillow-heif>=0.13.0",
        "cairosvg>=2.7.0"
    ],
    entry_points={
        "console_scripts": [
            "photo-studio=main:main"
        ]
    }
)