#!/usr/bin/env python3
"""Connect the missing door by exploring it directly"""

import json
import requests
import os

# API client
api_url = os.environ.get('ICFP_API_URL', 'https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com')

def explore(plans):
    response = requests.post(
        f"{api_url}/explore",
        headers={"Content-Type": "application/json"},
        json={"team": "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A", "plans": plans}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} {response.text}")
        return None

def connect_missing_door():
    # Load current solution
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Room 2 door 4 is unconnected - we need to find what it connects to
    # First, let's find a path to room 2
    # Looking at the rooms, room 2 has label 1
    # We need to trace a path to reach room 2, then explore door 4
    
    # Let's try exploring from the root - based on the algorithm, room 1 should be reachable
    # Let's find what paths exist to room 2
    
    print("Exploring to find what Room 2 door 4 connects to...")
    
    # Try various paths that might lead to room 2, then explore door 4
    # Based on the solution structure, let's try some exploration
    
    # Looking at the current connections, room 1 (index) connects to room 2 via door 2
    # So room 2 should be reachable via path from starting room -> room 1 -> door 2
    # Starting room is index 1, which has label 0
    # We need to find the path to room 2 (which has label 1)
    
    # Let's try exploring door 4 from various paths to room with label 1
    
    test_plans = [
        "24",  # If room 2 is reachable via door 2, then explore its door 4 
        "024", # Try via door 0 then door 2 then door 4
        "124", # Try via door 1 then door 2 then door 4
        "0024", # Longer path
    ]
    
    for plan in test_plans:
        print(f"Trying plan: {plan}")
        result = explore([plan])
        if result and "results" in result:
            result_data = result["results"][0]
            print(f"Result: {result_data}")
            
            # Parse the result to see what door 4 connects to
            if len(result_data) > len(plan):
                target_label = result_data[len(plan)]
                print(f"Door 4 leads to room with label: {target_label}")
                
                # Now we need to find which room index has this label and is reachable by this path
                # And find an available door on that room to connect back
                
                # Add the missing connection manually
                # For now, let's make a simple connection based on what we found
                missing_connections = []
                
                # Find an available door on a room with the target label
                room_labels = solution["rooms"]
                for room_idx, label in enumerate(room_labels):
                    if label == target_label:
                        # Check if any door of this room is available
                        for door in range(6):
                            door_used = False
                            for conn in solution["connections"]:
                                if conn["from"]["room"] == room_idx and conn["from"]["door"] == door:
                                    door_used = True
                                    break
                            if not door_used:
                                # Found an available door - connect it
                                conn1 = {
                                    "from": {"room": 2, "door": 4},
                                    "to": {"room": room_idx, "door": door}
                                }
                                conn2 = {
                                    "from": {"room": room_idx, "door": door},
                                    "to": {"room": 2, "door": 4}
                                }
                                missing_connections.extend([conn1, conn2])
                                print(f"Would connect: Room 2 door 4 <-> Room {room_idx} door {door}")
                                break
                    if missing_connections:
                        break
                
                if missing_connections:
                    solution["connections"].extend(missing_connections)
                    with open("solution.json", 'w') as f:
                        json.dump(solution, f, indent=2)
                    print("Added missing connections to solution.json")
                    return
                
                break
    
    print("Could not determine missing connection automatically")

if __name__ == "__main__":
    connect_missing_door()
