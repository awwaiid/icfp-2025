#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import ambiguously.problem
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ambiguously.problem import Problem

def main():
    problem_name = "simple-2"
    expected_rooms = 2
    
    print(f"=== Step-by-Step Analysis of {problem_name} ===")
    
    # Initialize problem - use the same pattern as run.py
    p = Problem(room_count=expected_rooms)
    p.select_problem(problem_name)
    
    print("\n=== STEP 1: Bootstrap ===")
    p.bootstrap(problem_name)
    
    print("\n=== Bootstrap Results ===")
    print(f"Total rooms: {len(p.room_manager.get_all_rooms())}")
    print(f"Complete rooms: {len(p.room_manager.get_complete_rooms())}")
    print(f"Incomplete rooms: {len(p.room_manager.get_incomplete_rooms())}")
    
    for i, room in enumerate(p.room_manager.get_all_rooms()):
        print(f"Room {i}: {room.get_fingerprint()}")
        print(f"  Paths: {room.paths}")
        print(f"  Door labels: {room.door_labels}")
        print(f"  Is complete: {room.is_complete()}")
        print()
    
    print("Continuing to first exploration iteration...")
    
    print("\n=== STEP 2: First Exploration Iteration ===")
    
    # Check what the exploration strategy suggests
    exploration_batch = p.exploration_strategy.get_next_exploration_batch()
    if exploration_batch:
        print(f"Strategy suggests: {exploration_batch['type']}")
        print(f"Priority: {exploration_batch['priority']}")
        print(f"Data: {exploration_batch['data']}")
    else:
        print("No exploration suggested!")
        return
    
    # Do one round of exploration
    p.explore_incomplete_rooms()
    
    print("\n=== After First Exploration ===")
    print(f"Total rooms: {len(p.room_manager.get_all_rooms())}")
    print(f"Complete rooms: {len(p.room_manager.get_complete_rooms())}")
    print(f"Incomplete rooms: {len(p.room_manager.get_incomplete_rooms())}")
    
    for i, room in enumerate(p.room_manager.get_all_rooms()):
        print(f"Room {i}: {room.get_fingerprint()}")
        print(f"  Paths: {room.paths}")
        print(f"  Door labels: {room.door_labels}")
        print(f"  Is complete: {room.is_complete()}")
        print()
    
    print("Continuing to room merging...")
    
    print("\n=== STEP 3: Room Merging ===")
    
    # Try room merging
    merged_count = p.room_manager.merge_rooms_with_identical_partial_fingerprints(p.api_client)
    if merged_count > 0:
        print(f"Merged {merged_count} rooms")
    else:
        print("No rooms merged")
    
    print("\n=== After Room Merging ===")
    print(f"Total rooms: {len(p.room_manager.get_all_rooms())}")
    print(f"Complete rooms: {len(p.room_manager.get_complete_rooms())}")
    print(f"Incomplete rooms: {len(p.room_manager.get_incomplete_rooms())}")
    
    for i, room in enumerate(p.room_manager.get_all_rooms()):
        print(f"Room {i}: {room.get_fingerprint()}")
        print(f"  Paths: {room.paths}")
        print(f"  Door labels: {room.door_labels}")
        print(f"  Is complete: {room.is_complete()}")
        print()

    print("Continuing to second exploration iteration...")
    
    print("\n=== STEP 4: Second Exploration Iteration ===")
    
    # Check what the exploration strategy suggests
    exploration_batch = p.exploration_strategy.get_next_exploration_batch()
    if exploration_batch:
        print(f"Strategy suggests: {exploration_batch['type']}")
        print(f"Priority: {exploration_batch['priority']}")
        print(f"Data: {exploration_batch['data']}")
    else:
        print("No exploration suggested!")
        return
    
    # Do another round of exploration
    p.explore_incomplete_rooms()
    
    print("\n=== After Second Exploration ===")
    print(f"Total rooms: {len(p.room_manager.get_all_rooms())}")
    print(f"Complete rooms: {len(p.room_manager.get_complete_rooms())}")
    print(f"Incomplete rooms: {len(p.room_manager.get_incomplete_rooms())}")
    
    for i, room in enumerate(p.room_manager.get_all_rooms()):
        print(f"Room {i}: {room.get_fingerprint()}")
        print(f"  Paths: {room.paths}")
        print(f"  Door labels: {room.door_labels}")
        print(f"  Is complete: {room.is_complete()}")
        print()
    
    # Try room merging again
    print("\n=== Second Room Merging ===")
    merged_count = p.room_manager.merge_rooms_with_identical_partial_fingerprints(p.api_client)
    if merged_count > 0:
        print(f"Merged {merged_count} rooms")
    else:
        print("No rooms merged")
    
    print("\n=== After Second Room Merging ===")
    print(f"Total rooms: {len(p.room_manager.get_all_rooms())}")
    print(f"Complete rooms: {len(p.room_manager.get_complete_rooms())}")
    print(f"Incomplete rooms: {len(p.room_manager.get_incomplete_rooms())}")
    
    for i, room in enumerate(p.room_manager.get_all_rooms()):
        print(f"Room {i}: {room.get_fingerprint()}")
        print(f"  Paths: {room.paths}")
        print(f"  Door labels: {room.door_labels}")
        print(f"  Is complete: {room.is_complete()}")
        print()

if __name__ == "__main__":
    main()