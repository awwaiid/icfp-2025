#!/usr/bin/env python3
"""
Test the label editing functionality with real API calls
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem

def test_label_editing_api():
    """Test basic label editing with real API"""
    print("=== Testing Label Editing API ===")
    
    # Create problem 
    problem = Problem(room_count=6)
    
    print("Testing basic label editing syntax...")
    
    # Test 1: Simple label edit with echo
    print("\nTest 1: Simple label edit")
    plans = ["[2]"]  # Just edit current room to label 2
    
    try:
        result = problem.api_client.explore(plans)
        if result and "results" in result:
            response = result["results"][0]  
            plan_string = result["plan_strings"][0]
            
            print(f"Sent: '{plan_string}'")
            print(f"Received: '{response}'")
            
            # Parse the response
            actual_labels, echo_labels = problem.api_client.parse_response_with_echoes(plan_string, response)
            print(f"Parsed - Actual: {actual_labels}, Echoes: {echo_labels}")
            
            if echo_labels == [2]:
                print("✓ Label editing echo received correctly")
            else:
                print(f"✗ Expected echo [2], got {echo_labels}")
        else:
            print("✗ No results received")
            
    except Exception as e:
        print(f"✗ API call failed: {e}")
    
    # Test 2: Label edit with movement  
    print("\nTest 2: Label edit with movement")
    plans = ["0[1]2"]  # Go door 0, edit to label 1, go door 2
    
    try:
        result = problem.api_client.explore(plans)
        if result and "results" in result:
            response = result["results"][0]
            plan_string = result["plan_strings"][0] 
            
            print(f"Sent: '{plan_string}'")
            print(f"Received: '{response}'")
            
            # Parse the response
            actual_labels, echo_labels = problem.api_client.parse_response_with_echoes(plan_string, response)
            print(f"Parsed - Actual: {actual_labels}, Echoes: {echo_labels}")
            
            if 1 in echo_labels:
                print("✓ Label editing with movement works")
            else:
                print(f"✗ Expected echo containing 1, got {echo_labels}")
        else:
            print("✗ No results received")
            
    except Exception as e:
        print(f"✗ API call failed: {e}")

def test_return_door_discovery():
    """Test the return door discovery with real API"""
    print("\n=== Testing Return Door Discovery ===")
    
    # Create problem and bootstrap to get some rooms
    problem = Problem(room_count=6)
    
    print("Bootstrapping to get initial rooms...")
    try:
        problem.bootstrap("primus")  # or whatever your problem name is
        
        complete_rooms = problem.room_manager.get_complete_rooms()
        if len(complete_rooms) >= 2:
            room_a = complete_rooms[0]
            
            # Find a connection from room_a to another room
            for door, label in enumerate(room_a.door_labels):
                if label is not None:
                    # Find the destination room
                    for room_b in complete_rooms:
                        if room_b.label == label and room_b != room_a:
                            print(f"\nTesting return door discovery:")
                            print(f"From: {room_a.get_fingerprint()} (paths: {room_a.paths})")  
                            print(f"To: {room_b.get_fingerprint()} (paths: {room_b.paths})")
                            print(f"Forward door: {door}")
                            
                            # Test discover_return_door
                            try:
                                problem.discover_return_door(room_a, room_b, door)
                                
                                # Check if return door was found
                                return_door_found = False
                                for return_door, return_label in enumerate(room_b.door_labels):
                                    if return_label == room_a.label:
                                        print(f"✓ Return door discovered: door {return_door} in room {room_b.label} leads back to room {room_a.label}")
                                        return_door_found = True
                                        break
                                
                                if not return_door_found:
                                    print("✗ Return door not found after discovery attempt")
                                    
                            except Exception as e:
                                print(f"✗ Return door discovery failed: {e}")
                            
                            return  # Test with first valid connection found
            
            print("No suitable room pair found for return door test")
        else:
            print("Need at least 2 complete rooms for return door test")
            
    except Exception as e:
        print(f"Bootstrap failed: {e}")

if __name__ == "__main__":
    print("Testing label editing and backtracking functionality...\n")
    
    # Test basic API integration
    test_label_editing_api()
    
    # Test return door discovery  
    test_return_door_discovery()
    
    print("\nLabel editing tests completed!")