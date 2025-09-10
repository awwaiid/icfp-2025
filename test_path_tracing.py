#!/usr/bin/env python3
"""
Test script to verify that path tracing prevents infinite partial room creation
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_path_tracing():
    """Test that find_or_create_room_for_path uses path tracing"""
    print("=== Testing Path Tracing Fix ===")
    
    # Create a problem with some complete rooms
    problem = Problem(room_count=6)
    
    # Manually set up some complete rooms that match your scenario
    room_0 = Room(label=0)
    room_0.add_path([])
    room_0.door_labels = [3, 1, 1, 2, 2, 1]  # Complete room 0-311221
    
    room_3 = Room(label=3) 
    room_3.add_path([0])
    room_3.door_labels = [2, 3, 0, 0, 0, 3]  # Complete room 3-230003
    
    room_1 = Room(label=1)
    room_1.add_path([1])
    room_1.door_labels = [0, 1, 0, 1, 0, 1]  # Complete room 1-010101
    
    # Add to room manager
    problem.room_manager.possible_rooms = [room_0, room_3, room_1]
    
    print("Initial setup:")
    for i, room in enumerate(problem.room_manager.possible_rooms):
        print(f"  Room {i}: {room.get_fingerprint()} at paths {room.paths}")
    
    # Test 1: Try to create a room for path [0, 1, 4] with label 0
    # This should trace through room_0 -> room_3 -> ... and find if it leads to an existing complete room
    print(f"\nTest 1: Looking for room at path [0, 1, 4] with label 0")
    
    # Mock the can_trace_path_to_complete_room to simulate finding room_0
    original_trace = problem.room_manager.can_trace_path_to_complete_room
    def mock_trace(path, debug=False):
        if path == [0, 1, 4]:
            return room_0  # Simulate that this path leads to room_0
        return original_trace(path, debug)
    
    problem.room_manager.can_trace_path_to_complete_room = mock_trace
    
    # This should return room_0 and add the path to it, not create a new room
    result_room = problem.room_manager.find_or_create_room_for_path([0, 1, 4], 0)
    
    print(f"Result room: {result_room.get_fingerprint()}")
    print(f"Room paths: {result_room.paths}")
    print(f"Total rooms: {len(problem.room_manager.possible_rooms)}")
    
    if result_room == room_0 and [0, 1, 4] in room_0.paths:
        print("✓ Path tracing worked - found existing room and added path")
    else:
        print("✗ Path tracing failed")
    
    # Test 2: Try with a path that doesn't lead to any complete room
    print(f"\nTest 2: Looking for room at path [99] with label 9 (should create new)")
    
    def mock_trace_none(path, debug=False):
        if path == [99]:
            return None  # This path doesn't lead anywhere
        return mock_trace(path, debug)
    
    problem.room_manager.can_trace_path_to_complete_room = mock_trace_none
    
    initial_count = len(problem.room_manager.possible_rooms)
    result_room = problem.room_manager.find_or_create_room_for_path([99], 9)
    final_count = len(problem.room_manager.possible_rooms)
    
    if final_count == initial_count + 1 and result_room.label == 9:
        print("✓ New room creation worked when path tracing failed")
    else:
        print("✗ New room creation failed")
    
    # Restore original function
    problem.room_manager.can_trace_path_to_complete_room = original_trace
    
    print("\nPath tracing test completed!")

if __name__ == "__main__":
    test_path_tracing()