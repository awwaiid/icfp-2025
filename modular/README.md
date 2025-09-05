# Modular Room Exploration System

This directory contains the modular room exploration system broken down into separate components for parallel development.

## Structure

- **`core/`**: Core data structures (Room, ProblemData)
- **`analysis/`**: Room identity analysis and merging logic
- **`strategies/`**: Different exploration strategies
- **`visualization/`**: Graphviz and text rendering
- **`modular_problem.py`**: Main coordinator class
- **`example_usage.py`**: Usage examples
- **`start_modular_repl.py`**: IPython REPL with everything loaded

## Quick Start

```bash
# Start the REPL
uv run python modular/start_modular_repl.py

# Or run examples
uv run python -m modular.example_usage
```

```python
# In REPL or code
from modular.modular_problem import ModularProblem
from modular.strategies.random_strategy import RandomWalkStrategy

p = ModularProblem(room_count=6)
p.set_strategy(RandomWalkStrategy, max_path_length=4)
p.select_problem("primus")
p.explore_with_strategy()
p.generate_graphviz("output")
```

## Available Strategies

- **SystematicStrategy**: Explores all paths up to increasing depths
- **RandomWalkStrategy**: Pure random exploration
- **BiasedRandomStrategy**: Random biased toward unexplored areas
- **TreeExplorationStrategy**: Expands from known room doors
- **AdaptiveStrategy**: Switches between different strategies

## Extending

To add a new exploration strategy:

1. Inherit from `strategies.base_strategy.ExplorationStrategy`
2. Implement `generate_next_paths()` and `should_continue_exploring()`
3. Use with `problem.set_strategy(YourStrategy, **kwargs)`

## Components

Each component is independent and can be worked on separately:

- **Data layer**: Pure room/problem data with no logic
- **Analysis layer**: Room identity detection and merging
- **Strategy layer**: Different exploration algorithms
- **Visualization layer**: Multiple rendering options