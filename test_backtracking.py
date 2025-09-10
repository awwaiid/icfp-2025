#!/usr/bin/env python3
"""
Simple test script for the backtracking/reverse door discovery system
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.api_client import ApiClient

def test_api_client_label_editing():
    """Test that ApiClient handles label editing syntax correctly"""
    print("=== Testing ApiClient label editing ===")
    
    client = ApiClient()
    
    # Test counting label edits
    assert client.count_label_edits_in_plan("012") == 0
    assert client.count_label_edits_in_plan("0[1]2") == 1
    assert client.count_label_edits_in_plan("0[1]2[3]") == 2
    print("✓ Label edit counting works")
    
    # Test parsing responses with echoes
    actual, echoes = client.parse_response_with_echoes("012", "345")
    assert actual == [3, 4, 5] and echoes == []
    print("✓ No-edit parsing works")
    
    actual, echoes = client.parse_response_with_echoes("0[1]2", "31145")
    assert echoes == [1]  # Should find the echo
    print(f"✓ Single-edit parsing works: actual={actual}, echoes={echoes}")
    
    print("ApiClient tests passed!\n")

def test_mock_exploration():
    """Test with mock data to verify the backtracking logic"""
    print("=== Testing backtracking logic ===")
    
    # Create a Problem instance
    problem = Problem(room_count=6)
    
    # Manually create some rooms and connections to test return door discovery
    from ambiguously.room import Room
    
    # Create two test rooms
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.set_door_label(1, 2)  # Door 1 leads to room with label 2
    
    room_b = Room(label=2) 
    room_b.add_path([1])
    
    # Add to room manager
    problem.room_manager.possible_rooms = [room_a, room_b]
    
    print(f"Room A: {room_a.get_fingerprint()} at paths {room_a.paths}")
    print(f"Room B: {room_b.get_fingerprint()} at paths {room_b.paths}")
    
    # Mock the API call for discover_return_door
    original_explore = problem.api_client.explore
    
    def mock_explore(plans):
        """Mock exploration that simulates finding the return door"""
        print(f"Mock explore called with plans: {plans}")
        
        # Simulate responses where door 3 leads back to the modified room
        mock_results = []
        for i, plan in enumerate(plans):
            if i == 3:  # Door 3 is the return door
                mock_results.append("121211")  # Echo of temp label 1, then path shows temp label 1 at destination
            else:
                mock_results.append("121210")  # Other doors lead to original label 0 rooms
        
        return {
            "plans": plans,
            "plan_strings": plans,
            "results": mock_results,
        }
    
    problem.api_client.explore = mock_explore
    
    # Test discover_return_door
    print("\nTesting discover_return_door...")
    try:
        problem.discover_return_door(room_a, room_b, 1)
        print(f"After discovery: Room B door labels = {room_b.door_labels}")
        
        # Check if door 3 was identified as the return door
        if room_b.door_labels[3] == 0:  # Should point back to room A (label 0)
            print("✓ Return door discovery successful!")
        else:
            print("✗ Return door discovery failed")
            
    except Exception as e:
        print(f"✗ Return door discovery error: {e}")
    
    # Restore original explore
    problem.api_client.explore = original_explore
    
    print("Backtracking test completed!\n")

if __name__ == "__main__":
    print("Testing backtracking system...\n")
    
    test_api_client_label_editing()
    test_mock_exploration()
    
    print("All tests completed!")