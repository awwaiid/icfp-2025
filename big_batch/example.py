"""
Example usage of the slowly approach
"""

from .problem import Problem


def example_bootstrap():
    """Basic bootstrap example"""
    print("=== Slowly Bootstrap Example ===")

    p = Problem(room_count=6)

    # Bootstrap to discover starting room and its connections
    p.bootstrap("primus")

    # Show what we learned
    print("\nAfter bootstrap:")
    p.print_fingerprints()

    return p


def example_incremental_exploration():
    """Incremental exploration example"""
    print("\n=== Incremental Exploration ===")

    p = Problem(room_count=6)
    p.bootstrap("primus")

    # Keep exploring until all rooms are complete
    iteration = 0
    while p.get_incomplete_rooms() and iteration < 10:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        p.explore_incomplete_rooms()
        p.print_fingerprints()

    if not p.get_incomplete_rooms():
        print("\n🎉 All rooms completely mapped!")
        p.print_analysis()  # Show duplicate analysis
    else:
        incomplete = p.get_incomplete_rooms()
        print(
            f"\n📊 {len(incomplete)} rooms still incomplete after {iteration} iterations"
        )

    return p


if __name__ == "__main__":
    p1 = example_bootstrap()
    p1.save_observations("slowly_bootstrap.json")

    p2 = example_incremental_exploration()
    p2.save_observations("slowly_complete.json")
