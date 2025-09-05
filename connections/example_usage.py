"""
Example usage of the connection-based problem solver
"""

from connection_problem import ConnectionProblem


def example_basic_exploration():
    """Basic example: bootstrap and explore a few iterations"""
    print("=== Basic Connection Exploration ===")

    problem = ConnectionProblem(room_count=6)

    # Bootstrap by exploring from starting room
    problem.bootstrap("primus")

    # Explore breadth-first for a few iterations
    problem.explore_breadth_first(max_iterations=3)

    # Show final state
    problem.print_full_state()

    # Save results
    problem.save_observations("basic_connections.json")


def example_systematic_exploration():
    """More systematic exploration until completion"""
    print("\n=== Systematic Connection Exploration ===")

    problem = ConnectionProblem(room_count=6)

    problem.bootstrap("primus")

    # Keep exploring until we've mapped most connections
    problem.explore_breadth_first(max_iterations=20)

    print("\n=== Final Connection Table ===")
    problem.table.print_table()

    print("\n=== Analysis ===")
    problem.analyze_connections()


def example_load_and_analyze():
    """Example of loading saved data and analyzing it"""
    print("\n=== Load and Analyze Example ===")

    try:
        problem = ConnectionProblem(room_count=6)
        problem.load_observations("basic_connections.json")

        print("Loaded previous exploration data:")
        problem.print_full_state()

    except FileNotFoundError:
        print("No saved data found. Run example_basic_exploration() first.")


if __name__ == "__main__":
    example_basic_exploration()
    example_systematic_exploration()
    example_load_and_analyze()
