#!/usr/bin/env python3
"""
Test room disambiguation with identical fingerprints
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_disambiguation_logic():
    """Test the disambiguation logic with mock ambiguous rooms"""
    print("=== Testing Room Disambiguation Logic ===")
    
    # Create problem
    problem = Problem(room_count=6)
    
    # Create two rooms with identical base fingerprints
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.door_labels = [1, 2, 3, 0, 1, 2]  # 0-123012
    
    room_b = Room(label=0) 
    room_b.add_path([1, 2])
    room_b.door_labels = [1, 2, 3, 0, 1, 2]  # 0-123012 (identical!)
    
    # Add different complete room
    room_c = Room(label=1)
    room_c.add_path([1])
    room_c.door_labels = [0, 0, 2, 3, 1, 0]  # 1-002310
    
    # Add to room manager
    problem.room_manager.possible_rooms = [room_a, room_b, room_c]
    
    print("Setup - rooms with identical base fingerprints:")
    for i, room in enumerate([room_a, room_b, room_c]):
        base_fp = room.get_fingerprint(include_disambiguation=False) 
        full_fp = room.get_fingerprint(include_disambiguation=True)
        print(f"  Room {i}: base='{base_fp}', full='{full_fp}', paths={room.paths}")
    
    # Test disambiguation detection
    print(f"\nTesting disambiguation detection...")
    disambiguated = problem.detect_and_resolve_ambiguous_rooms()
    
    if disambiguated > 0:
        print("✓ Ambiguous rooms detected and disambiguated")
        
        print("\nAfter disambiguation:")
        for i, room in enumerate([room_a, room_b, room_c]):
            full_fp = room.get_fingerprint(include_disambiguation=True)
            disambig_id = getattr(room, 'disambiguation_id', None)
            print(f"  Room {i}: '{full_fp}' (disambig_id={disambig_id})")
            
    else:
        print("✗ No ambiguous rooms detected")
    
    # Test return door patterns
    print(f"\nTesting return door pattern analysis...")
    return_doors_a = problem.room_manager.find_return_doors_to_room(room_a)
    return_doors_b = problem.room_manager.find_return_doors_to_room(room_b) 
    
    print(f"Return doors to Room A: {return_doors_a}")
    print(f"Return doors to Room B: {return_doors_b}")
    
    if return_doors_a != return_doors_b:
        print("✓ Rooms can be distinguished by return door patterns")
    else:
        print("⚠ Rooms have identical return door patterns")

def test_disambiguation_with_backtracking():
    """Test disambiguation that requires backtracking"""
    print("\n=== Testing Disambiguation with Backtracking ===")
    
    problem = Problem(room_count=6)
    
    # Create scenario where we need backtracking to distinguish rooms
    # Two rooms with same fingerprint but different return door patterns
    
    room_0a = Room(label=0)
    room_0a.add_path([])
    room_0a.door_labels = [1, 2, 0, 1, 0, 2]  # 0-120102
    
    room_0b = Room(label=0)
    room_0b.add_path([3, 4])
    room_0b.door_labels = [1, 2, 0, 1, 0, 2]  # 0-120102 (identical base)
    
    # Create rooms that point back differently to distinguish them
    room_1 = Room(label=1)
    room_1.add_path([1])
    room_1.door_labels = [0, 1, 1, 1, 1, 1]  # Points back to room_0a via door 0
    
    room_2a = Room(label=2)
    room_2a.add_path([2])
    room_2a.door_labels = [0, 2, 2, 2, 2, 2]  # Points back to room_0a via door 0
    
    room_2b = Room(label=2) 
    room_2b.add_path([3, 4, 5])
    room_2b.door_labels = [2, 2, 2, 0, 2, 2]  # Points back to room_0b via door 3
    
    problem.room_manager.possible_rooms = [room_0a, room_0b, room_1, room_2a, room_2b]
    
    print("Setup - complex scenario:")
    for i, room in enumerate(problem.room_manager.possible_rooms):
        print(f"  Room {i}: {room.get_fingerprint(include_disambiguation=False)} at {room.paths}")
    
    # Test disambiguation
    print(f"\nDetecting ambiguous rooms...")
    problem.detect_and_resolve_ambiguous_rooms()
    
    # Test verification with backtracking
    print(f"\nTesting backtracking verification...")
    are_different = problem.room_manager.verify_room_disambiguation_with_backtracking(room_0a, room_0b)
    print(f"Room 0a and 0b are different: {are_different}")
    
    if are_different:
        print("✓ Backtracking successfully distinguished identical fingerprints")
    else:
        print("⚠ Backtracking could not distinguish the rooms")

if __name__ == "__main__":
    print("Testing room disambiguation functionality...\n")
    
    # Test basic disambiguation
    test_disambiguation_logic()
    
    # Test disambiguation with backtracking
    test_disambiguation_with_backtracking()
    
    print("\nDisambiguation tests completed!")