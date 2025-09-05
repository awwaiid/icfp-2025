#!/usr/bin/env python3

from IPython import start_ipython
import sys

# IPython startup script for connection system
startup_script = """
%load_ext autoreload
%autoreload 2

# Import the connection system
from connections.connection_problem import ConnectionProblem
from connections.connection_data import ConnectionTable, Connection

print("Connection-based Problem Solver Loaded!")
print("Quick start:")
print("  p = ConnectionProblem(room_count=6)")
print("  p.bootstrap('primus')")
print("  p.explore_breadth_first(max_iterations=5)")
print("  p.print_full_state()")
print()
print("Key methods:")
print("  - bootstrap(problem_name): Start exploration from room 0")
print("  - explore_breadth_first(): Systematically explore all rooms")
print("  - print_full_state(): Show complete connection table")
print("  - analyze_connections(): Find mergeable connections")
print("  - save_observations(file): Save exploration data")
print("  - load_observations(file): Load exploration data")
"""

if __name__ == "__main__":
    # Start IPython with the startup script
    start_ipython(argv=[], user_ns={}, exec_lines=startup_script.strip().split("\n"))
