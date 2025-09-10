#!/usr/bin/env python3
"""Add self-loop for the remaining door"""

import json

def add_self_loop():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Add self-loop for room 2 door 4
    self_loop = {
        "from": {"room": 2, "door": 4},
        "to": {"room": 2, "door": 4}
    }
    
    solution["connections"].append(self_loop)
    
    with open("solution.json", 'w') as f:
        json.dump(solution, f, indent=2)
    
    print(f"Added self-loop for room 2 door 4")
    print(f"Total connections: {len(solution['connections'])}")

if __name__ == "__main__":
    add_self_loop()
