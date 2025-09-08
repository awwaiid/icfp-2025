"""
Solution Generator for the ICFP 2025 room exploration problem
"""

import json
from typing import Dict, Any, List


class SolutionGenerator:
    """Handles solution generation in the required JSON format"""

    def __init__(self, room_manager):
        self.room_manager = room_manager

    def generate_solution(self, filename: str = "solution.json") -> Dict[str, Any]:
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

        # Generate the solution JSON (only the map part - bin/guess adds the id)
        solution = {
            "rooms": rooms_array,
            "startingRoom": 0,  # Will be updated below
            "connections": [],
        }

        # Generate connections using direct door_rooms data from systematic exploration
        for from_abs_id in sorted(absolute_id_to_room.keys()):
            from_room = absolute_id_to_room[from_abs_id]
            from_index = absolute_id_to_index[from_abs_id]

            # Use the direct door_rooms connections recorded during exploration
            for from_door in range(6):
                to_room = from_room.door_rooms[from_door]
                
                if to_room is None:
                    raise RuntimeError(f"FATAL: Room {from_abs_id} door {from_door} has no connection recorded. This indicates incomplete systematic exploration.")
                
                # Find the absolute ID and index of destination room
                to_fp = to_room.get_fingerprint()
                if to_fp not in fingerprint_to_absolute_id:
                    raise RuntimeError(f"FATAL: Destination room {to_fp} not found in absolute ID mapping.")
                
                to_abs_id = fingerprint_to_absolute_id[to_fp]
                to_index = absolute_id_to_index[to_abs_id]
                
                # Find the return door using the backlink information
                if hasattr(to_room, 'path_to_root') and to_room.path_to_root:
                    # Use the calculated backlink
                    to_door = to_room.path_to_root[0]  # First step in path to root
                else:
                    # Fallback: search through to_room's door_rooms to find the return connection
                    to_door = None
                    for potential_to_door in range(6):
                        if to_room.door_rooms[potential_to_door] == from_room:
                            to_door = potential_to_door
                            break
                    
                    if to_door is None:
                        raise RuntimeError(f"FATAL: Could not find bidirectional connection from Room {to_abs_id} back to Room {from_abs_id}.")

                # Add the connection
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
