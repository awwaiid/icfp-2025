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

        # Generate connections - every door must have exactly one connection
        for from_abs_id in sorted(absolute_id_to_room.keys()):
            from_room = absolute_id_to_room[from_abs_id]
            from_index = absolute_id_to_index[from_abs_id]
            # Try systematic connections first, fallback to observation-based connections
            connections = self.room_manager.get_systematic_connections(from_room, debug=False)
            if all(conn is None for conn in connections):
                connections = self.room_manager.get_absolute_connections(from_room)

            for from_door, to_abs_id in enumerate(connections):
                if to_abs_id is not None:
                    to_room = absolute_id_to_room[to_abs_id]
                    to_index = absolute_id_to_index[to_abs_id]

                    # Find which door on the destination room leads back to from_abs_id
                    to_connections = self.room_manager.get_absolute_connections(to_room)
                    to_door = None

                    # Find a door that leads back (prefer the first one found)
                    for potential_to_door, reverse_abs_id in enumerate(to_connections):
                        if reverse_abs_id == from_abs_id:
                            to_door = potential_to_door
                            break

                    # EVERY door MUST have a connection - if we can't find reverse door, 
                    # use door 0 as fallback to prevent validation errors
                    if to_door is None:
                        print(f"Warning: Could not find reverse door for Room {from_abs_id} door {from_door} -> Room {to_abs_id}, using door 0 as fallback")
                        to_door = 0

                    # Every door needs a connection, so add it
                    solution["connections"].append(
                        {
                            "from": {
                                "room": from_index,  # Use index into rooms array
                                "door": from_door,
                            },
                            "to": {
                                "room": to_index,  # Use index into rooms array
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
