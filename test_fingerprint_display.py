#!/usr/bin/env python3
"""
Test the updated fingerprint display with disambiguation IDs
"""

import sys
sys.path.append('.')

from ambiguously.room import Room
from ambiguously.problem import Problem

def test_fingerprint_display():
    """Test fingerprint display formats"""
    print("=== Testing Fingerprint Display Formats ===")
    
    # Test various room states
    print("Test 1: Room without disambiguation ID")
    room1 = Room(label=0)
    room1.door_labels = [3, 0, 1, 0, 2, 3]
    print(f"  Expected: 0-301023-?")
    print(f"  Actual:   {room1.get_fingerprint()}")
    
    print("\nTest 2: Room with disambiguation ID = 0")
    room2 = Room(label=0)
    room2.door_labels = [3, 0, 1, 0, 2, 3]
    room2.disambiguation_id = 0
    print(f"  Expected: 0-301023-0")
    print(f"  Actual:   {room2.get_fingerprint()}")
    
    print("\nTest 3: Room with disambiguation ID = 1")
    room3 = Room(label=0)
    room3.door_labels = [3, 0, 1, 0, 2, 3]
    room3.disambiguation_id = 1
    print(f"  Expected: 0-301023-1")
    print(f"  Actual:   {room3.get_fingerprint()}")
    
    print("\nTest 4: Partial room")
    room4 = Room(label=2)
    room4.door_labels = [1, None, None, 3, None, 0]
    print(f"  Expected: 2-1??3?0-?")
    print(f"  Actual:   {room4.get_fingerprint()}")
    
    print("\nTest 5: Room with unknown label")
    room5 = Room(label=None)
    room5.door_labels = [1, 2, 3, 0, 1, 2]
    print(f"  Expected: ?-123012-?")
    print(f"  Actual:   {room5.get_fingerprint()}")

def test_problem_fingerprint_display():
    """Test fingerprint display in Problem context"""
    print("\n=== Testing Problem Fingerprint Display ===")
    
    problem = Problem(room_count=4)
    
    # Create some test rooms
    room1 = Room(label=0)
    room1.add_path([])
    room1.door_labels = [1, 2, 3, 0, 1, 2]
    
    room2 = Room(label=0) 
    room2.add_path([1, 2])
    room2.door_labels = [1, 2, 3, 0, 1, 2]
    room2.disambiguation_id = 0  # Manually set for testing
    
    room3 = Room(label=1)
    room3.add_path([1])
    room3.door_labels = [0, 1, None, None, 2, 3]
    
    problem.room_manager.possible_rooms = [room1, room2, room3]
    
    print("Expected fingerprint formats:")
    print("  0-123012-? (no disambiguation ID)")
    print("  0-123012-0 (disambiguation ID = 0)")
    print("  1-01??23-? (partial, no disambiguation ID)")
    
    print("\nActual output:")
    problem.print_fingerprints()

if __name__ == "__main__":
    print("Testing fingerprint display with disambiguation IDs...\n")
    
    # Test individual room fingerprints
    test_fingerprint_display()
    
    # Test in problem context
    test_problem_fingerprint_display()
    
    print("\nFingerprint display tests completed!")