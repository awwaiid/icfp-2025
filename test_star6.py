#!/usr/bin/env python3
"""
Test the systematic room disambiguation process on star-6
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ambiguously.problem import Problem

def test_star_6():
    """Test systematic process on star-6 with controlled exploration"""
    print("=== Testing Systematic Process on Star-6 ===")
    
    # Create problem
    problem = Problem(room_count=6)
    
    # Select problem first
    problem.select_problem("star")
    
    # Bootstrap  
    problem.bootstrap("star")
    
    print("\nAfter bootstrap:")
    problem.print_fingerprints()
    
    # For star-6, the center room (room 0) should have all doors leading to different rooms
    # Each peripheral room should have only one door leading back to center
    
    # Create rooms for each peripheral connection
    rooms = [problem.room_manager.possible_rooms[0]]  # Start with center room
    
    # Create peripheral rooms via paths [0], [1], [2], [3], [4], [5]
    for door in range(6):
        peripheral_room = problem.room_manager.find_or_create_room_for_path([door], 0, problem.api_client)
        rooms.append(peripheral_room)
    
    print(f"\nCreated {len(rooms)} rooms:")
    for i, room in enumerate(rooms):
        print(f"Room {i}: paths={room.paths}, label={room.label}")
    
    # Complete the center room - all doors lead to different peripheral rooms (all label 0)
    center_room = rooms[0]
    for door in range(6):
        center_room.set_door_label(door, 0)  # All peripheral rooms have label 0
    
    print(f"\nCompleted center room: {center_room.get_fingerprint()}")
    
    # Now apply systematic disambiguation to complete the peripheral rooms
    print("\n=== Applying Systematic Disambiguation ===")
    processed = problem.room_manager.systematic_room_disambiguation(problem.api_client)
    print(f"Processed {processed} rooms")
    
    print("\nFinal result:")
    problem.print_fingerprints()

if __name__ == "__main__":
    test_star_6()