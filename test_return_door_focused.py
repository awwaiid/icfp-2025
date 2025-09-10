#!/usr/bin/env python3
"""
Focused test of return door discovery with real API
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_return_door_with_real_api():
    """Test return door discovery with a controlled scenario"""
    print("=== Testing Return Door Discovery with Real API ===")
    
    # Create problem
    problem = Problem(room_count=6)
    
    # Create two rooms manually to test return door discovery
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.door_labels = [3, None, None, None, None, None]  # Door 0 leads to label 3
    
    room_b = Room(label=3)
    room_b.add_path([0])  # Reached via door 0 from room_a
    room_b.door_labels = [None, None, None, None, None, None]  # All doors unknown
    
    # Add to room manager
    problem.room_manager.possible_rooms = [room_a, room_b]
    
    print("Setup:")
    print(f"  Room A: {room_a.get_fingerprint()} at paths {room_a.paths}")
    print(f"  Room B: {room_b.get_fingerprint()} at paths {room_b.paths}")
    print(f"  Forward connection: Room A door 0 → Room B (label 3)")
    
    print(f"\nTesting return door discovery...")
    
    try:
        # This should use the API to discover which door in room_b leads back to room_a
        problem.discover_return_door(room_a, room_b, 0)
        
        print(f"\nAfter discovery:")
        print(f"  Room A door labels: {room_a.door_labels}")
        print(f"  Room B door labels: {room_b.door_labels}")
        
        # Check if any door in room_b now points back to room_a (label 0)
        return_doors = []
        for door, label in enumerate(room_b.door_labels):
            if label == 0:  # Points back to room_a
                return_doors.append(door)
        
        if return_doors:
            print(f"✓ Return door(s) discovered: {return_doors}")
            for door in return_doors:
                print(f"  Room B door {door} → Room A (label 0)")
        else:
            print("✗ No return door discovered")
            
    except Exception as e:
        print(f"✗ Return door discovery failed: {e}")
        import traceback
        traceback.print_exc()

def test_manual_label_editing():
    """Test manual label editing to understand the flow"""
    print("\n=== Testing Manual Label Editing Flow ===")
    
    problem = Problem(room_count=6)
    
    # Test the exact flow that discover_return_door would use
    print("Step 1: Navigate to starting position and edit label")
    
    # This simulates: go to room at path [], edit its label to 2, then go through door 0
    plans = ["[2]0"]
    
    try:
        result = problem.api_client.explore(plans)
        if result and "results" in result:
            response = result["results"][0]
            plan_string = result["plan_strings"][0]
            
            print(f"Sent: '{plan_string}'")
            print(f"Received: '{response}'")
            
            # Parse response
            actual_labels, echo_labels = problem.api_client.parse_response_with_echoes(plan_string, response)
            print(f"Parsed - Actual: {actual_labels}, Echoes: {echo_labels}")
            
            print("Step 2: From the destination, check different doors")
            
            # Now from the destination room, try each door to see which shows modified label
            for door in range(6):
                door_check_plan = f"[2]0{door}"  # Edit label, go door 0, then try door
                
                result2 = problem.api_client.explore([door_check_plan])
                if result2 and "results" in result2:
                    response2 = result2["results"][0]
                    actual2, echoes2 = problem.api_client.parse_response_with_echoes(door_check_plan, response2)
                    
                    print(f"  Door {door}: plan='{door_check_plan}' → actual={actual2}, echoes={echoes2}")
                    
                    # If the last actual label is our modified label (2), this door leads back
                    if actual2 and actual2[-1] == 2:
                        print(f"    ✓ Door {door} leads back to modified room!")
                        break
                else:
                    print(f"  Door {door}: failed")
                    
    except Exception as e:
        print(f"Manual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing return door discovery with real API calls...\n")
    
    # Test the return door discovery method
    test_return_door_with_real_api()
    
    # Test manual label editing flow
    test_manual_label_editing()
    
    print("\nReturn door tests completed!")