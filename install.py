#!/usr/bin/env python3
"""Install skill-finder into ~/.claude/skills and build its catalog from this machine's skills.

Usage:  python install.py
Re-run any time to update the installed copy.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "skill-finder")
DEST = os.path.join(os.path.expanduser("~"), ".claude", "skills", "skill-finder")

os.makedirs(DEST, exist_ok=True)
shutil.copy2(os.path.join(SRC, "SKILL.md"), DEST)
shutil.copytree(os.path.join(SRC, "scripts"), os.path.join(DEST, "scripts"), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__"))
print(f"Installed to {DEST}")
subprocess.run([sys.executable, os.path.join(DEST, "scripts", "build_catalog.py")], check=True)
print("Done. In Claude Code type:  /skill-finder <your goal>")
