"""
Connection-based problem solver
"""

import json
import requests
from typing import List, Optional, Tuple
from .connection_data import ConnectionTable, Connection


class ConnectionProblem:
    """Problem solver focused on building a table of room-door connections"""

    def __init__(
        self,
        room_count: int,
        user_id: str = "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A",
    ):
        self.room_count = room_count
        self.user_id = user_id
        self.base_url = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"

        self.table = ConnectionTable(room_count)
        self.starting_room_id = 0  # Always start in room 0
        self.starting_room_label = None  # Will be discovered

        self.observations = []  # Store raw API results

    def select_problem(self, problem_name: str):
        """Select a problem using the API"""
        print(f"Selecting problem {problem_name}")

        data = {"id": self.user_id, "problemName": problem_name}
        response = requests.post(
            f"{self.base_url}/select",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def explore_from_room(
        self, room_id: int, room_label: int
    ) -> List[Tuple[int, List[int]]]:
        """Explore all doors from a specific room"""
        print(f"Exploring all doors from Room {room_id} (label {room_label})")

        # Create plans for all 6 doors from this room
        plans = [[door] for door in range(6)]

        # Convert to API format
        plan_strings = [str(door) for door in range(6)]
        print(f"Exploring doors: {', '.join(plan_strings)}")

        data = {"id": self.user_id, "plans": plan_strings}
        response = requests.post(
            f"{self.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        results = []
        if response.status_code == 200:
            try:
                result = response.json()
                if "results" in result:
                    for door, rooms_result in enumerate(result["results"]):
                        self.observations.append(
                            {
                                "from_room_id": room_id,
                                "from_room_label": room_label,
                                "door": door,
                                "path": [door],
                                "rooms": rooms_result,
                            }
                        )
                        results.append((door, rooms_result))
                        print(f"  Door {door}: {rooms_result}")
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return results

    def process_exploration_results(
        self,
        from_room_id: int,
        from_room_label: int,
        results: List[Tuple[int, List[int]]],
    ):
        """Process results from exploring all doors of a room"""

        for door, rooms_result in results:
            if len(rooms_result) >= 2:  # Should be [from_room_label, to_room_label]
                to_room_label = rooms_result[1]  # Second room in the path

                # Try to find existing room with this label to connect to
                to_room_id = self._find_or_create_room_with_label(to_room_label)

                # Add connection (we don't know the to_door yet)
                connection = self.table.add_connection(
                    from_room_id=from_room_id,
                    from_room_label=from_room_label,
                    from_door=door,
                    to_room_id=to_room_id,
                    to_room_label=to_room_label,
                    to_door=None,  # Unknown for now
                    confirmed=True,  # We directly traversed this
                )

                print(f"  Added: {connection}")

    def _find_or_create_room_with_label(self, label: int) -> int:
        """Find existing room with given label, or create new one"""
        # Look for existing room with this label
        for connection in self.table.connections:
            if connection.from_room_label == label:
                return connection.from_room_id
            if connection.to_room_label == label and connection.to_room_id is not None:
                return connection.to_room_id

        # Create new room
        return self.table.get_next_room_id()

    def bootstrap(self, problem_name: str):
        """Bootstrap the exploration by starting from room 0"""
        print("=== Bootstrapping Connection Exploration ===")

        # Select the problem
        # self.select_problem(problem_name)

        # Explore from starting position to discover starting room label
        print("Discovering starting room...")
        initial_results = self.explore_from_room(0, 0)  # Assume label 0 initially

        if initial_results:
            # The first result tells us our actual starting room label
            first_result = initial_results[0][1]  # rooms_result from door 0
            if first_result:
                actual_starting_label = first_result[0]  # First room in path
                self.starting_room_label = actual_starting_label
                print(f"Starting room label discovered: {actual_starting_label}")

                # Re-process results with correct starting label
                self.process_exploration_results(
                    from_room_id=self.starting_room_id,
                    from_room_label=self.starting_room_label,
                    results=initial_results,
                )

    def explore_breadth_first(self, max_iterations: int = 10):
        """Explore rooms breadth-first, focusing on rooms with incomplete connections"""
        print(f"\n=== Breadth-First Exploration (max {max_iterations} iterations) ===")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}:")

            # Find rooms that need more exploration
            rooms_to_explore = self._find_rooms_needing_exploration()
            
            # If no rooms need basic exploration, check for reverse mapping opportunities
            if not rooms_to_explore:
                rooms_to_explore = self._find_rooms_for_reverse_mapping()
                if rooms_to_explore:
                    print("No rooms need basic exploration, but found rooms for reverse mapping")
                else:
                    incomplete = self.table.get_incomplete_connections()
                    if incomplete:
                        print(f"All rooms explored, but {len(incomplete)} connections still incomplete.")
                        print("This is expected - we can't determine to_door without more complex exploration.")
                        break
                    else:
                        print("All connections complete!")
                        break

            # Explore the first room that needs it
            room_id, room_label = rooms_to_explore[0]
            print(f"Exploring Room {room_id} (label {room_label})...")

            results = self.explore_from_room(room_id, room_label)
            self.process_exploration_results(room_id, room_label, results)

            # Show current state
            self.print_progress()

    def _find_rooms_needing_exploration(self) -> List[Tuple[int, int]]:
        """Find rooms that have incomplete door connections"""
        rooms_needing_exploration = []

        # Get all unique rooms we know about
        known_rooms = set()
        for conn in self.table.connections:
            known_rooms.add((conn.from_room_id, conn.from_room_label))
            if conn.to_room_id is not None and conn.to_room_label is not None:
                known_rooms.add((conn.to_room_id, conn.to_room_label))

        print(f"  DEBUG: Found {len(known_rooms)} known rooms: {sorted(known_rooms)}")

        # Check which rooms have incomplete door mappings
        for room_id, room_label in known_rooms:
            connections_from_room = self.table.get_room_connections(room_id)

            # Check if we have all 6 doors mapped from this room
            mapped_doors = set(conn.from_door for conn in connections_from_room)

            print(f"  DEBUG: Room {room_id}(L{room_label}) has {len(mapped_doors)}/6 doors mapped: {sorted(mapped_doors)}")

            if len(mapped_doors) < 6:
                rooms_needing_exploration.append((room_id, room_label))

        print(f"  DEBUG: {len(rooms_needing_exploration)} rooms need exploration: {rooms_needing_exploration}")
        return rooms_needing_exploration

    def _find_rooms_for_reverse_mapping(self) -> List[Tuple[int, int]]:
        """Find rooms that we haven't explored from yet, but know exist as destinations"""
        rooms_for_reverse_mapping = []

        # Get all unique rooms we know about  
        all_known_rooms = set()
        explored_from_rooms = set()  # Rooms we've explored FROM

        for conn in self.table.connections:
            all_known_rooms.add((conn.from_room_id, conn.from_room_label))
            explored_from_rooms.add((conn.from_room_id, conn.from_room_label))
            
            if conn.to_room_id is not None and conn.to_room_label is not None:
                all_known_rooms.add((conn.to_room_id, conn.to_room_label))

        # Find rooms we know about but haven't explored from
        unexplored_rooms = all_known_rooms - explored_from_rooms
        
        return list(unexplored_rooms)

    def analyze_connections(self):
        """Analyze the connection table for patterns and merges"""
        print("\n=== Connection Analysis ===")

        mergeable = self.table.find_mergeable_connections()
        if mergeable:
            print(f"Found {len(mergeable)} pairs of potentially mergeable connections:")
            for conn1, conn2 in mergeable[:5]:  # Show first 5
                print(f"  {conn1}")
                print(f"  {conn2}")
                print()
        else:
            print("No mergeable connections found yet.")

        incomplete = self.table.get_incomplete_connections()
        if incomplete:
            print(f"\n{len(incomplete)} incomplete connections:")
            for conn in incomplete[:10]:  # Show first 10
                print(f"  {conn}")

    def print_progress(self):
        """Print current exploration progress"""
        stats = self.table.get_stats()
        completion = (stats["confirmed_connections"] / stats["max_possible"]) * 100

        print(
            f"\nProgress: {stats['confirmed_connections']}/{stats['max_possible']} "
            f"connections confirmed ({completion:.1f}%)"
        )
        print(f"Unique rooms discovered: {stats['unique_rooms']}")

    def print_full_state(self):
        """Print complete connection table"""
        self.table.print_by_room()
        print()
        self.analyze_connections()

    def debug_exploration_state(self):
        """Debug current exploration state"""
        print("\n=== Debug Exploration State ===")
        
        # Show all rooms and their door completion
        known_rooms = set()
        for conn in self.table.connections:
            known_rooms.add((conn.from_room_id, conn.from_room_label))
            if conn.to_room_id is not None and conn.to_room_label is not None:
                known_rooms.add((conn.to_room_id, conn.to_room_label))
        
        print(f"All known rooms ({len(known_rooms)}):")
        for room_id, room_label in sorted(known_rooms):
            connections_from_room = self.table.get_room_connections(room_id)
            mapped_doors = set(conn.from_door for conn in connections_from_room)
            status = "COMPLETE" if len(mapped_doors) == 6 else f"INCOMPLETE ({len(mapped_doors)}/6)"
            print(f"  Room {room_id}(L{room_label}): {status} - doors {sorted(mapped_doors)}")
        
        incomplete = self.table.get_incomplete_connections()
        print(f"\nIncomplete connections ({len(incomplete)}):")
        for conn in incomplete[:10]:
            print(f"  {conn}")
        
        # Show what rooms need exploration
        rooms_to_explore = self._find_rooms_needing_exploration()
        print(f"\nResult: {len(rooms_to_explore)} rooms need exploration")
        
        # Show rooms that could help complete connections
        rooms_for_reverse_mapping = self._find_rooms_for_reverse_mapping()
        print(f"Rooms that could help complete connections: {len(rooms_for_reverse_mapping)}")
        for room_id, room_label in rooms_for_reverse_mapping[:5]:
            print(f"  Room {room_id}(L{room_label})")

    def save_observations(self, filename: str):
        """Save raw observations to file"""
        data = {
            "observations": self.observations,
            "starting_room_id": self.starting_room_id,
            "starting_room_label": self.starting_room_label,
            "room_count": self.room_count,
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved observations to {filename}")

    def load_observations(self, filename: str):
        """Load observations from file and rebuild connection table"""
        with open(filename, "r") as f:
            data = json.load(f)

        self.observations = data["observations"]
        self.starting_room_id = data["starting_room_id"]
        self.starting_room_label = data["starting_room_label"]

        # Rebuild connection table
        self.table = ConnectionTable(self.room_count)

        for obs in self.observations:
            results = [(obs["door"], obs["rooms"])]
            self.process_exploration_results(
                obs["from_room_id"], obs["from_room_label"], results
            )

        print(f"Loaded {len(self.observations)} observations from {filename}")
