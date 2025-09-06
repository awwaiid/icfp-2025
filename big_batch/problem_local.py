"""
Local Problem implementation using the mock server for testing
"""

import json
from typing import List, Dict, Any
from .room import Room
from .api_client_local import LocalApiClient
from .room_manager import RoomManager
from .exploration_strategy import ExplorationStrategy
from .solution_generator import SolutionGenerator


class LocalProblem:
    """Coordinating class for the room exploration problem using local mock server"""

    def __init__(self, room_count: int):
        self.room_count = room_count

        # Initialize components
        self.observations = []  # Raw API observations
        self.explored_paths = set()  # Track paths we've already explored

        # Use local API client and register automatically
        self.api_client = LocalApiClient()
        self.api_client.register()

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
        starting_room = self.room_manager.find_or_create_room_for_path(
            [], starting_label
        )
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
        print("=== Bootstrapping Big-Batch (Local) ===")

        # Select problem
        self.select_problem(problem_name)

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
        print(
            f"\n=== Room Fingerprints ({len(self.room_manager.get_all_rooms())} rooms) ==="
        )

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

    def explore_all_pending_batched(self):
        """NEW: Get ALL pending explorations and send them in one big batch"""
        pending_paths = self.exploration_strategy.get_all_pending_explorations()

        if not pending_paths:
            print("No pending explorations!")
            return False

        print(
            f"BATCH: Found {len(pending_paths)} pending explorations to send in one batch"
        )
        for i, path in enumerate(pending_paths[:10]):  # Show first 10 for brevity
            print(f"  {i + 1}: {path}")
        if len(pending_paths) > 10:
            print(f"  ... and {len(pending_paths) - 10} more")

        # Send all at once
        self.explore(pending_paths)

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

        return True

    def explore_until_complete_batched(self, max_iterations: int = 10000):
        """Keep exploring using big batches until all rooms are complete"""
        print("=== Big-Batch Exploring Until Complete (Local) ===")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Big-Batch Iteration {iteration} ---")

            # Check if we have any work remaining
            incomplete_rooms = self.room_manager.get_incomplete_rooms()
            unknown_connections = (
                self.exploration_strategy.get_unknown_connections_to_verify()
            )
            missing_connections = (
                self.exploration_strategy.get_missing_connections_from_complete_rooms()
            )
            partial_explorations = (
                self.exploration_strategy.get_partial_rooms_to_explore()
            )

            total_work = (
                len(incomplete_rooms)
                + len(unknown_connections)
                + len(missing_connections)
                + len(partial_explorations)
            )

            if total_work == 0:
                print("🎉 All rooms complete and all connections verified!")
                break

            print(
                f"Work remaining: {len(incomplete_rooms)} incomplete rooms, {len(unknown_connections)} unknown connections, {len(missing_connections)} missing connections, {len(partial_explorations)} partial explorations"
            )

            # Try to do all pending explorations in one big batch
            had_work = self.explore_all_pending_batched()

            if not had_work:
                print("No more work to do!")
                break

            # Show current progress
            self.print_fingerprints()

        if iteration >= max_iterations:
            print(f"⚠️  Reached maximum iterations ({max_iterations})")

        print(f"\nCompleted after {iteration} iterations")
        return iteration

    def generate_solution(self, filename: str = "solution.json"):
        """Generate the solution in the JSON format expected by the guess endpoint"""
        return self.solution_generator.generate_solution(filename)

    def submit_solution(self) -> bool:
        """Submit the generated solution and return whether it was correct"""
        print("=== Submitting Solution ===")

        # Generate the solution
        solution_data = self.solution_generator.generate_solution_data()

        # Submit to the mock server
        correct = self.api_client.guess(solution_data)

        if correct:
            print("🎉 Solution was CORRECT!")
        else:
            print("❌ Solution was INCORRECT!")

        return correct

    def debug(self):
        """Print debug information"""
        debug_info = self.api_client.debug()
        print(f"\n=== Debug Information ===")
        print(json.dumps(debug_info, indent=2))
