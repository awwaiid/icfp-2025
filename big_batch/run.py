#!/usr/bin/env python3
"""
Run script for the big-batch approach
Usage: python big-batch/run.py <problem_name> <room_count>
Example: python big-batch/run.py secundus 12
"""

import sys
import os

# Add the parent directory to the path so we can import big_batch.problem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from big_batch.problem import Problem


def main():
    if len(sys.argv) != 3:
        print("Usage: python big-batch/run.py <problem_name> <room_count>")
        print("Example: python big-batch/run.py secundus 12")
        sys.exit(1)
    
    problem_name = sys.argv[1]
    room_count = int(sys.argv[2])
    
    print(f"=== Running BIG-BATCH approach on {problem_name} with {room_count} rooms ===")
    
    # Create problem instance
    p = Problem(room_count=room_count)
    
    # Select the problem
    p.select_problem(problem_name)
    
    # Bootstrap to discover starting room
    p.bootstrap(problem_name)
    
    # Explore until complete using BIG BATCHES
    p.explore_until_complete_batched()
    
    # Generate solution
    p.generate_solution()
    
    print(f"\n🎉 Completed! Solution written to solution.json")
    print(f"To submit: python bin/guess solution.json")


if __name__ == "__main__":
    main()