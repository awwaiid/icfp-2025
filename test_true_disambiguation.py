#!/usr/bin/env python3
"""
Test true room disambiguation using path navigation and label editing
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem

def create_ambiguous_scenario():
    """Create a scenario with truly ambiguous rooms that need path-based disambiguation
    
    Scenario:
    - Room A (0-010210) at path []
    - Room B (0-010210) at path [1, 2] (identical fingerprint!)  
    - Room C (1-??????) at path [0] (connects A and B)
    - Room D (2-??????) at path [1] (connects A and B)
    
    The key insight: A and B have identical fingerprints, but they are different physical rooms.
    To distinguish them:
    1. Start at A, edit its label to 3
    2. Navigate: A[3] -> C -> D -> B  (via doors 0, ?, 2)  
    3. Check if B still has original label 0 (different room) or modified label 3 (same room)
    """
    print("=== Creating Ambiguous Scenario for Testing ===")
    
    problem = Problem(room_count=4)
    
    # Create the scenario with API calls to simulate discovery
    print("Step 1: Bootstrap to discover initial room structure")
    
    # We'll simulate having discovered this structure:
    # Room A (label=0): [] -> doors: [1, 0, 2, 1, 0] -> [C, A, D, C, A] 
    # Room B (label=0): [1,2] -> doors: [1, 0, 2, 1, 0] -> [C, B, D, C, B] (identical!)
    # Room C (label=1): [0] -> doors: [0, ?, 0, ?, ?] -> [A, ?, B, ?, ?]
    # Room D (label=2): [2] -> doors: [0, 0, ?, ?, ?] -> [A, B, ?, ?, ?]
    
    # Let's start by exploring from the starting room
    try:
        # First explore the basic structure
        print("Exploring doors 0, 1, 2 from starting room...")
        result = problem.api_client.explore(["0", "1", "2"])
        
        if result and "results" in result:
            for i, (plan, rooms) in enumerate(zip(result["plans"], result["results"])):
                print(f"  Plan {plan}: {rooms}")
                problem.process_observation(plan, rooms)
        
        # Now explore from the discovered rooms to build the network
        print("\nExploring to build room network...")
        
        # From room at [0], explore doors to find connections back
        more_plans = ["01", "02", "10", "12", "20", "21"]
        result2 = problem.api_client.explore(more_plans)
        
        if result2 and "results" in result2:
            for plan, rooms in zip(result2["plans"], result2["results"]):
                print(f"  Plan {plan}: {rooms}")
                problem.process_observation(plan, rooms)
        
        print(f"\nDiscovered rooms:")
        problem.print_fingerprints()
        
        # Look for rooms with identical fingerprints
        complete_rooms = problem.room_manager.get_complete_rooms()
        fingerprint_groups = {}
        
        for room in complete_rooms:
            fp = room.get_fingerprint(include_disambiguation=False)
            if fp not in fingerprint_groups:
                fingerprint_groups[fp] = []
            fingerprint_groups[fp].append(room)
        
        ambiguous_groups = {fp: rooms for fp, rooms in fingerprint_groups.items() if len(rooms) > 1}
        
        if ambiguous_groups:
            print(f"\n🎯 Found ambiguous fingerprints:")
            for fp, rooms in ambiguous_groups.items():
                print(f"  {fp}: {len(rooms)} rooms")
                for room in rooms:
                    print(f"    Paths: {room.paths}")
            
            return problem, ambiguous_groups
        else:
            print("\n⚠️ No ambiguous fingerprints found in this run")
            print("This map might not have the ambiguous room scenario we need")
            return problem, {}
            
    except Exception as e:
        print(f"Error during exploration: {e}")
        import traceback
        traceback.print_exc()
        return problem, {}

def test_path_based_disambiguation(problem, ambiguous_groups):
    """Test path-based disambiguation using label editing"""
    print("\n=== Testing Path-Based Disambiguation ===")
    
    if not ambiguous_groups:
        print("No ambiguous rooms to test - skipping disambiguation test")
        return
    
    # Take the first ambiguous group
    fp, ambiguous_rooms = next(iter(ambiguous_groups.items()))
    print(f"Testing disambiguation for fingerprint: {fp}")
    
    if len(ambiguous_rooms) < 2:
        print("Need at least 2 rooms for disambiguation test")
        return
    
    room_a = ambiguous_rooms[0]
    room_b = ambiguous_rooms[1]
    
    print(f"Room A: {room_a.get_fingerprint()} at paths {room_a.paths}")
    print(f"Room B: {room_b.get_fingerprint()} at paths {room_b.paths}")
    
    # Find a path from room_a to room_b
    print(f"\nLooking for path from Room A to Room B...")
    
    path_a = room_a.paths[0] if room_a.paths else []
    path_b = room_b.paths[0] if room_b.paths else []
    
    print(f"Path to A: {path_a}")
    print(f"Path to B: {path_b}")
    
    # For disambiguation, we need to:
    # 1. Navigate to Room A
    # 2. Edit Room A's label to something unique (like 3)
    # 3. Navigate from A to B
    # 4. Check B's label - if it's still original, they're different rooms
    
    if len(path_b) > len(path_a):
        # B is reachable from A
        path_a_to_b = path_b[len(path_a):]  # The additional steps from A to B
        
        print(f"Constructing disambiguation test:")
        print(f"  1. Navigate to Room A: {path_a}")
        print(f"  2. Edit Room A's label to 3")  
        print(f"  3. Navigate from A to B: {path_a} + [3] + {path_a_to_b}")
        print(f"  4. Check B's final label")
        
        # Construct the test plan
        disambiguation_plan = path_a + ["[3]"] + path_a_to_b
        disambiguation_plan_str = "".join(str(x) for x in disambiguation_plan)
        
        print(f"\nExecuting disambiguation plan: {disambiguation_plan_str}")
        
        try:
            result = problem.api_client.explore([disambiguation_plan_str])
            
            if result and "results" in result:
                response = result["results"][0]
                plan_string = result["plan_strings"][0]
                
                print(f"Response: {response}")
                
                # Parse the response
                actual_labels, echo_labels = problem.api_client.parse_response_with_echoes(
                    plan_string, response
                )
                
                print(f"Parsed - Actual: {actual_labels}, Echoes: {echo_labels}")
                
                if actual_labels:
                    final_label = actual_labels[-1]
                    original_label = room_b.label
                    
                    print(f"\n🔍 Disambiguation Result:")
                    print(f"  Room B's original label: {original_label}")
                    print(f"  Room B's final label: {final_label}")
                    
                    if final_label == original_label:
                        print(f"  ✅ DIFFERENT ROOMS: B kept its original label {original_label}")
                        print(f"     Room A and Room B are physically different rooms!")
                    elif final_label == 3:  # Our edited label
                        print(f"  ❌ SAME ROOM: B has the edited label 3")
                        print(f"     Room A and Room B are the same physical room!")
                    else:
                        print(f"  ❓ UNCLEAR: B has unexpected label {final_label}")
                        
                else:
                    print("No labels in response - disambiguation failed")
                    
        except Exception as e:
            print(f"Disambiguation test failed: {e}")
            import traceback
            traceback.print_exc()
            
    else:
        print("Cannot find clear path from A to B for disambiguation test")

if __name__ == "__main__":
    print("Testing true room disambiguation with path navigation...\n")
    
    # Create the ambiguous scenario
    problem, ambiguous_groups = create_ambiguous_scenario()
    
    # Test path-based disambiguation
    test_path_based_disambiguation(problem, ambiguous_groups)
    
    print("\nDisambiguation test completed!")