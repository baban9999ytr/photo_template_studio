import subprocess
import sys
from setuptools import setup,find_packages

subprocess.check_call([sys.executable, "app/install.py"])

setup(
    name="photo_template_studio",
    version="1.0.0",
    packages=find_packages(include=["app", "app.*"]),
)