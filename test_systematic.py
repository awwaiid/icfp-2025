#!/usr/bin/env python3
"""
Test the systematic room disambiguation process specifically
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ambiguously.problem import Problem

def test_simple_2():
    """Test systematic process on simple-2 with controlled exploration"""
    print("=== Testing Systematic Process on Simple-2 ===")
    
    # Create problem
    problem = Problem(room_count=2)
    
    # Select problem first
    problem.select_problem("simple-2")
    
    # Bootstrap
    problem.bootstrap("simple-2")
    
    print("\nAfter bootstrap:")
    problem.print_fingerprints()
    
    # Manually create the basic rooms based on what we know simple-2 should have
    # Room 0: label=0, all doors lead to label 0 (the other room)
    # Room 1: label=0, all doors lead back to label 0 (room 0)
    
    # Start room (already exists)
    start_room = problem.room_manager.possible_rooms[0]
    
    # Create the second room manually with path [0] 
    second_room = problem.room_manager.find_or_create_room_for_path([0], 0, problem.api_client)
    
    print(f"\nAfter creating second room:")
    print(f"Room 0: {start_room}")
    print(f"Room 1: {second_room}")
    
    # Now try to make the first room complete by setting all its doors to point to the second room
    for door in range(6):
        start_room.set_door_label(door, 0)  # All doors lead to label 0
    
    print(f"\nAfter setting all doors of room 0:")
    print(f"Room 0 complete: {start_room.is_complete()}")
    print(f"Room 0: {start_room.get_fingerprint()}")
    problem.print_fingerprints()
    
    # The second room should have path [0] - let's check if we can complete it too
    print(f"\nSecond room paths: {second_room.paths}")
    print(f"Second room complete: {second_room.is_complete()}")
    print(f"Second room door labels: {second_room.door_labels}")
    
    # Now apply systematic disambiguation - this should complete the second room
    print("\n=== Applying Systematic Disambiguation ===")
    processed = problem.room_manager.systematic_room_disambiguation(problem.api_client)
    print(f"Processed {processed} rooms")
    
    # If it completed the second room, let's see what it looks like
    print(f"\nAfter systematic process:")
    print(f"Second room complete: {second_room.is_complete()}")
    if second_room.is_complete():
        print(f"Second room fingerprint: {second_room.get_fingerprint()}")
    
    print("\nFinal result:")
    problem.print_fingerprints()

if __name__ == "__main__":
    test_simple_2()