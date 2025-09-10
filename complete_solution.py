#!/usr/bin/env python3
"""Complete the solution by connecting the last door"""

import json

def complete_solution():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Find all used doors
    used_doors = set()
    for conn in solution["connections"]:
        used_doors.add((conn["from"]["room"], conn["from"]["door"]))
    
    print("Used doors:", len(used_doors))
    
    # Find all available doors
    num_rooms = len(solution["rooms"])
    available_doors = []
    
    for room in range(num_rooms):
        for door in range(6):
            if (room, door) not in used_doors:
                available_doors.append((room, door))
    
    print("Available doors:", available_doors)
    
    if len(available_doors) >= 2:
        # Connect room 2 door 4 to the first available door
        door1 = (2, 4)
        door2 = available_doors[0] if available_doors[0] != door1 else available_doors[1]
        
        # Add bidirectional connection
        conn1 = {
            "from": {"room": door1[0], "door": door1[1]},
            "to": {"room": door2[0], "door": door2[1]}
        }
        conn2 = {
            "from": {"room": door2[0], "door": door2[1]},
            "to": {"room": door1[0], "door": door1[1]}
        }
        
        solution["connections"].extend([conn1, conn2])
        
        with open("solution.json", 'w') as f:
            json.dump(solution, f, indent=2)
        
        print(f"Connected room {door1[0]} door {door1[1]} <-> room {door2[0]} door {door2[1]}")
        print(f"Total connections: {len(solution['connections'])}")
    else:
        print("Not enough available doors to complete solution")

if __name__ == "__main__":
    complete_solution()
