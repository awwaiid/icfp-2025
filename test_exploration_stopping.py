#!/usr/bin/env python3
"""
Test that exploration stops when we have complete coverage
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_exploration_stopping():
    """Test that exploration stops when we have complete unique room coverage"""
    print("=== Testing Exploration Stopping ===")
    
    # Create a problem with 6 rooms
    problem = Problem(room_count=6)
    
    # Create 6 unique complete rooms with different fingerprints
    rooms = [
        Room(0), Room(3), Room(1), Room(0), Room(1), Room(2)
    ]
    
    # Set up complete fingerprints (different for each)
    rooms[0].door_labels = [3, 1, 0, 1, 0, 1]  # 0-310101
    rooms[1].door_labels = [0, 3, 3, 3, 3, 3]  # 3-033333
    rooms[2].door_labels = [0, 2, 1, 1, 1, 0]  # 1-021110
    rooms[3].door_labels = [1, 1, 0, 0, 2, 2]  # 0-110022 (different from room 0)
    rooms[4].door_labels = [2, 0, 0, 1, 1, 0]  # 1-200110
    rooms[5].door_labels = [1, 0, 1, 2, 2, 0]  # 2-101220
    
    # Add paths to make them reachable
    for i, room in enumerate(rooms):
        room.add_path([i])  # Simple paths
    
    problem.room_manager.possible_rooms = rooms
    
    print("Setup complete rooms:")
    for i, room in enumerate(rooms):
        print(f"  Room {i}: {room.get_fingerprint()}")
    
    # Mock the get_absolute_connections to return verified connections
    original_get_connections = problem.room_manager.get_absolute_connections
    def mock_get_connections(room):
        return [0, 1, 2, 3, 4, 5]  # All connections verified
    problem.room_manager.get_absolute_connections = mock_get_connections
    
    # Test that partial explorations should return empty
    partial_explorations = problem.exploration_strategy.get_partial_rooms_to_explore()
    
    print(f"Partial explorations suggested: {len(partial_explorations)}")
    
    if len(partial_explorations) == 0:
        print("✓ Exploration correctly stops when complete coverage achieved")
    else:
        print("✗ Exploration continues despite complete coverage")
        
    # Test the overall exploration batch
    exploration_batch = problem.exploration_strategy.get_next_exploration_batch()
    
    if exploration_batch is None:
        print("✓ No exploration batch suggested - exploration complete")
    else:
        print(f"✗ Exploration batch still suggested: {exploration_batch}")
    
    # Restore original function
    problem.room_manager.get_absolute_connections = original_get_connections
    
    print("Exploration stopping test complete!")

if __name__ == "__main__":
    test_exploration_stopping()