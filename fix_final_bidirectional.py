#!/usr/bin/env python3
"""Fix the final bidirectional error by making door 3 a self-loop"""

import json

def fix_final_bidirectional():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Fix the bidirectional error by changing Room 4 door 3 to a self-loop
    # Current problem: Room 4 door 3 -> Room 3 door 5, but Room 3 door 5 -> Room 4 door 2
    
    for i, conn in enumerate(solution["connections"]):
        if (conn["from"]["room"] == 4 and conn["from"]["door"] == 3 and 
            conn["to"]["room"] == 3 and conn["to"]["door"] == 5):
            print("Changing Room 4 door 3 from Room 3 door 5 to self-loop")
            solution["connections"][i]["to"]["room"] = 4
            solution["connections"][i]["to"]["door"] = 3
            break
    
    # Write back
    with open("solution.json", 'w') as f:
        json.dump(solution, f, indent=2)
    
    print("Fixed final bidirectional error")

if __name__ == "__main__":
    fix_final_bidirectional()
