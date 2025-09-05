"""
Example usage of the modular problem solver with different strategies
"""

from .modular_problem import ModularProblem
from .strategies.systematic_strategy import SystematicStrategy, TreeExplorationStrategy
from .strategies.random_strategy import (
    RandomWalkStrategy,
    BiasedRandomStrategy,
    AdaptiveStrategy,
)


def example_systematic():
    """Example using systematic exploration"""
    print("=== Systematic Exploration Example ===")

    problem = ModularProblem(room_count=6)
    problem.set_strategy(SystematicStrategy, max_depth=2)

    # Select a problem
    problem.select_problem("primus")

    # Explore systematically
    problem.explore_with_strategy(max_iterations=5, max_paths_per_iteration=20)

    # Show results
    problem.print_summary()
    problem.generate_graphviz("systematic_output")


def example_random_walk():
    """Example using random walk exploration"""
    print("\n=== Random Walk Exploration Example ===")

    problem = ModularProblem(room_count=6)
    problem.set_strategy(RandomWalkStrategy, max_path_length=4)

    problem.select_problem("primus")
    problem.explore_with_strategy(max_iterations=8, max_paths_per_iteration=5)

    problem.print_summary()
    problem.generate_graphviz("random_output")


def example_adaptive():
    """Example using adaptive exploration"""
    print("\n=== Adaptive Exploration Example ===")

    problem = ModularProblem(room_count=6)
    problem.set_strategy(AdaptiveStrategy)

    problem.select_problem("primus")
    problem.explore_with_strategy(max_iterations=10, max_paths_per_iteration=8)

    problem.print_identity_analysis()
    problem.generate_graphviz("adaptive_output", show_possibilities=True)


def compare_strategies():
    """Compare different strategies on the same problem"""
    print("\n=== Strategy Comparison ===")

    strategies = [
        ("Systematic", SystematicStrategy, {"max_depth": 2}),
        ("Random Walk", RandomWalkStrategy, {"max_path_length": 3}),
        ("Biased Random", BiasedRandomStrategy, {"bias_strength": 0.8}),
        ("Tree Exploration", TreeExplorationStrategy, {}),
    ]

    for name, strategy_class, kwargs in strategies:
        print(f"\n--- Testing {name} ---")
        problem = ModularProblem(room_count=6)
        problem.set_strategy(strategy_class, **kwargs)

        problem.select_problem("primus")
        problem.explore_with_strategy(max_iterations=3, max_paths_per_iteration=10)

        stats = problem.current_strategy.get_exploration_stats()
        print(
            f"Results: {stats['confirmed_doors']} doors confirmed, "
            f"{stats['unique_rooms']} unique rooms, "
            f"{stats['ambiguous_rooms']} ambiguous rooms"
        )


if __name__ == "__main__":
    # Run examples
    example_systematic()
    example_random_walk()
    example_adaptive()
    compare_strategies()
