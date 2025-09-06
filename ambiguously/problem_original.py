"""
Minimal Problem implementation with fingerprint-based room tracking
"""

import json
import requests
from typing import List, Optional
from .room import Room


class Problem:
    """Simple problem solver using room fingerprints"""

    def __init__(
        self,
        room_count: int,
        user_id: str = "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A",
    ):
        self.room_count = room_count
        self.user_id = user_id
        self.base_url = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"

        self.possible_rooms = []  # List of discovered room possibilities
        self.observations = []  # Raw API observations
        self.explored_paths = set()  # Track paths we've already explored

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

    def should_explore_path(self, plan: List[int]) -> bool:
        """Determine if we should explore this path"""
        plan_tuple = tuple(plan)

        # Always explore if we've never been there
        if plan_tuple not in self.explored_paths:
            return True

        # Don't re-explore paths we've already been on
        print(f"Skipping already explored path: {plan}")
        return False

    def explore(self, plans: List[List[int]]):
        """Explore with given plans and process results"""
        # Filter out paths based on whether they're worth exploring
        new_plans = []
        for plan in plans:
            if self.should_explore_path(plan):
                new_plans.append(plan)
                # Mark as explored after we decide to explore it
                plan_tuple = tuple(plan)
                self.explored_paths.add(plan_tuple)
            else:
                print(f"Skipping path: {plan} (destination already complete)")

        if not new_plans:
            print("All provided paths lead to already complete destinations!")
            return None

        # Convert plans to API format
        plan_strings = ["".join(str(door) for door in plan) for plan in new_plans]
        print(f"Exploring with plans: {plan_strings}")

        data = {"id": self.user_id, "plans": plan_strings}
        response = requests.post(
            f"{self.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        # Process results
        if response.status_code == 200:
            try:
                result = response.json()
                if "results" in result:
                    for plan, rooms_result in zip(new_plans, result["results"]):
                        self.observations.append({"plan": plan, "rooms": rooms_result})
                        self.process_observation(plan, rooms_result)
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return response

    def process_observation(self, path: List[int], rooms: List[int]):
        """Process a single observation to update room knowledge"""
        print(f"Processing: path={path}, rooms={rooms}")

        if not rooms:
            return

        # The first room in the sequence is where we start
        starting_label = rooms[0]

        # Find or create room for starting position
        print(f"  Looking for starting room with path=[] and label={starting_label}")
        starting_room = self.find_or_create_room_for_path([], starting_label)
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
                destination_room = self.find_or_create_room_for_path(
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

    def find_or_create_room_for_path(self, path: List[int], label: int) -> Room:
        """Find existing room matching path and label, or create new one"""
        # Look for existing room with this exact path and label
        for room in self.possible_rooms:
            if path in room.paths and room.label == label:
                return room

        # If no exact match, create new room
        # (We can't assume same label = same room since labels can be reused)
        new_room = Room(label)
        new_room.add_path(path)
        self.possible_rooms.append(new_room)
        return new_room

    def bootstrap(self, problem_name: str):
        """Bootstrap by discovering the starting room"""
        print("=== Bootstrapping Ambiguously ===")

        # Select problem
        # self.select_problem(problem_name)

        # Explore all doors from starting position
        plans = [[door] for door in range(6)]
        self.explore(plans)

        # Remove any duplicates discovered during bootstrap
        removed = self.remove_duplicate_rooms()
        if removed > 0:
            print(f"Removed {removed} duplicate rooms after bootstrap")

        print("Bootstrap complete!")
        self.print_fingerprints()

    def print_fingerprints(self):
        """Print all discovered room fingerprints with absolute-identity info"""
        print(f"\n=== Room Fingerprints ({len(self.possible_rooms)} rooms) ===")

        fingerprint_to_absolute_id = self.get_absolute_room_mapping()

        for i, room in enumerate(self.possible_rooms):
            completeness = (
                "COMPLETE"
                if room.is_complete()
                else f"PARTIAL ({len(room.get_known_doors())}/6)"
            )

            # Add absolute-identity information
            if room.is_complete():
                fingerprint = room.get_fingerprint()
                absolute_id = fingerprint_to_absolute_id.get(fingerprint, "?")
                absolute_connections = self.get_absolute_connections(room)
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

        if not self.possible_rooms:
            print("No rooms discovered yet.")

    def get_incomplete_rooms(self) -> List[Room]:
        """Get rooms that don't have complete door information"""
        return [room for room in self.possible_rooms if not room.is_complete()]

    def find_identical_fingerprints(self):
        """Find rooms with identical fingerprints (likely the same room)"""
        fingerprint_groups = {}

        # Group rooms by fingerprint
        for i, room in enumerate(self.possible_rooms):
            if room.is_complete():  # Only compare complete fingerprints
                fp = room.get_fingerprint()
                if fp not in fingerprint_groups:
                    fingerprint_groups[fp] = []
                fingerprint_groups[fp].append((i, room))

        # Find groups with multiple rooms (identical fingerprints)
        identical_groups = {}
        for fp, rooms in fingerprint_groups.items():
            if len(rooms) > 1:
                identical_groups[fp] = rooms

        return identical_groups

    def get_absolute_room_mapping(self):
        """Create mapping from fingerprints to absolute room IDs"""
        fingerprint_to_absolute_id = {}
        absolute_id_counter = 0

        # Group all rooms by complete fingerprints
        fingerprint_groups = {}
        for room in self.possible_rooms:
            if room.is_complete():
                fp = room.get_fingerprint()
                if fp not in fingerprint_groups:
                    fingerprint_groups[fp] = []
                fingerprint_groups[fp].append(room)

        # Assign absolute IDs to each unique fingerprint
        for fp in sorted(fingerprint_groups.keys()):
            fingerprint_to_absolute_id[fp] = absolute_id_counter
            absolute_id_counter += 1

        return fingerprint_to_absolute_id

    def get_door_destination_fingerprint(self, from_room, door):
        """Determine which specific complete room fingerprint this door leads to"""
        # We need to look at our exploration data to see where this door actually goes
        # from this specific room

        for obs in self.observations:
            if len(obs["plan"]) >= 1 and len(obs["rooms"]) >= 2:
                # Check if this observation shows us going through this door from this room

                # Find if any path to from_room matches the start of this observation
                for from_path in from_room.paths:
                    if len(obs["plan"]) > len(from_path):
                        # Check if observation starts with this path + door
                        if (
                            obs["plan"][: len(from_path)] == from_path
                            and obs["plan"][len(from_path)] == door
                        ):
                            # This observation shows us going through this door!
                            # The destination should be at position len(from_path) + 1 in rooms
                            if len(obs["rooms"]) > len(from_path) + 1:
                                destination_label = obs["rooms"][len(from_path) + 1]
                                destination_path = obs["plan"][: len(from_path) + 1]

                                # Find the complete room that matches this destination
                                for room in self.possible_rooms:
                                    if (
                                        room.is_complete()
                                        and room.label == destination_label
                                        and destination_path in room.paths
                                    ):
                                        return room.get_fingerprint()

        return None

    def get_absolute_connections(self, room, debug=False):
        """Get absolute-identity connections for a room - based on actual exploration paths"""
        if not room.is_complete():
            return [None] * 6

        fingerprint_to_absolute_id = self.get_absolute_room_mapping()
        absolute_connections = []

        if debug:
            print(f"Getting connections for room {room.get_fingerprint()}")
            print(f"Room paths: {room.paths}")

        for door in range(6):
            # Find which specific complete room fingerprint this door leads to
            destination_fingerprint = self.get_door_destination_fingerprint(room, door)

            if debug:
                print(
                    f"  Door {door}: destination fingerprint = {destination_fingerprint}"
                )

            if (
                destination_fingerprint
                and destination_fingerprint in fingerprint_to_absolute_id
            ):
                absolute_connections.append(
                    fingerprint_to_absolute_id[destination_fingerprint]
                )
            else:
                absolute_connections.append(None)

        return absolute_connections

    def remove_duplicate_rooms(self):
        """Remove duplicate rooms with identical complete fingerprints"""
        identical_groups = self.find_identical_fingerprints()

        if not identical_groups:
            return 0  # No duplicates found

        removed_count = 0

        # For each group of identical fingerprints, keep the first one and remove the rest
        for fingerprint, rooms in identical_groups.items():
            # Sort by room index to have consistent behavior
            rooms.sort(key=lambda x: x[0])  # Sort by room index

            # Keep the first room (lowest index), merge paths from others
            keeper_idx, keeper_room = rooms[0]
            rooms_to_remove = []

            print(f"Merging duplicate rooms with fingerprint '{fingerprint}':")
            print(f"  Keeping Room {keeper_idx}")

            # Merge paths from duplicate rooms into the keeper
            for room_idx, room in rooms[1:]:
                print(f"  Removing Room {room_idx} (merging paths)")

                # Add any unique paths from the duplicate to the keeper
                for path in room.paths:
                    if path not in keeper_room.paths:
                        keeper_room.add_path(path)

                rooms_to_remove.append(room)
                removed_count += 1

            # Remove duplicates from the possible_rooms list
            for room_to_remove in rooms_to_remove:
                if room_to_remove in self.possible_rooms:
                    self.possible_rooms.remove(room_to_remove)

        if removed_count > 0:
            print(f"Removed {removed_count} duplicate rooms")

        return removed_count

    def can_trace_path_to_complete_room(self, partial_path, debug=False):
        """Check if a partial path can be traced through complete rooms to find its destination"""
        if not partial_path:
            return None

        if debug:
            print(f"    Tracing path {partial_path}")

        # Start from the beginning (empty path = starting room)
        current_path = []
        current_room = None

        # Find the starting room (path = [])
        for room in self.possible_rooms:
            if room.is_complete() and [] in room.paths:
                current_room = room
                break

        if not current_room:
            if debug:
                print(f"    No starting room found!")
            return None

        if debug:
            print(f"    Starting from room: {current_room.get_fingerprint()}")

        # Follow the partial path through complete rooms
        for step, door in enumerate(partial_path):
            if not current_room.is_complete():
                if debug:
                    print(f"    Step {step}: Hit incomplete room, can't trace further")
                return None  # Hit an incomplete room, can't trace further

            # What label does this door lead to?
            if (
                door >= len(current_room.door_labels)
                or current_room.door_labels[door] is None
            ):
                if debug:
                    print(f"    Step {step}: Door {door} info not available")
                return None  # Door info not available

            target_label = current_room.door_labels[door]
            current_path.append(door)

            if debug:
                print(
                    f"    Step {step}: Door {door} leads to label {target_label}, path so far: {current_path}"
                )

            # Find a complete room with this label - we don't need it to explicitly include this path
            # We just need it to have the right label and be complete
            next_room = None
            complete_candidates = []

            for room in self.possible_rooms:
                if room.is_complete() and room.label == target_label:
                    complete_candidates.append(room)

            if debug:
                print(
                    f"      Found {len(complete_candidates)} complete rooms with label {target_label}"
                )
                for c in complete_candidates:
                    print(f"        {c.get_fingerprint()} paths={c.paths}")

            if len(complete_candidates) == 1:
                # Only one complete room with this label - use it
                next_room = complete_candidates[0]
            elif len(complete_candidates) > 1:
                # Multiple complete rooms with same label - try to pick the best one
                # Prefer one that already includes a prefix of our current path
                for room in complete_candidates:
                    if any(
                        path == current_path[: len(path)]
                        or current_path == path[: len(current_path)]
                        for path in room.paths
                    ):
                        next_room = room
                        break
                if not next_room:
                    # No path overlap, just pick the first one
                    next_room = complete_candidates[0]

            if not next_room:
                if debug:
                    print(
                        f"    Step {step}: No complete room with label {target_label}"
                    )
                    # Show what rooms we do have with this label
                    candidates = [
                        r for r in self.possible_rooms if r.label == target_label
                    ]
                    print(
                        f"      All candidates with label {target_label}: {len(candidates)}"
                    )
                    for c in candidates[:3]:  # Show first 3
                        print(
                            f"        {c.get_fingerprint() if c.is_complete() else 'PARTIAL'} paths={c.paths}"
                        )
                return None  # Can't find the next complete room

            if debug:
                print(f"      Selected room: {next_room.get_fingerprint()}")

            current_room = next_room

        if debug:
            print(f"    Final destination: {current_room.get_fingerprint()}")
        return current_room

    def cleanup_redundant_partial_rooms(self):
        """Remove partial rooms that are redundant with complete rooms"""
        removed_count = 0

        # Find partial rooms that are redundant
        partial_rooms = [room for room in self.possible_rooms if not room.is_complete()]
        rooms_to_remove = []

        print("Checking for redundant partial rooms...")

        for partial_room in partial_rooms:
            # Check if this partial room's path can be traced through complete rooms
            if len(partial_room.paths) == 1:  # Only handle single-path partials for now
                partial_path = partial_room.paths[0]

                print(
                    f"  Checking partial room {partial_room.label} at path {partial_path}"
                )

                # Try to trace this path through complete rooms
                destination_room = self.can_trace_path_to_complete_room(
                    partial_path, debug=True
                )

                if destination_room and destination_room.label == partial_room.label:
                    print(
                        f"  Removing redundant partial room {partial_room.label} at path {partial_path}"
                    )
                    print(
                        f"    -> Path traces to complete room with fingerprint {destination_room.get_fingerprint()}"
                    )
                    print(f"    -> Complete room has paths: {destination_room.paths}")
                    rooms_to_remove.append(partial_room)
                    removed_count += 1
                else:
                    if destination_room:
                        print(
                            f"    -> Path traces to room with label {destination_room.label}, but partial has label {partial_room.label} (mismatch)"
                        )
                    else:
                        print(f"    -> Could not trace path")

        # Remove the redundant partial rooms
        for room_to_remove in rooms_to_remove:
            if room_to_remove in self.possible_rooms:
                self.possible_rooms.remove(room_to_remove)

        if removed_count > 0:
            print(f"Cleaned up {removed_count} redundant partial rooms")

        return removed_count

    def cleanup_all_partial_rooms_when_complete(self):
        """Remove all partial rooms when we have complete room coverage"""
        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]
        partial_rooms = [room for room in self.possible_rooms if not room.is_complete()]

        # Check if we have complete coverage
        if len(complete_rooms) == self.room_count:
            # Check if all complete rooms have verified connections
            all_verified = True
            for room in complete_rooms:
                connections = self.get_absolute_connections(room)
                if any(conn is None for conn in connections):
                    all_verified = False
                    break

            if all_verified:
                print(
                    f"Complete coverage achieved! Removing all {len(partial_rooms)} redundant partial rooms"
                )

                # Remove all partial rooms
                self.possible_rooms = [
                    room for room in self.possible_rooms if room.is_complete()
                ]

                return len(partial_rooms)

        return 0

    def debug_absolute_connections(self):
        """Debug absolute connection mapping"""
        print("\n=== Debug Absolute Connections ===")

        fingerprint_to_absolute_id = self.get_absolute_room_mapping()

        print("Fingerprint to Absolute ID mapping:")
        for fp, abs_id in sorted(fingerprint_to_absolute_id.items()):
            print(f"  {fp} -> Absolute ID {abs_id}")

        print("\nChecking connections for each room:")
        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]

        for i, room in enumerate(complete_rooms):
            if not room.is_complete():
                continue

            print(f"\nRoom {i}: {room.get_fingerprint()}")
            print(f"  Door labels: {room.door_labels}")

            for door, door_label in enumerate(room.door_labels):
                print(f"  Door {door} -> label {door_label}:")

                # Find complete rooms with this label
                complete_rooms_with_label = [
                    other_room
                    for other_room in self.possible_rooms
                    if other_room.is_complete() and other_room.label == door_label
                ]

                print(
                    f"    Found {len(complete_rooms_with_label)} complete rooms with label {door_label}"
                )
                for other_room in complete_rooms_with_label:
                    other_fp = other_room.get_fingerprint()
                    other_abs_id = fingerprint_to_absolute_id.get(other_fp, "?")
                    print(f"      {other_fp} -> Absolute ID {other_abs_id}")

    def print_analysis(self):
        """Print analysis of room fingerprints and potential duplicates"""
        print(f"\n=== Room Analysis ===")

        complete_rooms = [r for r in self.possible_rooms if r.is_complete()]
        incomplete_rooms = self.get_incomplete_rooms()

        print(f"Complete rooms: {len(complete_rooms)}")
        print(f"Incomplete rooms: {len(incomplete_rooms)}")

        # Check for identical fingerprints
        identical = self.find_identical_fingerprints()
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

    def is_destination_already_known_complete(self, from_room, door):
        """Check if exploring this door would lead to a room we already know completely"""
        # We don't know the destination label yet, so we can't pre-filter
        # The better approach is to rely on duplicate removal after exploration
        # and potentially add smarter logic later if we can predict destinations
        return False

    def get_doors_worth_exploring(self, room):
        """Get doors that are worth exploring (lead to unknown destinations)"""
        if not room.paths:
            return []

        unknown_doors = room.get_unknown_doors()
        doors_worth_exploring = []

        for door in unknown_doors:
            # For now, explore all unknown doors - the duplicate removal will handle
            # cases where we discover rooms we already knew about
            # TODO: Could optimize by checking if we can predict the destination
            doors_worth_exploring.append(door)

        return doors_worth_exploring

    def get_missing_connections_from_complete_rooms(self):
        """Find connections from complete rooms to labels we haven't fully explored"""
        missing_connections = []

        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]

        for room in complete_rooms:
            if not room.paths:
                continue

            base_path = room.paths[0]  # Use first path to this room

            # Check each door in this complete room
            for door, target_label in enumerate(room.door_labels):
                if target_label is not None:
                    # Check if we have a complete room with this label
                    complete_targets = [
                        r
                        for r in self.possible_rooms
                        if r.label == target_label and r.is_complete()
                    ]

                    if not complete_targets:
                        # We don't have a complete room with this target label yet
                        # But only suggest this if we haven't already explored this path
                        target_path = base_path + [door]
                        path_tuple = tuple(target_path)

                        if path_tuple not in self.explored_paths:
                            missing_connections.append(
                                {
                                    "from_room": room,
                                    "door": door,
                                    "target_label": target_label,
                                    "path": target_path,
                                    "priority": "complete_to_unknown",
                                }
                            )

        return missing_connections

    def get_unknown_connections_to_verify(self):
        """Find unknown connections in complete rooms that need verification or specific partial rooms that block verification"""
        unknown_connections = []

        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]

        for room in complete_rooms:
            if not room.paths:
                continue

            # Get the absolute connections to see which are unknown
            absolute_connections = self.get_absolute_connections(room)

            # Find doors with unknown connections (None)
            for door, connection in enumerate(absolute_connections):
                if connection is None:
                    base_path = room.paths[0]  # Use first path to this room

                    # Check if we have an observation for this door that shows the destination
                    destination_info = self.get_door_destination_info(room, door)

                    if destination_info:
                        # We have an observation, check if destination room is complete
                        destination_path, destination_label = destination_info
                        destination_room = self.find_room_by_path_and_label(
                            destination_path, destination_label
                        )

                        if destination_room and not destination_room.is_complete():
                            # We found the blocking partial room - prioritize completing it with all doors
                            batch_paths = []
                            for dest_door in range(6):
                                dest_exploration_path = destination_path + [dest_door]
                                path_tuple = tuple(dest_exploration_path)

                                if path_tuple not in self.explored_paths:
                                    batch_paths.append(dest_exploration_path)

                            if batch_paths:
                                unknown_connections.append(
                                    {
                                        "from_room": room,
                                        "door": door,
                                        "blocking_room": destination_room,
                                        "paths": batch_paths,  # Multiple paths for batch exploration
                                        "priority": "complete_blocking_partial_room_batch",
                                        "reason": f"Complete destination room to verify {room.get_fingerprint()} door {door}",
                                    }
                                )
                                return (
                                    unknown_connections  # Focus on one room at a time
                                )

                    # Fallback: try direct exploration if no observation yet
                    exploration_path = base_path + [door]
                    unknown_connections.append(
                        {
                            "from_room": room,
                            "door": door,
                            "path": exploration_path,
                            "priority": "verify_complete_room_connection",
                        }
                    )

        return unknown_connections

    def get_door_destination_info(self, from_room, door):
        """Get destination path and label for a door, if we have an observation"""
        for obs in self.observations:
            if len(obs["plan"]) >= 1 and len(obs["rooms"]) >= 2:
                # Check if this observation shows us going through this door from this room
                for from_path in from_room.paths:
                    if len(obs["plan"]) > len(from_path):
                        if (
                            obs["plan"][: len(from_path)] == from_path
                            and obs["plan"][len(from_path)] == door
                        ):
                            # Found matching observation
                            if len(obs["rooms"]) > len(from_path) + 1:
                                destination_label = obs["rooms"][len(from_path) + 1]
                                destination_path = obs["plan"][: len(from_path) + 1]
                                return destination_path, destination_label
        return None

    def find_room_by_path_and_label(self, path, label):
        """Find a room with the given path and label"""
        for room in self.possible_rooms:
            if room.label == label and path in room.paths:
                return room
        return None

    def get_partial_rooms_to_explore(self):
        """Find partial rooms that we could explore further"""
        partial_explorations = []

        # Find partial rooms that we haven't fully explored from
        partial_rooms = [room for room in self.possible_rooms if not room.is_complete()]

        for room in partial_rooms:
            if not room.paths:
                continue

            base_path = room.paths[0]  # Use first path to reach this room

            # Try to explore all doors from this partial room
            for door in range(6):
                exploration_path = base_path + [door]
                path_tuple = tuple(exploration_path)

                # Only suggest if we haven't explored this path yet
                if path_tuple not in self.explored_paths:
                    partial_explorations.append(
                        {
                            "from_room": room,
                            "door": door,
                            "path": exploration_path,
                            "priority": "partial_room_expansion",
                        }
                    )

        return partial_explorations

    def explore_incomplete_rooms(self):
        """Explore from rooms that have incomplete door information, prioritizing complete room connections"""
        # First priority: Verify unknown connections in complete rooms
        unknown_connections = self.get_unknown_connections_to_verify()

        if unknown_connections:
            # Take the first unknown connection
            connection = unknown_connections[0]

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
                print(
                    f"Found {len(unknown_connections)} unknown connections in complete rooms to verify"
                )

                from_room = connection["from_room"]
                door = connection["door"]
                path = connection["path"]

                print(
                    f"VERIFY: Exploring door {door} from complete room {from_room.get_fingerprint()} (absolute ID {self.get_absolute_room_mapping().get(from_room.get_fingerprint(), '?')})"
                )
                print(f"  Path: {path}")

                self.explore([path])

            # After exploration, check for and remove duplicates
            removed = self.remove_duplicate_rooms()
            if removed > 0:
                print("Updated room list after removing duplicates:")
                self.print_fingerprints()

            # Check if we can do aggressive cleanup now that we might have complete coverage
            cleaned = self.cleanup_all_partial_rooms_when_complete()
            if cleaned > 0:
                print("Final clean room list:")
                self.print_fingerprints()

            return  # Focus on one verification at a time

        # Second priority: Explore missing connections from complete rooms
        missing_connections = self.get_missing_connections_from_complete_rooms()

        if missing_connections:
            print(
                f"Found {len(missing_connections)} high-priority connections from complete rooms"
            )

            # Take the first missing connection
            connection = missing_connections[0]
            from_room = connection["from_room"]
            door = connection["door"]
            target_label = connection["target_label"]
            path = connection["path"]

            print(
                f"PRIORITY: Exploring door {door} from complete room {from_room.label} -> label {target_label}"
            )
            print(f"  Path: {path}")

            self.explore([path])

            # After exploration, check for and remove duplicates
            removed = self.remove_duplicate_rooms()
            if removed > 0:
                print("Updated room list after removing duplicates:")
                self.print_fingerprints()

            return  # Focus on one high-priority connection at a time

        # Third priority: Explore from partial rooms we discovered
        partial_explorations = self.get_partial_rooms_to_explore()

        if partial_explorations:
            print(
                f"Found {len(partial_explorations)} partial room explorations available"
            )

            # Take the first partial room exploration
            exploration = partial_explorations[0]
            from_room = exploration["from_room"]
            door = exploration["door"]
            path = exploration["path"]

            print(
                f"PARTIAL: Exploring door {door} from partial room {from_room.label} (path {from_room.paths[0]})"
            )
            print(f"  Full path: {path}")

            self.explore([path])

            # After exploration, check for and remove duplicates
            removed = self.remove_duplicate_rooms()
            if removed > 0:
                print("Updated room list after removing duplicates:")
                self.print_fingerprints()

            return  # Focus on one exploration at a time

        # Fourth priority: Regular incomplete room exploration
        incomplete = self.get_incomplete_rooms()

        if not incomplete:
            print("All rooms are complete!")
            return

        print(
            f"No high-priority or partial room explorations found. Found {len(incomplete)} incomplete rooms"
        )

        # For each incomplete room, explore its unknown doors
        for room in incomplete:
            doors_to_explore = self.get_doors_worth_exploring(room)
            if doors_to_explore and room.paths:
                # Use the first path to this room as base
                base_path = room.paths[0]

                # Create plans to explore doors worth exploring
                plans = []
                for door in doors_to_explore:
                    plan = base_path + [door]
                    plans.append(plan)

                print(
                    f"FALLBACK: Exploring doors {doors_to_explore} from incomplete room {room.label} (had {len(room.get_unknown_doors())} unknown)"
                )
                print(f"  Base path: {base_path}")

                self.explore(plans)

                # After exploration, check for and remove duplicates
                removed = self.remove_duplicate_rooms()
                if removed > 0:
                    print("Updated room list after removing duplicates:")
                    self.print_fingerprints()

                break  # Explore one room at a time

    def explore_until_complete(self, max_iterations=10000):
        """Keep exploring incomplete rooms until all are complete or max iterations reached"""
        print("=== Exploring Until Complete ===")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Check if we have any incomplete rooms or unknown connections
            incomplete_rooms = self.get_incomplete_rooms()

            # Also check for unknown connections in complete rooms
            unknown_connections = self.get_unknown_connections_to_verify()
            missing_connections = self.get_missing_connections_from_complete_rooms()
            partial_explorations = self.get_partial_rooms_to_explore()

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
        self.possible_rooms = []  # Reset rooms

        # Replay observations
        for obs in self.observations:
            self.process_observation(obs["plan"], obs["rooms"])

        # Populate explored paths from the loaded observations
        self.populate_explored_paths_from_observations()

        print(f"Loaded {len(self.observations)} observations from {filename}")
        self.print_fingerprints()

    def generate_solution(self, filename="solution.json"):
        """Generate the solution in the JSON format expected by bin/guess"""
        print("=== SOLUTION FOR bin/guess ===")

        # Get all complete rooms sorted by absolute ID
        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]
        fingerprint_to_absolute_id = self.get_absolute_room_mapping()

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

        # Generate connections with proper door mapping, using room indexes
        connections_set = set()  # Use set to avoid duplicates

        for from_abs_id in sorted(absolute_id_to_room.keys()):
            from_room = absolute_id_to_room[from_abs_id]
            from_index = absolute_id_to_index[from_abs_id]
            connections = self.get_absolute_connections(from_room)

            for from_door, to_abs_id in enumerate(connections):
                if to_abs_id is not None:
                    to_room = absolute_id_to_room[to_abs_id]
                    to_index = absolute_id_to_index[to_abs_id]

                    # Find which door on the destination room leads back to from_abs_id
                    to_connections = self.get_absolute_connections(to_room)
                    to_door = None

                    # Find all potential reverse doors
                    potential_to_doors = []
                    for potential_to_door, reverse_abs_id in enumerate(to_connections):
                        if reverse_abs_id == from_abs_id:
                            potential_to_doors.append(potential_to_door)

                    # If we have multiple options, try to find one that hasn't been used yet
                    if potential_to_doors:
                        for potential_to_door in potential_to_doors:
                            # Check if this bidirectional connection is already in our set
                            test_connection_key = (
                                min(from_index, to_index),
                                max(from_index, to_index),
                                min(from_door, potential_to_door),
                                max(from_door, potential_to_door),
                            )
                            if test_connection_key not in connections_set:
                                to_door = potential_to_door
                                break

                        # If all potential doors are already used, take the first one
                        if to_door is None:
                            to_door = potential_to_doors[0]

                    if to_door is not None:
                        # Create a unique key for this connection (bidirectional)
                        connection_key = (
                            min(from_index, to_index),
                            max(from_index, to_index),
                            min(from_door, to_door),
                            max(from_door, to_door),
                        )

                        if connection_key not in connections_set:
                            connections_set.add(connection_key)

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
                    else:
                        print(
                            f"Warning: Could not find reverse door for Room {from_abs_id} door {from_door} -> Room {to_abs_id}"
                        )

        # Find the actual starting room (the one with empty path) and convert to index
        for abs_id, room in absolute_id_to_room.items():
            if [] in room.paths:
                solution["startingRoom"] = absolute_id_to_index[abs_id]
                break

        # Write to file with double quotes
        import json

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
