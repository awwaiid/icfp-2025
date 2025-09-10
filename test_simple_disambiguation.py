#!/usr/bin/env python3
"""
Simple test of path-based room disambiguation
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem
from ambiguously.room import Room

def test_simple_disambiguation():
    """Test disambiguation with a manually constructed simple scenario"""
    print("=== Testing Simple Path-Based Disambiguation ===")
    
    problem = Problem(room_count=4)
    
    # Manually create a simple scenario where we can test disambiguation
    print("Creating test scenario:")
    print("  Room A: 0-123000 at path []")
    print("  Room B: 0-123000 at path [1, 2] (identical fingerprint!)")
    print("  Room C: 1-?????? at path [1]")  
    print("  Room D: 2-?????? at path [1, 2]")
    
    # Create rooms manually
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.door_labels = [1, 2, 3, 0, 0, 0]  # 0-123000
    
    room_b = Room(label=0)
    room_b.add_path([1, 2])  # Different path but same fingerprint
    room_b.door_labels = [1, 2, 3, 0, 0, 0]  # 0-123000 (identical!)
    
    room_c = Room(label=1)
    room_c.add_path([1])
    room_c.door_labels = [0, 1, 2, 1, 1, 1]  # Some connections
    
    room_d = Room(label=2) 
    room_d.add_path([1, 2])
    room_d.door_labels = [2, 2, 0, 2, 2, 2]  # Door 2 leads back to room with label 0
    
    problem.room_manager.possible_rooms = [room_a, room_b, room_c, room_d]
    
    print(f"\nSetup complete:")
    for i, room in enumerate(problem.room_manager.possible_rooms):
        print(f"  Room {i}: {room.get_fingerprint(include_disambiguation=False)} at path {room.paths[0]}")
    
    # Check for identical fingerprints
    base_fingerprints = {}
    for room in problem.room_manager.possible_rooms:
        fp = room.get_fingerprint(include_disambiguation=False)
        if fp not in base_fingerprints:
            base_fingerprints[fp] = []
        base_fingerprints[fp].append(room)
    
    ambiguous_pairs = [(fp, rooms) for fp, rooms in base_fingerprints.items() if len(rooms) > 1]
    
    if ambiguous_pairs:
        fp, ambiguous_rooms = ambiguous_pairs[0]
        print(f"\n🎯 Found ambiguous fingerprint: {fp}")
        
        room_a, room_b = ambiguous_rooms[0], ambiguous_rooms[1]
        print(f"  Room A: path {room_a.paths[0]}")
        print(f"  Room B: path {room_b.paths[0]}")
        
        # Test disambiguation
        print(f"\n🔬 Testing disambiguation...")
        print("Expected: If rooms are different, B should keep its original label 0")
        print("If rooms are same, B should show the edited label")
        
        is_different = problem.room_manager.disambiguate_rooms_with_path_navigation(
            room_a, room_b, problem.api_client
        )
        
        print(f"\n📊 Disambiguation result: {'DIFFERENT rooms' if is_different else 'SAME room or unclear'}")
        
        # Also test the reverse direction if possible
        if room_a.paths[0] and len(room_a.paths[0]) > len(room_b.paths[0]):
            print(f"\n🔄 Testing reverse disambiguation (B -> A)...")
            is_different_reverse = problem.room_manager.disambiguate_rooms_with_path_navigation(
                room_b, room_a, problem.api_client
            )
            print(f"Reverse result: {'DIFFERENT rooms' if is_different_reverse else 'SAME room or unclear'}")
        
    else:
        print("❌ No ambiguous fingerprints found in manual setup")

def test_manual_disambiguation_exploration():
    """Test the disambiguation logic manually with specific API calls"""
    print("\n=== Manual Disambiguation Test ===")
    
    problem = Problem(room_count=6)
    
    print("Step 1: Manual path exploration to create potential ambiguity")
    
    # Do a few explorations to see what we get
    plans = ["0", "01", "012"]
    
    try:
        result = problem.api_client.explore(plans)
        if result and "results" in result:
            print("Exploration results:")
            for plan, rooms in zip(result["plans"], result["results"]):
                print(f"  {plan} -> {rooms}")
        
        print("\nStep 2: Test manual disambiguation approach")
        
        # Test the exact disambiguation pattern: start -> edit -> path -> check
        disambiguation_plan = "[3]01"  # Edit current room to label 3, then go door 0, then door 1
        
        print(f"Testing plan: {disambiguation_plan}")
        result2 = problem.api_client.explore([disambiguation_plan])
        
        if result2 and "results" in result2:
            response = result2["results"][0]
            actual, echoes = problem.api_client.parse_response_with_echoes(disambiguation_plan, response)
            
            print(f"Response: {response}")
            print(f"Parsed - Actual: {actual}, Echoes: {echoes}")
            print(f"Final room label: {actual[-1] if actual else 'none'}")
            
            if actual and len(actual) >= 3:
                start_label = actual[0]
                intermediate_label = actual[1] 
                final_label = actual[-1]
                
                print(f"Label progression: {start_label} -> {intermediate_label} -> {final_label}")
                
                if final_label == 3:
                    print("✅ Final room has edited label - rooms are connected/same")
                elif final_label != 3:
                    print("✅ Final room has different label - rooms are separate")
            
    except Exception as e:
        print(f"Manual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing simple room disambiguation...\n")
    
    # Test with manual setup
    test_simple_disambiguation()
    
    # Test with manual API exploration
    test_manual_disambiguation_exploration()
    
    print("\nSimple disambiguation tests completed!")