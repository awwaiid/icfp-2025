"""
Room Manager for the ICFP 2025 room exploration problem
"""

from typing import List, Dict, Tuple, Optional, Any
from .room import Room


class RoomManager:
    """Manages the collection of rooms and their relationships"""

    def __init__(self, room_count: int, observations: List[Dict]):
        self.room_count = room_count
        self.possible_rooms = []  # List of discovered room possibilities
        self.observations = observations

    def get_all_rooms(self) -> List[Room]:
        """Get all rooms"""
        return self.possible_rooms

    def get_complete_rooms(self) -> List[Room]:
        """Get rooms that have complete door information"""
        return [room for room in self.possible_rooms if room.is_complete()]

    def get_incomplete_rooms(self) -> List[Room]:
        """Get rooms that don't have complete door information"""
        return [room for room in self.possible_rooms if not room.is_complete()]

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

    def find_identical_fingerprints(self) -> Dict[str, List[Tuple[int, Room]]]:
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

    def get_absolute_room_mapping(self) -> Dict[str, int]:
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

    def get_door_destination_fingerprint(self, from_room: Room, door: int) -> Optional[str]:
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

    def get_absolute_connections(self, room: Room, debug: bool = False) -> List[Optional[int]]:
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

    def remove_duplicate_rooms(self) -> int:
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

    def can_trace_path_to_complete_room(self, partial_path: List[int], debug: bool = False) -> Optional[Room]:
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

    def cleanup_redundant_partial_rooms(self) -> int:
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

    def cleanup_all_partial_rooms_when_complete(self) -> int:
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

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the room collection"""
        complete_rooms = self.get_complete_rooms()
        total_connections = 0
        verified_connections = 0
        
        for room in complete_rooms:
            connections = self.get_absolute_connections(room)
            total_connections += len(connections)
            verified_connections += sum(1 for conn in connections if conn is not None)

        return {
            "total_rooms": len(self.possible_rooms),
            "complete_rooms": len(complete_rooms),
            "incomplete_rooms": len(self.get_incomplete_rooms()),
            "total_connections": total_connections,
            "verified_connections": verified_connections,
            "max_possible": self.room_count * 6,
            "unique_rooms": len(set(room.get_fingerprint() for room in complete_rooms))
        }