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

        # Before creating a new room, check if this path can be traced through complete rooms
        destination_room = self.can_trace_path_to_complete_room(path, debug=False)
        if destination_room and destination_room.label == label:
            print(f"    Path {path} traces to existing complete room {destination_room.get_fingerprint()}")
            # Add this path to the existing complete room
            destination_room.add_path(path)
            return destination_room

        # If no match found through tracing, create new room
        # (We can't assume same label = same room since labels can be reused)
        print(f"    Creating new partial room for path {path} with label {label}")
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

    def get_door_destination_fingerprint(
        self, from_room: Room, door: int
    ) -> Optional[str]:
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

    def get_absolute_connections(
        self, room: Room, debug: bool = False
    ) -> List[Optional[int]]:
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

    def assign_initial_disambiguation_ids(self):
        """Assign disambiguation ID 0 to unique complete rooms"""
        complete_rooms = self.get_complete_rooms()
        
        # Group by base fingerprint
        base_fingerprint_groups = {}
        for room in complete_rooms:
            base_fp = room.get_fingerprint(include_disambiguation=False)
            if base_fp not in base_fingerprint_groups:
                base_fingerprint_groups[base_fp] = []
            base_fingerprint_groups[base_fp].append(room)
        
        # Assign ID 0 to rooms that are unique
        for base_fp, rooms in base_fingerprint_groups.items():
            if len(rooms) == 1:
                room = rooms[0]
                if not hasattr(room, 'disambiguation_id') or room.disambiguation_id is None:
                    room.disambiguation_id = 0
                    print(f"Assigned disambiguation ID 0 to unique room: {room.get_fingerprint()}")

    def remove_duplicate_rooms(self, api_client=None) -> int:
        """Remove duplicate rooms with identical complete fingerprints, using disambiguation when needed"""
        # First, assign ID 0 to unique rooms
        self.assign_initial_disambiguation_ids()
        
        identical_groups = self.find_identical_fingerprints()

        if not identical_groups:
            return 0  # No duplicates found

        removed_count = 0

        # For each group of identical fingerprints, disambiguate before merging
        for fingerprint, rooms in identical_groups.items():
            # Sort by room index to have consistent behavior
            rooms.sort(key=lambda x: x[0])  # Sort by room index

            print(f"Processing rooms with identical fingerprint '{fingerprint}':")
            
            if len(rooms) == 2 and api_client:
                # The first room (already exists) should have disambiguation_id = 0
                # The second room (newly discovered) gets disambiguation_id = ? until verified
                room_idx_a, room_a = rooms[0]
                room_idx_b, room_b = rooms[1]
                
                # Ensure first room has ID 0, second room has None (shows as ?)
                if not hasattr(room_a, 'disambiguation_id') or room_a.disambiguation_id is None:
                    room_a.disambiguation_id = 0
                if hasattr(room_b, 'disambiguation_id') and room_b.disambiguation_id == 0:
                    room_b.disambiguation_id = None  # Reset to ? until verified
                
                print(f"  Disambiguating Room {room_idx_a} (ID: {room_a.disambiguation_id}) and Room {room_idx_b} (ID: ?)")
                
                try:
                    are_different = self.disambiguate_rooms_with_path_navigation(room_a, room_b, api_client)
                    
                    if are_different:
                        print(f"  ✅ Rooms confirmed DIFFERENT - assigning disambiguation ID 1 to new room")
                        room_b.disambiguation_id = 1  # Now it gets ID 1
                        continue  # Keep both rooms, don't merge
                    else:
                        print(f"  ❌ Rooms confirmed SAME - will merge")
                        # Fall through to merge logic below
                        
                except Exception as e:
                    print(f"  ⚠️ Disambiguation failed ({e}) - will merge as duplicates")
                    # Fall through to merge logic below

            # Merge duplicate rooms (either disambiguation failed or confirmed same)
            keeper_idx, keeper_room = rooms[0]
            rooms_to_remove = []

            print(f"  Merging rooms:")
            print(f"    Keeping Room {keeper_idx}")

            # Ensure keeper gets ID 0 if it doesn't have one
            if not hasattr(keeper_room, 'disambiguation_id') or keeper_room.disambiguation_id is None:
                keeper_room.disambiguation_id = 0

            # Merge paths from duplicate rooms into the keeper
            for room_idx, room in rooms[1:]:
                print(f"    Removing Room {room_idx} (merging paths)")

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
            print(f"Removed {removed_count} duplicate rooms after disambiguation checks")

        return removed_count

    def can_trace_path_to_complete_room(
        self, partial_path: List[int], debug: bool = False
    ) -> Optional[Room]:
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
    
    def cleanup_all_traceable_partial_rooms(self) -> int:
        """Remove all partial rooms whose paths can be traced to complete rooms"""
        removed_count = 0
        partial_rooms = [room for room in self.possible_rooms if not room.is_complete()]
        rooms_to_remove = []
        
        print(f"Checking {len(partial_rooms)} partial rooms for traceability...")
        
        for partial_room in partial_rooms:
            for path in partial_room.paths:
                destination_room = self.can_trace_path_to_complete_room(path, debug=False)
                
                if destination_room and destination_room.label == partial_room.label:
                    print(f"  Removing partial room {partial_room.label} at path {path}")
                    print(f"    -> Traced to complete room {destination_room.get_fingerprint()}")
                    
                    # Add this path to the complete room
                    destination_room.add_path(path)
                    rooms_to_remove.append(partial_room)
                    removed_count += 1
                    break  # Move on to next partial room
        
        # Remove the traceable partial rooms
        for room_to_remove in rooms_to_remove:
            if room_to_remove in self.possible_rooms:
                self.possible_rooms.remove(room_to_remove)
        
        if removed_count > 0:
            print(f"Removed {removed_count} traceable partial rooms")
        
        return removed_count
    
    def detect_and_resolve_ambiguous_rooms(self) -> int:
        """Detect rooms with identical base fingerprints and assign disambiguation IDs"""
        disambiguation_count = 0
        
        # Group complete rooms by base fingerprint (without disambiguation)
        base_fingerprint_groups = {}
        for room in self.possible_rooms:
            if room.is_complete():
                base_fp = room.get_fingerprint(include_disambiguation=False)
                if base_fp not in base_fingerprint_groups:
                    base_fingerprint_groups[base_fp] = []
                base_fingerprint_groups[base_fp].append(room)
        
        # Find groups with multiple rooms (ambiguous fingerprints)
        for base_fp, rooms in base_fingerprint_groups.items():
            if len(rooms) > 1:
                print(f"Found {len(rooms)} rooms with identical base fingerprint '{base_fp}':")
                
                # Assign disambiguation IDs
                for i, room in enumerate(rooms):
                    room.disambiguation_id = i
                    print(f"  Room {i}: {room.get_fingerprint()} at paths {room.paths}")
                    disambiguation_count += 1
        
        return disambiguation_count
    
    def verify_room_disambiguation_with_backtracking(self, room_a: Room, room_b: Room) -> bool:
        """Verify if two rooms with same base fingerprint are actually different using backtracking"""
        if not room_a.is_complete() or not room_b.is_complete():
            return False
            
        base_fp_a = room_a.get_fingerprint(include_disambiguation=False)
        base_fp_b = room_b.get_fingerprint(include_disambiguation=False)
        
        if base_fp_a != base_fp_b:
            return True  # Different base fingerprints, clearly different rooms
        
        # Same base fingerprint - use backtracking to verify if they're different
        # Compare return door patterns - if they lead to different rooms, they're different
        
        # For each door in both rooms, check if they lead to rooms that can be distinguished
        for door in range(6):
            label_a = room_a.door_labels[door]
            label_b = room_b.door_labels[door]
            
            if label_a != label_b:
                return True  # Different destination labels, clearly different
                
            if label_a is not None:  # Both have the same destination label
                # Find return doors that lead back to each room
                return_doors_a = self.find_return_doors_to_room(room_a)
                return_doors_b = self.find_return_doors_to_room(room_b)
                
                # If return door patterns are different, rooms are different
                if return_doors_a != return_doors_b:
                    return True
        
        return False  # Cannot distinguish - might be the same room
    
    def find_return_doors_to_room(self, target_room: Room) -> Dict[str, List[int]]:
        """Find all doors in other rooms that lead back to target_room"""
        return_doors = {}
        
        for room in self.possible_rooms:
            if room != target_room and room.is_complete():
                doors_to_target = []
                for door, label in enumerate(room.door_labels):
                    if label == target_room.label:
                        doors_to_target.append(door)
                
                if doors_to_target:
                    room_fp = room.get_fingerprint(include_disambiguation=False)
                    return_doors[room_fp] = doors_to_target
        
        return return_doors
    
    def disambiguate_rooms_with_path_navigation(self, room_a: Room, room_b: Room, api_client) -> bool:
        """Use path navigation and label editing to determine if two rooms are actually different
        
        Algorithm:
        1. Find a path from room_a to room_b  
        2. Navigate to room_a, edit its label to a unique value
        3. Navigate from room_a to room_b following the path
        4. Check room_b's label - if unchanged, they're different rooms
        
        Returns True if rooms are confirmed different, False if same or unclear
        """
        if not room_a.paths or not room_b.paths:
            return False
            
        # Get paths to each room
        path_to_a = room_a.paths[0]
        path_to_b = room_b.paths[0]
        
        # Simple case: if B is reachable from A by additional steps
        if len(path_to_b) > len(path_to_a) and path_to_b[:len(path_to_a)] == path_to_a:
            # B is reachable from A
            path_a_to_b = path_to_b[len(path_to_a):]
            
            print(f"Disambiguating via path: A{path_to_a} -> [edit] -> A{path_to_a}{path_a_to_b}")
            
            # Choose a unique label for editing (different from both rooms)
            edit_label = None
            for candidate in [2, 3, 1, 0]:  # Try different labels
                if candidate != room_a.label and candidate != room_b.label:
                    edit_label = candidate
                    break
                    
            if edit_label is None:
                print("Cannot find unique edit label")
                return False
            
            # Construct disambiguation plan: path_to_a + [edit] + path_from_a_to_b
            plan_parts = path_to_a + [f"[{edit_label}]"] + path_a_to_b
            plan_string = "".join(str(x) for x in plan_parts)
            
            print(f"Executing plan: {plan_string}")
            
            try:
                result = api_client.explore([plan_string])
                
                if result and "results" in result:
                    response = result["results"][0]
                    
                    # Parse response
                    actual_labels, echo_labels = api_client.parse_response_with_echoes(plan_string, response)
                    
                    if actual_labels:
                        final_label = actual_labels[-1]
                        print(f"Final label at B: {final_label} (original: {room_b.label}, edit: {edit_label})")
                        
                        if final_label == room_b.label:
                            print("✅ Rooms are DIFFERENT - B kept original label")
                            return True
                        elif final_label == edit_label:
                            print("❌ Rooms are SAME - B has edited label")
                            return False
                        else:
                            print(f"❓ Unclear result - B has unexpected label {final_label}")
                            return False
                            
            except Exception as e:
                print(f"Disambiguation failed: {e}")
                return False
        
        # TODO: Handle more complex path relationships (A->B via different routes)
        print("No simple path from A to B found for disambiguation")
        return False

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
            "unique_rooms": len(set(room.get_fingerprint() for room in complete_rooms)),
        }
