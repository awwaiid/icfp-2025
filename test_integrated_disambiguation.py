#!/usr/bin/env python3
"""
Test integrated disambiguation during exploration
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem

def test_integrated_disambiguation():
    """Test that disambiguation runs automatically during exploration"""
    print("=== Testing Integrated Disambiguation During Exploration ===")
    
    problem = Problem(room_count=6)
    
    print("Step 1: Bootstrap exploration to discover initial rooms")
    try:
        problem.bootstrap("primus")
        
        print(f"\nAfter bootstrap:")
        problem.print_fingerprints()
        
        print(f"\nStep 2: Continue exploration to potentially find ambiguous rooms")
        
        # Do some more exploration that might create duplicate fingerprints
        initial_complete_count = len(problem.room_manager.get_complete_rooms())
        
        # Explore more to potentially trigger disambiguation
        for iteration in range(3):
            print(f"\n--- Exploration iteration {iteration + 1} ---")
            
            initial_room_count = len(problem.room_manager.possible_rooms)
            
            # Do one round of exploration
            problem.explore_incomplete_rooms()
            
            final_room_count = len(problem.room_manager.possible_rooms)
            
            print(f"Room count: {initial_room_count} -> {final_room_count}")
            
            # Check for rooms with disambiguation IDs
            disambiguated_rooms = []
            for room in problem.room_manager.get_complete_rooms():
                if hasattr(room, 'disambiguation_id') and room.disambiguation_id is not None:
                    disambiguated_rooms.append(room)
            
            if disambiguated_rooms:
                print(f"🎯 Found {len(disambiguated_rooms)} disambiguated rooms:")
                for room in disambiguated_rooms:
                    print(f"  {room.get_fingerprint()} (disambig_id={room.disambiguation_id})")
                break
                
            # If we have complete coverage, stop
            complete_rooms = problem.room_manager.get_complete_rooms()
            if len(complete_rooms) >= problem.room_count:
                unique_complete = len(set(r.get_fingerprint(include_disambiguation=False) for r in complete_rooms))
                if unique_complete >= problem.room_count:
                    print("Complete coverage achieved - stopping exploration")
                    break
        
        # Final analysis
        print(f"\n=== Final Analysis ===")
        complete_rooms = problem.room_manager.get_complete_rooms()
        
        # Group by base fingerprint
        base_fingerprints = {}
        for room in complete_rooms:
            base_fp = room.get_fingerprint(include_disambiguation=False)
            if base_fp not in base_fingerprints:
                base_fingerprints[base_fp] = []
            base_fingerprints[base_fp].append(room)
        
        ambiguous_groups = {fp: rooms for fp, rooms in base_fingerprints.items() if len(rooms) > 1}
        
        print(f"Base fingerprints found: {len(base_fingerprints)}")
        print(f"Ambiguous fingerprints: {len(ambiguous_groups)}")
        
        if ambiguous_groups:
            print(f"Ambiguous fingerprint details:")
            for fp, rooms in ambiguous_groups.items():
                print(f"  {fp}: {len(rooms)} rooms")
                for room in rooms:
                    disambig_id = getattr(room, 'disambiguation_id', None)
                    full_fp = room.get_fingerprint()
                    print(f"    {full_fp} (disambig_id={disambig_id}) at paths {room.paths}")
        else:
            print("No ambiguous fingerprints found")
        
        # Test manual disambiguation trigger
        print(f"\n=== Testing Manual Disambiguation Trigger ===")
        if len(ambiguous_groups) == 0:
            print("Creating artificial ambiguity for testing...")
            
            # Find two rooms we can test disambiguation on
            if len(complete_rooms) >= 2:
                room_a = complete_rooms[0]
                room_b = complete_rooms[1]
                
                print(f"Testing disambiguation between:")
                print(f"  Room A: {room_a.get_fingerprint()} at paths {room_a.paths}")
                print(f"  Room B: {room_b.get_fingerprint()} at paths {room_b.paths}")
                
                # Test the disambiguation method directly
                try:
                    are_different = problem.room_manager.disambiguate_rooms_with_path_navigation(
                        room_a, room_b, problem.api_client
                    )
                    print(f"Disambiguation result: {'DIFFERENT' if are_different else 'SAME or UNCLEAR'}")
                    
                except Exception as e:
                    print(f"Disambiguation test failed: {e}")
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()

def test_manual_duplicate_room_processing():
    """Test the duplicate room processing with manual setup"""
    print("\n=== Testing Manual Duplicate Room Processing ===")
    
    problem = Problem(room_count=4)
    
    # Create two rooms with identical fingerprints but different paths
    from ambiguously.room import Room
    
    room_a = Room(label=0)
    room_a.add_path([])
    room_a.door_labels = [1, 2, 3, 0, 0, 0]  # 0-123000
    
    room_b = Room(label=0)
    room_b.add_path([1, 2])
    room_b.door_labels = [1, 2, 3, 0, 0, 0]  # 0-123000 (identical)
    
    problem.room_manager.possible_rooms = [room_a, room_b]
    
    print("Setup: Two rooms with identical fingerprints")
    print(f"  Room A: {room_a.get_fingerprint()} at path {room_a.paths[0]}")
    print(f"  Room B: {room_b.get_fingerprint()} at path {room_b.paths[0]}")
    
    # Test the integrated disambiguation
    print(f"\nTrigger duplicate room processing...")
    removed = problem.room_manager.remove_duplicate_rooms(problem.api_client)
    
    print(f"\nResult: {removed} rooms removed")
    print(f"Remaining rooms: {len(problem.room_manager.possible_rooms)}")
    
    for i, room in enumerate(problem.room_manager.possible_rooms):
        disambig_id = getattr(room, 'disambiguation_id', None)
        print(f"  Room {i}: {room.get_fingerprint()} (disambig_id={disambig_id})")

if __name__ == "__main__":
    print("Testing integrated disambiguation functionality...\n")
    
    # Test during actual exploration
    test_integrated_disambiguation()
    
    # Test manual processing
    test_manual_duplicate_room_processing()
    
    print("\nIntegrated disambiguation tests completed!")