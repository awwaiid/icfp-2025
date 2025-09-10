#!/usr/bin/env python3
"""Add the missing connection for Room 5 door 3"""

import json

def add_missing_connection():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Add self-loop for room 5 door 3
    missing_connection = {
        "from": {"room": 5, "door": 3},
        "to": {"room": 5, "door": 3}
    }
    
    solution["connections"].append(missing_connection)
    
    with open("solution.json", 'w') as f:
        json.dump(solution, f, indent=2)
    
    print(f"Added self-loop for Room 5 door 3")
    print(f"Total connections: {len(solution['connections'])}")

if __name__ == "__main__":
    add_missing_connection()
