#!/usr/bin/env python3

from IPython import start_ipython
import sys

# IPython startup script for ambiguously system
startup_script = """
%load_ext autoreload
%autoreload 2

# Import the ambiguously system
from ambiguously.problem import Problem
from ambiguously.room import Room

print("Ambiguously Problem Solver Loaded!")
print("Minimal fingerprint-based room exploration")
print()
print("Quick start:")
print("  p = Problem(room_count=6)")
print("  p.bootstrap('primus')  # Discover starting room")
print("  p.print_fingerprints()  # Show room fingerprints")
print("  p.explore_incomplete_rooms()  # Fill in missing doors")
print()
print("Fingerprint format: 'label-door0door1door2door3door4door5'")
print("Example: '1-210012' means room label=1, door0→label2, door1→label1, etc.")
print("Unknown values shown as '?': '1-21??12'")
"""

if __name__ == "__main__":
    # Start IPython with the startup script
    start_ipython(argv=[], user_ns={}, exec_lines=startup_script.strip().split("\n"))
