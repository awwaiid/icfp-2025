#!/usr/bin/env python3
"""
Solution validation script to check bidirectional consistency and completeness
"""

import json
import sys

def validate_solution(filename="solution.json"):
    """Validate the solution for completeness and bidirectional consistency"""
    
    try:
        with open(filename, 'r') as f:
            solution = json.load(f)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return False
    
    rooms = solution["rooms"]
    connections = solution["connections"]
    starting_room = solution["startingRoom"]
    
    num_rooms = len(rooms)
    total_doors = num_rooms * 6
    
    print(f"=== Solution Validation ===")
    print(f"Rooms: {num_rooms}")
    print(f"Room labels: {rooms}")
    print(f"Starting room: {starting_room}")
    print(f"Total doors: {total_doors}")
    print(f"Total connection entries: {len(connections)}")
    
    # Create a map of (room, door) -> (target_room, target_door)
    door_map = {}
    
    # Track which doors are connected
    connected_doors = set()
    
    for conn in connections:
        from_room = conn["from"]["room"]
        from_door = conn["from"]["door"]
        to_room = conn["to"]["room"]
        to_door = conn["to"]["door"]
        
        door_key = (from_room, from_door)
        target = (to_room, to_door)
        
        if door_key in door_map:
            print(f"ERROR: Duplicate connection for room {from_room} door {from_door}")
            return False
            
        door_map[door_key] = target
        connected_doors.add(door_key)
    
    # Check bidirectional consistency
    bidirectional_errors = 0
    
    print(f"\n=== Bidirectional Consistency Check ===")
    
    for (from_room, from_door), (to_room, to_door) in door_map.items():
        reverse_key = (to_room, to_door)
        if reverse_key not in door_map:
            print(f"ERROR: Room {from_room} door {from_door} -> Room {to_room} door {to_door}, but no reverse connection")
            bidirectional_errors += 1
        else:
            reverse_target = door_map[reverse_key]
            if reverse_target != (from_room, from_door):
                print(f"ERROR: Room {from_room} door {from_door} -> Room {to_room} door {to_door}, but Room {to_room} door {to_door} -> {reverse_target}")
                bidirectional_errors += 1
    
    if bidirectional_errors == 0:
        print("✅ All connections are bidirectionally consistent")
    else:
        print(f"❌ Found {bidirectional_errors} bidirectional errors")
    
    # Check completeness - every door should be connected
    print(f"\n=== Completeness Check ===")
    
    unconnected_doors = []
    for room in range(num_rooms):
        for door in range(6):
            door_key = (room, door)
            if door_key not in connected_doors:
                unconnected_doors.append(door_key)
    
    if len(unconnected_doors) == 0:
        print(f"✅ All {total_doors} doors are connected")
    else:
        print(f"❌ {len(unconnected_doors)} doors are not connected:")
        for room, door in unconnected_doors:
            print(f"  Room {room} door {door}")
    
    # Summary
    print(f"\n=== Summary ===")
    connected_count = len(connected_doors)
    success = bidirectional_errors == 0 and len(unconnected_doors) == 0
    
    print(f"Connected doors: {connected_count}/{total_doors}")
    print(f"Bidirectional errors: {bidirectional_errors}")
    print(f"Unconnected doors: {len(unconnected_doors)}")
    print(f"Overall result: {'✅ VALID' if success else '❌ INVALID'}")
    
    return success

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "solution.json"
    validate_solution(filename)
