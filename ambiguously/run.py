#!/usr/bin/env python3
"""
Run script for the ambiguously approach
Usage: python ambiguously/run.py <problem_name> <room_count>
Example: python ambiguously/run.py secundus 12
"""

import sys
import os

# Add the parent directory to the path so we can import ambiguously.problem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ambiguously.problem import Problem


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python ambiguously/run.py <problem_name> <room_count> [--no-select]")
        print("Example: python ambiguously/run.py secundus 12")
        print("  --no-select: Skip the select_problem API call to preserve current problem state")
        sys.exit(1)

    problem_name = sys.argv[1]
    room_count = int(sys.argv[2])
    skip_select = len(sys.argv) == 4 and sys.argv[3] == '--no-select'

    print(f"=== Running ambiguously approach on {problem_name} with {room_count} rooms ===")

    # Create problem instance
    p = Problem(room_count=room_count)

    # Select the problem (unless --no-select flag is used)
    if skip_select:
        print("Skipping select_problem API call (--no-select flag)")
    else:
        p.select_problem(problem_name)

    # Bootstrap to discover starting room
    p.bootstrap(problem_name)

    # Explore until complete
    p.explore_until_complete()

    # Generate solution
    p.generate_solution()

    print(f"\n🎉 Completed! Solution written to solution.json")
    print(f"To submit: python bin/guess solution.json")


if __name__ == "__main__":
    main()
