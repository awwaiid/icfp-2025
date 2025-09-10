#!/usr/bin/env python3
"""Fix solution.json by removing duplicates and ensuring all doors are connected exactly once"""

import json

def fix_solution(filename="solution.json"):
    with open(filename, 'r') as f:
        solution = json.load(f)
    
    connections = solution["connections"]
    
    # Create a clean connection map
    door_map = {}
    clean_connections = []
    
    for conn in connections:
        from_room = conn["from"]["room"]
        from_door = conn["from"]["door"]
        to_room = conn["to"]["room"] 
        to_door = conn["to"]["door"]
        
        door_key = (from_room, from_door)
        
        # Skip if we've already seen this door
        if door_key in door_map:
            print(f"SKIP DUPLICATE: room {from_room} door {from_door}")
            continue
            
        # Add to clean list
        clean_connections.append(conn)
        door_map[door_key] = (to_room, to_door)
    
    # Update solution
    solution["connections"] = clean_connections
    
    # Write back
    with open(filename, 'w') as f:
        json.dump(solution, f, indent=2)
    
    print(f"Fixed solution: {len(clean_connections)} connections")
    
    # Check for unconnected doors
    num_rooms = len(solution["rooms"])
    connected_doors = set(door_map.keys())
    
    unconnected = []
    for room in range(num_rooms):
        for door in range(6):
            if (room, door) not in connected_doors:
                unconnected.append((room, door))
    
    print(f"Unconnected doors: {len(unconnected)}")
    for room, door in unconnected:
        print(f"  Room {room} door {door}")

if __name__ == "__main__":
    fix_solution()
