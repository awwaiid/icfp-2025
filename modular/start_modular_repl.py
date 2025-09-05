#!/usr/bin/env python3

from IPython import start_ipython
import sys

# IPython startup script for modular system
startup_script = """
%load_ext autoreload
%autoreload 2

# Import all the modular components
from modular.modular_problem import ModularProblem
from modular.strategies.systematic_strategy import SystematicStrategy, TreeExplorationStrategy
from modular.strategies.random_strategy import RandomWalkStrategy, BiasedRandomStrategy, AdaptiveStrategy
from modular.core.room_data import ProblemData, Room
from modular.analysis.room_identity import RoomIdentityAnalyzer
from modular.visualization.graphviz_renderer import GraphvizRenderer, TextRenderer

print("Modular Problem Solver Loaded!")
print("Quick start:")
print("  p = ModularProblem(room_count=6)")
print("  p.set_strategy(SystematicStrategy, max_depth=2)")
print("  p.select_problem('primus')")
print("  p.explore_with_strategy()")
print()
print("Available strategies:")
print("  - SystematicStrategy: explores all paths up to depth")
print("  - RandomWalkStrategy: random exploration")
print("  - BiasedRandomStrategy: random biased toward unexplored")
print("  - AdaptiveStrategy: switches between strategies")
print("  - TreeExplorationStrategy: expands from known rooms")
"""

if __name__ == "__main__":
    # Start IPython with the startup script
    start_ipython(argv=[], user_ns={}, exec_lines=startup_script.strip().split("\n"))
