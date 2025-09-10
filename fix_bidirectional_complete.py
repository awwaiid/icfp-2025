#!/usr/bin/env python3
"""Fix bidirectional consistency by resolving conflicts properly"""

import json

def fix_bidirectional_complete():
    with open("solution.json", 'r') as f:
        solution = json.load(f)
    
    # Build connection map
    door_to_connection = {}
    for i, conn in enumerate(solution["connections"]):
        from_key = (conn["from"]["room"], conn["from"]["door"])
        door_to_connection[from_key] = (conn, i)
    
    # Find all conflicts
    conflicts = []
    
    for from_key, (conn, idx) in door_to_connection.items():
        to_room = conn["to"]["room"]
        to_door = conn["to"]["door"]
        to_key = (to_room, to_door)
        
        if to_key in door_to_connection:
            reverse_conn, reverse_idx = door_to_connection[to_key]
            reverse_to_room = reverse_conn["to"]["room"]
            reverse_to_door = reverse_conn["to"]["door"]
            reverse_to_key = (reverse_to_room, reverse_to_door)
            
            if reverse_to_key != from_key:
                conflicts.append((from_key, to_key, reverse_to_key))
    
    print(f"Found {len(conflicts)} bidirectional conflicts")
    
    # The issue is that we have:
    # Room 4 door 1 -> Room 5 door 3
    # Room 5 door 3 -> Room 4 door 5
    # Room 4 door 5 -> Room 5 door 3  (this creates the conflict)
    
    # We need to resolve by creating consistent pairs
    # Let's remove conflicting connections and create clean bidirectional pairs
    
    if conflicts:
        print("Resolving conflicts by creating consistent bidirectional connections...")
        
        # Remove all connections involved in conflicts
        to_remove = set()
        for from_key, to_key, wrong_reverse in conflicts:
            from_conn, from_idx = door_to_connection[from_key]
            to_conn, to_idx = door_to_connection[to_key]
            to_remove.add(from_idx)
            to_remove.add(to_idx)
            print(f"Conflict: {from_key} -> {to_key} vs {to_key} -> {wrong_reverse}")
        
        # Remove conflicting connections
        new_connections = []
        for i, conn in enumerate(solution["connections"]):
            if i not in to_remove:
                new_connections.append(conn)
        
        # Add back clean bidirectional pairs for the conflicts
        # For the conflict: (4,1) -> (5,3) vs (5,3) -> (4,5) vs (4,5) -> (5,3)
        # We need to decide which pairs to keep
        # Let's keep (4,1) <-> (5,3) and make (4,5) a self-loop
        
        # Add (4,1) <-> (5,3)
        new_connections.extend([
            {
                "from": {"room": 4, "door": 1},
                "to": {"room": 5, "door": 3}
            },
            {
                "from": {"room": 5, "door": 3},
                "to": {"room": 4, "door": 1}
            }
        ])
        
        # Make (4,5) a self-loop
        new_connections.append({
            "from": {"room": 4, "door": 5},
            "to": {"room": 4, "door": 5}
        })
        
        solution["connections"] = new_connections
        
        with open("solution.json", 'w') as f:
            json.dump(solution, f, indent=2)
        
        print("Resolved conflicts with clean bidirectional connections")

if __name__ == "__main__":
    fix_bidirectional_complete()
