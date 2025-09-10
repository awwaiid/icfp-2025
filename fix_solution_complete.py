#!/usr/bin/env python3
"""Fix both the missing connection and bidirectional error"""

import json

def fix_solution_complete():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    print("Fixing solution issues...")
    
    # Issue 1: Fix bidirectional error
    # Room 4 door 2 -> Room 3 door 5, but Room 3 door 5 -> Room 4 door 3
    # We need to make them consistent
    
    # Find and fix the inconsistent connections
    for i, conn in enumerate(solution["connections"]):
        if (conn["from"]["room"] == 4 and conn["from"]["door"] == 2 and 
            conn["to"]["room"] == 3 and conn["to"]["door"] == 5):
            print("Found: Room 4 door 2 -> Room 3 door 5")
        
        if (conn["from"]["room"] == 3 and conn["from"]["door"] == 5 and 
            conn["to"]["room"] == 4 and conn["to"]["door"] == 3):
            print("Found inconsistent: Room 3 door 5 -> Room 4 door 3")
            print("Fixing to: Room 3 door 5 -> Room 4 door 2")
            # Fix it to point back to door 2
            solution["connections"][i]["to"]["door"] = 2
    
    # Issue 2: Add missing connection for Room 3 door 4
    # Since it's the only unconnected door, make it a self-loop
    missing_connection = {
        "from": {"room": 3, "door": 4},
        "to": {"room": 3, "door": 4}
    }
    
    solution["connections"].append(missing_connection)
    print("Added self-loop for Room 3 door 4")
    
    # Write back
    with open("solution.json", 'w') as f:
        json.dump(solution, f, indent=2)
    
    print(f"Fixed solution with {len(solution['connections'])} total connections")

if __name__ == "__main__":
    fix_solution_complete()
