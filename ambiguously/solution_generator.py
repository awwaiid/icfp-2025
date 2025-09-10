"""
Solution Generator for the ICFP 2025 room exploration problem
"""

import json
from typing import Dict, Any, List


class SolutionGenerator:
    """Handles solution generation in the required JSON format"""

    def __init__(self, room_manager):
        self.room_manager = room_manager

    def generate_solution(self, filename: str = "solution.json", problem=None) -> Dict[str, Any]:
        """Generate the solution in the JSON format expected by bin/guess"""
        print("=== SOLUTION FOR bin/guess ===")

        # Get all complete rooms sorted by absolute ID
        complete_rooms = self.room_manager.get_complete_rooms()
        fingerprint_to_absolute_id = self.room_manager.get_absolute_room_mapping()

        # Create mapping from absolute ID to room
        absolute_id_to_room = {}
        for room in complete_rooms:
            fp = room.get_fingerprint()
            if fp in fingerprint_to_absolute_id:
                absolute_id_to_room[fingerprint_to_absolute_id[fp]] = room

        # Create the rooms array with actual labels (not absolute IDs)
        # The rooms array should contain the labels in absolute ID order
        rooms_array = []
        absolute_id_to_index = {}

        for abs_id in sorted(absolute_id_to_room.keys()):
            room = absolute_id_to_room[abs_id]
            rooms_array.append(room.label)  # Use the actual label, not absolute ID
            absolute_id_to_index[abs_id] = len(rooms_array) - 1  # Track index mapping

        print("Room index mapping:")
        for abs_id in sorted(absolute_id_to_room.keys()):
            room = absolute_id_to_room[abs_id]
            index = absolute_id_to_index[abs_id]
            print(
                f"Index {index}: Label {room.label} (fingerprint {room.get_fingerprint()})"
            )
        
        print(f"\n=== ANALYZING ALL STORED CONNECTIONS ===")
        print(f"Total stored connections: {len(problem.connections)}")
        for (room_fp, door), (target_fp, target_door) in sorted(problem.connections.items()):
            print(f"STORED: {room_fp} door {door} -> {target_fp} door {target_door}")

        # Generate the solution JSON (only the map part - bin/guess adds the id)
        solution = {
            "rooms": rooms_array,
            "startingRoom": 0,  # Will be updated below
            "connections": [],
        }

        # Generate connections using the clean stored connections from problem
        if problem is None or not hasattr(problem, 'connections'):
            raise RuntimeError("FATAL: Problem instance with stored connections required")
        
        # Track processed connections to ensure each bidirectional pair is only added once
        processed_connections = set()
        added_connections = set()  # Track actual connections added to avoid duplicates
        
        for from_abs_id in sorted(absolute_id_to_room.keys()):
            from_room = absolute_id_to_room[from_abs_id]
            from_index = absolute_id_to_index[from_abs_id]
            from_fp = from_room.get_fingerprint()

            # Use the clean stored connections from problem.connections
            for from_door in range(6):
                # Skip if we've already processed this connection
                connection_key = (from_fp, from_door)
                if connection_key in processed_connections:
                    continue
                    
                # Get connection from stored data
                connection = problem.get_connection(from_fp, from_door)
                if connection is None:
                    print(f"  No connection stored for {from_fp} door {from_door}")
                    continue
                    
                to_fp, to_door = connection
                print(f"  CLEAN: {from_fp} door {from_door} -> {to_fp} door {to_door}")
                
                # Find the absolute ID and index of destination room
                if to_fp not in fingerprint_to_absolute_id:
                    print(f"SKIP: Connection destination room {to_fp} not found in final room mapping")
                    continue
                
                to_abs_id = fingerprint_to_absolute_id[to_fp]
                to_index = absolute_id_to_index[to_abs_id]
                print(f"  SOLUTION: {from_fp} door {from_door} -> {to_fp} (abs_id {to_abs_id} = index {to_index}) door {to_door}")
                print(f"  MAPPING: room {from_index} door {from_door} -> room {to_index} door {to_door}")
                
                # We already have the clean return door from stored connections - no complex calculation needed!

                # Check for duplicates before adding
                conn1 = (from_index, from_door, to_index, to_door)
                conn2 = (to_index, to_door, from_index, from_door)
                
                if conn1 not in added_connections and conn2 not in added_connections:
                    # Handle self-loops: only add one direction for self-connections
                    if from_index == to_index and from_door == to_door:
                        print(f"  SELF-LOOP: room {from_index} door {from_door} -> room {to_index} door {to_door}")
                        # Only add one connection for self-loops
                        solution["connections"].append(
                            {
                                "from": {
                                    "room": from_index,
                                    "door": from_door,
                                },
                                "to": {
                                    "room": to_index,
                                    "door": to_door,
                                },
                            }
                        )
                        added_connections.add(conn1)
                    else:
                        # Add BOTH directions for normal connections
                        solution["connections"].append(
                            {
                                "from": {
                                    "room": from_index,
                                    "door": from_door,
                                },
                                "to": {
                                    "room": to_index,
                                    "door": to_door,
                                },
                            }
                        )
                        
                        solution["connections"].append(
                            {
                                "from": {
                                    "room": to_index,
                                    "door": to_door,
                                },
                                "to": {
                                    "room": from_index,
                                    "door": from_door,
                                },
                            }
                        )
                        
                        # Mark both directions as added
                        added_connections.add(conn1)
                        added_connections.add(conn2)
                else:
                    print(f"  SKIP DUPLICATE: {from_index}:{from_door} <-> {to_index}:{to_door}")
                
                # Mark both directions as processed to avoid duplicates
                processed_connections.add((from_fp, from_door))
                processed_connections.add((to_fp, to_door))

        # Find the actual starting room (the one with empty path) and convert to index
        # Look for the room that has the empty path and disambiguation ID 0 (original room)
        starting_room_found = False
        for abs_id, room in absolute_id_to_room.items():
            if [] in room.paths:
                # Prefer the room with disambiguation ID 0 (the original room)
                if hasattr(room, 'disambiguation_id') and room.disambiguation_id == 0:
                    solution["startingRoom"] = absolute_id_to_index[abs_id]
                    starting_room_found = True
                    break
                # Fallback: if no room with disambiguation ID 0, use the first one found
                elif not starting_room_found:
                    solution["startingRoom"] = absolute_id_to_index[abs_id]
                    starting_room_found = True

        # Write to file with double quotes
        with open(filename, "w") as f:
            json.dump(solution, f, indent=2, ensure_ascii=False)

        print(f"\nSolution written to {filename}")
        print(f"Rooms: {solution['rooms']}")
        print(
            f"Starting room index: {solution['startingRoom']} (label {rooms_array[solution['startingRoom']]})"
        )
        print(f"Total connections: {len(solution['connections'])}")

        print("\nTo submit, run:")
        print(f"python bin/guess {filename}")

        return solution
