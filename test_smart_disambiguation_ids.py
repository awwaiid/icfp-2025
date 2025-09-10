#!/usr/bin/env python3
"""
Test the smart disambiguation ID assignment logic
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_unique_room_gets_id_0():
    """Test that unique rooms get disambiguation ID 0"""
    print("=== Test: Unique Room Gets ID 0 ===")
    
    problem = Problem(room_count=4)
    
    # Create a single unique room
    room = Room(label=0)
    room.add_path([])
    room.door_labels = [1, 2, 3, 0, 1, 2]  # Complete room
    
    problem.room_manager.possible_rooms = [room]
    
    print("Before ID assignment:")
    print(f"  Room: {room.get_fingerprint()}")
    
    # Trigger disambiguation ID assignment
    problem.room_manager.assign_initial_disambiguation_ids()
    
    print("After ID assignment:")
    print(f"  Room: {room.get_fingerprint()}")
    
    if hasattr(room, 'disambiguation_id') and room.disambiguation_id == 0:
        print("✅ Unique room correctly assigned ID 0")
    else:
        print(f"❌ Expected ID 0, got {getattr(room, 'disambiguation_id', None)}")

def test_duplicate_discovery_progression():
    """Test the progression when a duplicate is discovered"""
    print("\n=== Test: Duplicate Discovery Progression ===")
    
    problem = Problem(room_count=4)
    
    # Step 1: Create first room (should get ID 0)
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.door_labels = [1, 2, 3, 0, 1, 2]  # 0-123012
    
    problem.room_manager.possible_rooms = [room_a]
    
    print("Step 1: Single room (should get ID 0)")
    problem.room_manager.assign_initial_disambiguation_ids()
    print(f"  Room A: {room_a.get_fingerprint()}")
    
    # Step 2: Add a second room with identical base fingerprint (should stay ?)
    room_b = Room(label=0)
    room_b.add_path([1, 2])
    room_b.door_labels = [1, 2, 3, 0, 1, 2]  # 0-123012 (identical!)
    
    problem.room_manager.possible_rooms.append(room_b)
    
    print(f"\nStep 2: Add potential duplicate (should show ?)")
    print(f"  Room A: {room_a.get_fingerprint()}")
    print(f"  Room B: {room_b.get_fingerprint()}")
    
    # Step 3: Run duplicate detection/disambiguation
    print(f"\nStep 3: Run disambiguation...")
    removed = problem.room_manager.remove_duplicate_rooms(problem.api_client)
    
    print(f"Removed: {removed} rooms")
    print("Final state:")
    for i, room in enumerate(problem.room_manager.possible_rooms):
        disambig_id = getattr(room, 'disambiguation_id', None)
        print(f"  Room {i}: {room.get_fingerprint()} (ID: {disambig_id})")

def test_multiple_unique_rooms():
    """Test multiple unique rooms all get ID 0"""
    print("\n=== Test: Multiple Unique Rooms Get ID 0 ===")
    
    problem = Problem(room_count=4)
    
    # Create several unique rooms
    rooms = []
    
    room1 = Room(label=0)
    room1.add_path([])
    room1.door_labels = [1, 2, 3, 0, 1, 2]  # 0-123012
    rooms.append(room1)
    
    room2 = Room(label=1) 
    room2.add_path([1])
    room2.door_labels = [0, 1, 2, 3, 0, 1]  # 1-012301
    rooms.append(room2)
    
    room3 = Room(label=2)
    room3.add_path([2])
    room3.door_labels = [3, 0, 1, 2, 3, 0]  # 2-301230
    rooms.append(room3)
    
    problem.room_manager.possible_rooms = rooms
    
    print("Before ID assignment:")
    for i, room in enumerate(rooms):
        print(f"  Room {i}: {room.get_fingerprint()}")
    
    # Assign IDs
    problem.room_manager.assign_initial_disambiguation_ids()
    
    print("After ID assignment (all should have ID 0):")
    all_got_zero = True
    for i, room in enumerate(rooms):
        print(f"  Room {i}: {room.get_fingerprint()}")
        if not hasattr(room, 'disambiguation_id') or room.disambiguation_id != 0:
            all_got_zero = False
    
    if all_got_zero:
        print("✅ All unique rooms correctly assigned ID 0")
    else:
        print("❌ Not all unique rooms got ID 0")

def test_real_exploration_progression():
    """Test the ID assignment during real exploration"""
    print("\n=== Test: Real Exploration ID Assignment ===")
    
    problem = Problem(room_count=6)
    
    print("Bootstrap exploration and check ID assignments...")
    try:
        problem.bootstrap("primus")
        
        print("\nAfter bootstrap - checking disambiguation IDs:")
        complete_rooms = problem.room_manager.get_complete_rooms()
        
        for i, room in enumerate(complete_rooms):
            disambig_id = getattr(room, 'disambiguation_id', None)
            print(f"  Room {i}: {room.get_fingerprint()} (ID: {disambig_id})")
        
        # Continue with one more exploration iteration
        print(f"\nContinue exploration to see if more rooms get ID 0...")
        problem.explore_incomplete_rooms()
        
        print("\nAfter exploration iteration:")
        complete_rooms = problem.room_manager.get_complete_rooms()
        
        id_0_count = 0
        id_other_count = 0
        id_none_count = 0
        
        for room in complete_rooms:
            disambig_id = getattr(room, 'disambiguation_id', None)
            if disambig_id == 0:
                id_0_count += 1
            elif disambig_id is None:
                id_none_count += 1
            else:
                id_other_count += 1
        
        print(f"Summary: ID 0: {id_0_count}, ID other: {id_other_count}, ID ?: {id_none_count}")
        
    except Exception as e:
        print(f"Real exploration test failed: {e}")

if __name__ == "__main__":
    print("Testing smart disambiguation ID assignment...\n")
    
    # Test unique room gets ID 0
    test_unique_room_gets_id_0()
    
    # Test duplicate discovery progression
    test_duplicate_discovery_progression()
    
    # Test multiple unique rooms
    test_multiple_unique_rooms()
    
    # Test with real exploration
    test_real_exploration_progression()
    
    print("\nSmart disambiguation ID tests completed!")