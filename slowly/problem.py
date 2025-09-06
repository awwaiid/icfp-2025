"""
Refactored Problem implementation using modular components
"""

import json
from typing import List, Dict, Any
from .room import Room
from .api_client import ApiClient
from .room_manager import RoomManager
from .exploration_strategy import ExplorationStrategy
from .solution_generator import SolutionGenerator


class Problem:
    """Coordinating class for the room exploration problem"""

    def __init__(
        self,
        room_count: int,
        user_id: str = "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A",
    ):
        self.room_count = room_count
        self.user_id = user_id
        
        # Initialize components
        self.observations = []  # Raw API observations
        self.explored_paths = set()  # Track paths we've already explored
        
        self.api_client = ApiClient(user_id)
        self.room_manager = RoomManager(room_count, self.observations)
        self.exploration_strategy = ExplorationStrategy(
            self.room_manager, self.observations, self.explored_paths
        )
        self.solution_generator = SolutionGenerator(self.room_manager)

    def select_problem(self, problem_name: str):
        """Select a problem using the API"""
        return self.api_client.select_problem(problem_name)

    def explore(self, plans: List[List[int]]):
        """Explore with given plans and process results"""
        # Filter out paths based on whether they're worth exploring
        new_plans = []
        for plan in plans:
            if self.exploration_strategy.should_explore_path(plan):
                new_plans.append(plan)
                # Mark as explored after we decide to explore it
                plan_tuple = tuple(plan)
                self.explored_paths.add(plan_tuple)
            else:
                print(f"Skipping path: {plan} (destination already complete)")

        if not new_plans:
            print("All provided paths lead to already complete destinations!")
            return None

        # Use API client to explore
        result = self.api_client.explore(new_plans)
        
        if result and "results" in result:
            # Process each result
            for plan, rooms_result in zip(result["plans"], result["results"]):
                self.observations.append({"plan": plan, "rooms": rooms_result})
                self.process_observation(plan, rooms_result)
        
        return result.get("response") if result else None

    def process_observation(self, path: List[int], rooms: List[int]):
        """Process a single observation to update room knowledge"""
        print(f"Processing: path={path}, rooms={rooms}")

        if not rooms:
            return

        # The first room in the sequence is where we start
        starting_label = rooms[0]

        # Find or create room for starting position
        print(f"  Looking for starting room with path=[] and label={starting_label}")
        starting_room = self.room_manager.find_or_create_room_for_path([], starting_label)
        print(f"  Using starting room: {starting_room}")

        # Process each step in the path
        current_room = starting_room
        for i, door in enumerate(path):
            if i + 1 < len(rooms):
                destination_label = rooms[i + 1]

                # Record that this door leads to a room with this label
                print(
                    f"  Room {current_room.label} door {door} -> label {destination_label}"
                )
                current_room.set_door_label(door, destination_label)

                # Find or create the destination room
                path_to_destination = path[: i + 1]
                print(
                    f"  Looking for destination room with path={path_to_destination} and label={destination_label}"
                )
                destination_room = self.room_manager.find_or_create_room_for_path(
                    path_to_destination, destination_label
                )
                print(f"  Using destination room: {destination_room}")

                current_room = destination_room

    def populate_explored_paths_from_observations(self):
        """Populate explored paths from existing observations"""
        self.explored_paths.clear()
        for obs in self.observations:
            path_tuple = tuple(obs["plan"])
            self.explored_paths.add(path_tuple)
        print(f"Populated {len(self.explored_paths)} explored paths from observations")

    def bootstrap(self, problem_name: str):
        """Bootstrap by discovering the starting room"""
        print("=== Bootstrapping Slowly ===")

        # Select problem (uncomment if needed)
        # self.select_problem(problem_name)

        # Explore all doors from starting position
        plans = [[door] for door in range(6)]
        self.explore(plans)

        # Remove any duplicates discovered during bootstrap
        removed = self.room_manager.remove_duplicate_rooms()
        if removed > 0:
            print(f"Removed {removed} duplicate rooms after bootstrap")

        print("Bootstrap complete!")
        self.print_fingerprints()

    def print_fingerprints(self):
        """Print all discovered room fingerprints with absolute-identity info"""
        print(f"\n=== Room Fingerprints ({len(self.room_manager.get_all_rooms())} rooms) ===")

        fingerprint_to_absolute_id = self.room_manager.get_absolute_room_mapping()

        for i, room in enumerate(self.room_manager.get_all_rooms()):
            completeness = (
                "COMPLETE"
                if room.is_complete()
                else f"PARTIAL ({len(room.get_known_doors())}/6)"
            )

            # Add absolute-identity information
            if room.is_complete():
                fingerprint = room.get_fingerprint()
                absolute_id = fingerprint_to_absolute_id.get(fingerprint, "?")
                absolute_connections = self.room_manager.get_absolute_connections(room)
                absolute_connections_str = (
                    "["
                    + ", ".join(
                        str(conn) if conn is not None else "?"
                        for conn in absolute_connections
                    )
                    + "]"
                )

                # Count how many connections are verified vs unknown
                verified_count = sum(
                    1 for conn in absolute_connections if conn is not None
                )
                unknown_count = sum(1 for conn in absolute_connections if conn is None)

                connection_status = (
                    f"({verified_count} verified, {unknown_count} unknown)"
                )

                print(
                    f"Room {i}: {fingerprint} [{completeness}] | "
                    f"Absolute ID: {absolute_id} | Connections: {absolute_connections_str} {connection_status}"
                )
            # Skip printing partial rooms

        if not self.room_manager.get_all_rooms():
            print("No rooms discovered yet.")

    def get_incomplete_rooms(self) -> List[Room]:
        """Get rooms that don't have complete door information"""
        return self.room_manager.get_incomplete_rooms()

    def explore_incomplete_rooms(self):
        """Explore from rooms that have incomplete door information, prioritizing complete room connections"""
        exploration_batch = self.exploration_strategy.get_next_exploration_batch()
        
        if not exploration_batch:
            print("All rooms are complete!")
            return
        
        batch_type = exploration_batch["type"]
        data = exploration_batch["data"]
        priority = exploration_batch["priority"]
        
        if batch_type == "unknown_connections":
            connection = data
            if connection["priority"] == "complete_blocking_partial_room_batch":
                from_room = connection["from_room"]
                door = connection["door"]
                blocking_room = connection["blocking_room"]
                paths = connection["paths"]
                reason = connection["reason"]

                print(f"BLOCKING: {reason}")
                print(
                    f"  Completing partial room {blocking_room.get_fingerprint()} by exploring {len(paths)} doors in batch: {paths}"
                )

                self.explore(paths)
            else:
                print(f"VERIFY: Exploring {connection['priority']} connection")
                print(f"  Path: {connection['path']}")
                self.explore([connection["path"]])
                
        elif batch_type == "missing_connections":
            connection = data
            from_room = connection["from_room"]
            door = connection["door"]
            target_label = connection["target_label"]
            path = connection["path"]

            print(
                f"PRIORITY: Exploring door {door} from complete room {from_room.label} -> label {target_label}"
            )
            print(f"  Path: {path}")

            self.explore([path])
            
        elif batch_type == "partial_explorations":
            exploration = data
            from_room = exploration["from_room"]
            door = exploration["door"]
            path = exploration["path"]

            print(
                f"PARTIAL: Exploring door {door} from partial room {from_room.label} (path {from_room.paths[0]})"
            )
            print(f"  Full path: {path}")

            self.explore([path])
            
        elif batch_type == "incomplete_rooms":
            room_data = data
            room = room_data["room"]
            doors = room_data["doors"]
            plans = room_data["plans"]

            print(
                f"FALLBACK: Exploring doors {doors} from incomplete room {room.label} (had {len(room.get_unknown_doors())} unknown)"
            )
            print(f"  Base path: {room.paths[0]}")

            self.explore(plans)

        # After exploration, check for and remove duplicates
        removed = self.room_manager.remove_duplicate_rooms()
        if removed > 0:
            print("Updated room list after removing duplicates:")
            self.print_fingerprints()

        # Check if we can do aggressive cleanup now that we might have complete coverage
        cleaned = self.room_manager.cleanup_all_partial_rooms_when_complete()
        if cleaned > 0:
            print("Final clean room list:")
            self.print_fingerprints()

    def explore_until_complete(self, max_iterations: int = 10000):
        """Keep exploring incomplete rooms until all are complete or max iterations reached"""
        print("=== Exploring Until Complete ===")
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Check if we have any incomplete rooms or unknown connections
            incomplete_rooms = self.room_manager.get_incomplete_rooms()
            
            # Also check for unknown connections in complete rooms
            unknown_connections = self.exploration_strategy.get_unknown_connections_to_verify()
            missing_connections = self.exploration_strategy.get_missing_connections_from_complete_rooms()
            partial_explorations = self.exploration_strategy.get_partial_rooms_to_explore()
            
            total_work = len(incomplete_rooms) + len(unknown_connections) + len(missing_connections) + len(partial_explorations)
            
            if total_work == 0:
                print("🎉 All rooms complete and all connections verified!")
                break
                
            print(f"Work remaining: {len(incomplete_rooms)} incomplete rooms, {len(unknown_connections)} unknown connections, {len(missing_connections)} missing connections, {len(partial_explorations)} partial explorations")
            
            # Do one round of exploration
            self.explore_incomplete_rooms()
            
            # Show current progress
            self.print_fingerprints()
        
        if iteration >= max_iterations:
            print(f"⚠️  Reached maximum iterations ({max_iterations})")
        
        print(f"\nCompleted after {iteration} iterations")
        return iteration

    def save_observations(self, filename: str):
        """Save observations to file"""
        data = {"observations": self.observations, "room_count": self.room_count}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(self.observations)} observations to {filename}")

    def load_observations(self, filename: str):
        """Load observations from file"""
        with open(filename, "r") as f:
            data = json.load(f)

        self.observations = data["observations"]
        
        # Reset room manager with new observations
        self.room_manager = RoomManager(self.room_count, self.observations)
        
        # Update strategy with new room manager
        self.exploration_strategy = ExplorationStrategy(
            self.room_manager, self.observations, self.explored_paths
        )
        
        # Update solution generator
        self.solution_generator = SolutionGenerator(self.room_manager)

        # Replay observations
        for obs in self.observations:
            self.process_observation(obs["plan"], obs["rooms"])

        # Populate explored paths from the loaded observations
        self.populate_explored_paths_from_observations()

        print(f"Loaded {len(self.observations)} observations from {filename}")
        self.print_fingerprints()

    def generate_solution(self, filename: str = "solution.json"):
        """Generate the solution in the JSON format expected by bin/guess"""
        return self.solution_generator.generate_solution(filename)

    # Convenience methods that delegate to components
    def print_analysis(self):
        """Print analysis of room fingerprints and potential duplicates"""
        print(f"\n=== Room Analysis ===")

        complete_rooms = self.room_manager.get_complete_rooms()
        incomplete_rooms = self.room_manager.get_incomplete_rooms()

        print(f"Complete rooms: {len(complete_rooms)}")
        print(f"Incomplete rooms: {len(incomplete_rooms)}")

        # Check for identical fingerprints
        identical = self.room_manager.find_identical_fingerprints()
        if identical:
            print(
                f"\n🔍 Found {len(identical)} sets of rooms with identical fingerprints:"
            )
            for fp, rooms in identical.items():
                print(f"  Fingerprint '{fp}':")
                for room_idx, room in rooms:
                    paths_str = ", ".join([str(p) for p in room.paths])
                    print(f"    Room {room_idx}: paths=[{paths_str}]")
                print(
                    f"    → These {len(rooms)} rooms are likely the same physical room!"
                )
        else:
            print("\n✅ No identical fingerprints found - all rooms appear unique")

    def debug_absolute_connections(self):
        """Debug absolute connection mapping"""
        print("\n=== Debug Absolute Connections ===")

        fingerprint_to_absolute_id = self.room_manager.get_absolute_room_mapping()

        print("Fingerprint to Absolute ID mapping:")
        for fp, abs_id in sorted(fingerprint_to_absolute_id.items()):
            print(f"  {fp} -> Absolute ID {abs_id}")

        print("\nChecking connections for each room:")
        complete_rooms = self.room_manager.get_complete_rooms()

        for i, room in enumerate(complete_rooms):
            print(f"\nRoom {i}: {room.get_fingerprint()}")
            print(f"  Door labels: {room.door_labels}")

            for door, door_label in enumerate(room.door_labels):
                print(f"  Door {door} -> label {door_label}:")

                # Find complete rooms with this label
                complete_rooms_with_label = [
                    other_room
                    for other_room in self.room_manager.get_all_rooms()
                    if other_room.is_complete() and other_room.label == door_label
                ]

                print(
                    f"    Found {len(complete_rooms_with_label)} complete rooms with label {door_label}"
                )
                for other_room in complete_rooms_with_label:
                    other_fp = other_room.get_fingerprint()
                    other_abs_id = fingerprint_to_absolute_id.get(other_fp, "?")
                    print(f"      {other_fp} -> Absolute ID {other_abs_id}")

    def print_progress(self):
        """Print current exploration progress"""
        stats = self.room_manager.get_stats()
        completion = (stats["verified_connections"] / stats["max_possible"]) * 100

        print(
            f"\nProgress: {stats['verified_connections']}/{stats['max_possible']} "
            f"connections confirmed ({completion:.1f}%)"
        )
        print(f"Unique rooms discovered: {stats['unique_rooms']}")

    def print_full_state(self):
        """Print complete connection table"""
        self.print_fingerprints()
        print()
        self.print_analysis()

    def debug_exploration_state(self):
        """Debug current exploration state"""
        print("\n=== Debug Exploration State ===")

        # Show all rooms and their door completion
        all_rooms = self.room_manager.get_all_rooms()
        known_rooms = set()
        
        for room in all_rooms:
            if room.is_complete():
                fingerprint = room.get_fingerprint()
                absolute_id = self.room_manager.get_absolute_room_mapping().get(fingerprint, "?")
                known_rooms.add((absolute_id, room.label))

        print(f"All known complete rooms ({len(known_rooms)}):")
        for abs_id, room_label in sorted(known_rooms):
            # Find the room with this absolute ID
            for room in all_rooms:
                if room.is_complete():
                    fp = room.get_fingerprint()
                    if self.room_manager.get_absolute_room_mapping().get(fp) == abs_id:
                        connections = self.room_manager.get_absolute_connections(room)
                        verified_count = sum(1 for conn in connections if conn is not None)
                        status = "COMPLETE" if verified_count == 6 else f"INCOMPLETE ({verified_count}/6)"
                        print(f"  Room {abs_id}(L{room_label}): {status}")
                        break

        incomplete_rooms = self.room_manager.get_incomplete_rooms()
        print(f"\nIncomplete rooms ({len(incomplete_rooms)}): (fingerprints not shown)")

        # Show what exploration options we have
        exploration_batch = self.exploration_strategy.get_next_exploration_batch()
        if exploration_batch:
            print(f"\nNext exploration: {exploration_batch['type']} (priority {exploration_batch['priority']})")
        else:
            print("\nNo more exploration needed!")