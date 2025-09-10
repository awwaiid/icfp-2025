#!/usr/bin/env python3
"""Fix bidirectional consistency errors"""

import json

def fix_bidirectional():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Build connection map
    connections = {}
    for i, conn in enumerate(solution["connections"]):
        from_key = (conn["from"]["room"], conn["from"]["door"])
        to_key = (conn["to"]["room"], conn["to"]["door"])
        connections[from_key] = (to_key, i)
    
    # Find bidirectional errors
    errors = []
    for from_key, (to_key, idx) in connections.items():
        if to_key in connections:
            reverse_to_key, reverse_idx = connections[to_key]
            if reverse_to_key != from_key:
                errors.append((from_key, to_key, reverse_to_key, idx, reverse_idx))
    
    print(f"Found {len(errors)} bidirectional errors")
    
    for from_key, to_key, wrong_reverse, idx, reverse_idx in errors:
        print(f"Error: {from_key} -> {to_key}, but {to_key} -> {wrong_reverse}")
        
        # Fix by updating the reverse connection to point back correctly
        solution["connections"][reverse_idx]["to"]["room"] = from_key[0]
        solution["connections"][reverse_idx]["to"]["door"] = from_key[1]
        
        print(f"Fixed: {to_key} now points to {from_key}")
    
    # Write back
    with open("solution.json", 'w') as f:
        json.dump(solution, f, indent=2)
    
    print("Fixed bidirectional errors")

if __name__ == "__main__":
    fix_bidirectional()
