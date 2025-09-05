#!/usr/bin/env python3

from IPython import start_ipython
import sys

# IPython startup script
startup_script = """
%load_ext autoreload
%autoreload 2
from problem import Problem
from room import Room
print("Auto-reload enabled. Problem and Room classes imported.")
print("Usage: p = Problem(room_count=6)")
"""

if __name__ == "__main__":
    # Start IPython with the startup script
    start_ipython(argv=[], user_ns={}, exec_lines=startup_script.strip().split("\n"))
