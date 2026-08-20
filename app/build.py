import os
import subprocess
import sys
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)
sep = ";" if sys.platform.startswith("win") else ":"

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconsole",
    "--onefile",
    f"--add-data={ctk_path}{sep}customtkinter",
    f"--add-data=app{sep}app",
    f"--add-data=templates.json{sep}.",
    "--name=PhotoTemplateStudioPro",
    "main.py",
]

print("Building executable...")
subprocess.run(cmd, check=True)
print("Build complete! Check the dist/ directory.")