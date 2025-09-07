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

    def find_or_create_room_for_path(self, path: List[int], label: int, api_client=None) -> Room:
        """Find existing room matching path and label, or create new one with proper verification"""
        # First check: Look for existing room with this exact path and label
        for room in self.possible_rooms:
            if path in room.paths and room.label == label:
                return room

        # Second check: If we have a complete room that points to the same label,
        # check if this path should be added to an existing destination room
        if path:  # Don't do this for bootstrap (empty path)
            # Find complete rooms that might have created this destination
            for complete_room in self.possible_rooms:
                if complete_room.is_complete() and complete_room != self:
                    # Check if this complete room's doors point to our label
                    for door, door_label in enumerate(complete_room.door_labels):
                        if door_label == label:
                            # This complete room has a door leading to our label
                            # Check if there's an existing room for that door
                            door_path = complete_room.paths[0] + [door] 
                            for existing_room in self.possible_rooms:
                                if door_path in existing_room.paths and existing_room.label == label:
                                    # Found existing room - add this path to it
                                    print(f"    Adding path {path} to existing destination room {existing_room.get_fingerprint()}")
                                    existing_room.add_path(path)
                                    return existing_room

        # Third check: Look for complete rooms with same label for navigation testing
        if api_client and path:  # Don't test during initial bootstrap
            complete_candidates = [r for r in self.possible_rooms 
                                 if r.label == label and r.is_complete()]
            
            for existing_room in complete_candidates:
                try:
                    # Create a temporary room to test against
                    temp_room = Room(label)
                    temp_room.add_path(path)
                    
                    # Test if they're the same room using navigation
                    are_different = self.disambiguate_rooms_with_path_navigation(
                        existing_room, temp_room, api_client
                    )
                    
                    if not are_different:
                        # They're the same room! Add this path to the existing room
                        print(f"    Navigation test shows path {path} leads to existing room {existing_room.get_fingerprint()}")
                        existing_room.add_path(path)
                        return existing_room
                    else:
                        print(f"    Navigation test shows path {path} leads to different room than {existing_room.get_fingerprint()}")
                except Exception as e:
                    print(f"    Navigation test failed: {e}")
                    # Continue to test other rooms

        # If no matches or all tests show different, create new room
        print(f"    Creating new partial room for path {path} with label {label}")
        new_room = Room(label)
        new_room.add_path(path)
        self.possible_rooms.append(new_room)
        return new_room
    
    def _get_potential_adjacent_labels(self, path: List[int], label: int, api_client) -> Optional[List[int]]:
        """Try to determine what adjacent-room labels would be for a room at this path using actual exploration"""
        if not path or not api_client:
            return None
        
        try:
            # Create exploration plans to navigate to this room and check each door
            base_path_string = "".join(str(door) for door in path)
            explore_plans = []
            
            # For each door (0-5), create a plan to go to this room and then through that door
            for door in range(6):
                explore_plan = base_path_string + str(door)
                explore_plans.append(explore_plan)
            
            # Execute the exploration
            result = api_client.explore(explore_plans)
            
            if result and "results" in result and len(result["results"]) == len(explore_plans):
                adjacent_labels = []
                
                # Parse each result to get the adjacent room labels
                for i, result_data in enumerate(result["results"]):
                    if "rooms" in result_data and len(result_data["rooms"]) >= len(path) + 2:
                        # The adjacent room label is at index len(path) + 1 
                        # (starting room at 0, intermediate rooms, then destination)
                        adjacent_label = result_data["rooms"][len(path) + 1]
                        adjacent_labels.append(adjacent_label)
                    else:
                        # Couldn't determine this adjacent label
                        adjacent_labels.append(None)
                
                # Only return if we got all 6 adjacent labels
                if len(adjacent_labels) == 6 and all(label is not None for label in adjacent_labels):
                    return adjacent_labels
                    
        except Exception as e:
            print(f"Error in _get_potential_adjacent_labels: {e}")
        
        return None
    
    def _create_partial_fingerprint(self, label: int, adjacent_labels: List[int]) -> str:
        """Create partial fingerprint from room label and adjacent labels"""
        adjacent_str = "".join(str(adj) for adj in adjacent_labels)
        return f"{label}-{adjacent_str}"
    
    def _find_rooms_with_partial_fingerprint(self, partial_fingerprint: str) -> List[Room]:
        """Find existing disambiguated rooms that match this partial fingerprint"""
        matching_rooms = []
        for room in self.possible_rooms:
            if room.is_complete() and hasattr(room, 'disambiguation_id') and room.disambiguation_id is not None:
                # Get the room's base fingerprint without disambiguation ID
                room_fingerprint = room.get_fingerprint()
                if '-' in room_fingerprint:
                    # Remove disambiguation ID (everything after the last dash)
                    base_fingerprint = room_fingerprint.rsplit('-', 1)[0]
                    if base_fingerprint == partial_fingerprint:
                        matching_rooms.append(room)
        return matching_rooms

    def find_identical_fingerprints(self) -> Dict[str, List[Tuple[int, Room]]]:
        """Find rooms with identical fingerprints (likely the same room)"""
        fingerprint_groups = {}

        # Group rooms by fingerprint (excluding disambiguation ID for comparison)
        for i, room in enumerate(self.possible_rooms):
            if room.is_complete():  # Only compare complete fingerprints
                fp = room.get_fingerprint(include_disambiguation=False)  # Compare base fingerprints only
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
            
            if len(rooms) >= 2 and api_client:
                # Handle multiple rooms with identical fingerprints systematically
                # Use an incremental approach: test each room against all previous confirmed distinct rooms
                confirmed_distinct_rooms = []
                next_disambiguation_id = 0
                
                for room_idx_test, room_test in rooms:
                    room_test.disambiguation_id = None  # Reset
                    is_same_as_existing = False
                    
                    # Test this room against all confirmed distinct rooms
                    for existing_idx, existing_room in confirmed_distinct_rooms:
                        print(f"  Disambiguating Room {existing_idx} (ID: {existing_room.disambiguation_id}) and Room {room_idx_test} (ID: ?)")
                        
                        try:
                            are_different = self.disambiguate_rooms_with_path_navigation(existing_room, room_test, api_client)
                            
                            if not are_different:
                                # Rooms are the same - merge with existing room
                                print(f"  ❌ Rooms confirmed SAME - will merge with Room {existing_idx}")
                                is_same_as_existing = True
                                break  # Found a match, no need to test further
                                
                        except Exception as e:
                            print(f"  ⚠️ Disambiguation failed ({e}) - assuming rooms are same")
                            is_same_as_existing = True
                            break
                    
                    if not is_same_as_existing:
                        # This is a new distinct room
                        room_test.disambiguation_id = next_disambiguation_id
                        confirmed_distinct_rooms.append((room_idx_test, room_test))
                        print(f"  ✅ Room {room_idx_test} confirmed DISTINCT - assigning disambiguation ID {next_disambiguation_id}")
                        next_disambiguation_id += 1
                
                # Merge rooms that weren't confirmed as distinct (they're duplicates of existing rooms)
                rooms_to_merge = []
                rooms_to_keep = []
                
                for room_idx, room in rooms:
                    # Check if this room was confirmed as distinct
                    is_distinct = any(existing_idx == room_idx for existing_idx, _ in confirmed_distinct_rooms)
                    if is_distinct:
                        rooms_to_keep.append((room_idx, room))
                    else:
                        rooms_to_merge.append((room_idx, room))
                
                # If there are rooms to merge, merge them into the first confirmed distinct room
                if rooms_to_merge and confirmed_distinct_rooms:
                    keeper_idx, keeper_room = confirmed_distinct_rooms[0]  # First distinct room
                    print(f"  Merging duplicate rooms into Room {keeper_idx}:")
                    
                    for room_idx, room in rooms_to_merge:
                        print(f"    Merging Room {room_idx} into Room {keeper_idx}")
                        # Add paths from duplicate room to keeper
                        for path in room.paths:
                            if path not in keeper_room.paths:
                                keeper_room.add_path(path)
                        
                        # Remove duplicate room
                        if room in self.possible_rooms:
                            self.possible_rooms.remove(room)
                            removed_count += 1
                
                if len(confirmed_distinct_rooms) > 1:
                    print(f"  Kept {len(confirmed_distinct_rooms)} distinct rooms after disambiguation and merging")
                    continue  # Don't run the old merge logic

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


    def cleanup_redundant_partial_rooms(self) -> int:
        """Remove partial rooms that are redundant with complete rooms
        
        NOTE: Path tracing has been removed. Room deduplication now relies entirely on
        navigation and label editing during the disambiguation phase.
        """
        return 0
    
    def cleanup_all_traceable_partial_rooms(self) -> int:
        """Remove all partial rooms whose paths can be traced to complete rooms
        
        NOTE: Path tracing has been removed. Room deduplication now relies entirely on
        navigation and label editing during the disambiguation phase.
        """
        return 0
    
    def merge_rooms_with_identical_partial_fingerprints(self, api_client=None) -> int:
        """Merge rooms that have identical partial fingerprints, using navigation-based testing for complete rooms"""
        merged_count = 0
        
        # Group rooms by partial fingerprint (label + known door labels)
        fingerprint_groups = {}
        
        for room in self.possible_rooms:
            if not room.paths:  # Skip rooms with no paths
                continue
                
            # Create a partial fingerprint based on what we know
            partial_fp = self._get_partial_fingerprint_for_room(room)
            if partial_fp:
                if partial_fp not in fingerprint_groups:
                    fingerprint_groups[partial_fp] = []
                fingerprint_groups[partial_fp].append(room)
        
        # Process rooms in groups with identical partial fingerprints
        for partial_fp, rooms in fingerprint_groups.items():
            if len(rooms) > 1:
                print(f"Found {len(rooms)} rooms with partial fingerprint {partial_fp}")
                
                # Check if these are complete rooms with identical fingerprints
                complete_rooms = [r for r in rooms if r.is_complete()]
                incomplete_rooms = [r for r in rooms if not r.is_complete()]
                
                if len(complete_rooms) > 1 and api_client:
                    # Use navigation-based testing for complete rooms with identical fingerprints
                    print(f"  {len(complete_rooms)} complete rooms need disambiguation testing")
                    
                    # Keep the first room and test others against it
                    primary_room = complete_rooms[0]
                    for other_room in complete_rooms[1:]:
                        try:
                            are_different = self.disambiguate_rooms_with_path_navigation(primary_room, other_room, api_client)
                            if are_different:
                                # Rooms are different - assign disambiguation ID
                                if other_room.disambiguation_id is None:
                                    other_room.disambiguation_id = len([r for r in self.possible_rooms if r.get_fingerprint(include_disambiguation=False) == other_room.get_fingerprint(include_disambiguation=False) and r.disambiguation_id is not None]) + 1
                                    print(f"  Assigned disambiguation ID {other_room.disambiguation_id} to different room")
                            else:
                                # Rooms are the same - merge them
                                print(f"  Navigation test shows rooms are same - merging paths")
                                for path in other_room.paths:
                                    primary_room.add_path(path)
                                self.possible_rooms.remove(other_room)
                                merged_count += 1
                        except Exception as e:
                            print(f"  Navigation test failed: {e}")
                            # If navigation test fails, assume they're different
                            if other_room.disambiguation_id is None:
                                other_room.disambiguation_id = len([r for r in self.possible_rooms if r.get_fingerprint(include_disambiguation=False) == other_room.get_fingerprint(include_disambiguation=False) and r.disambiguation_id is not None]) + 1
                                print(f"  Assigned disambiguation ID {other_room.disambiguation_id} due to test failure")
                
                # For incomplete rooms with same partial fingerprint, merge them (they're clearly the same)
                if len(incomplete_rooms) > 1:
                    print(f"  Merging {len(incomplete_rooms)} incomplete rooms with same partial fingerprint")
                    primary_room = incomplete_rooms[0]
                    for other_room in incomplete_rooms[1:]:
                        # Merge paths
                        for path in other_room.paths:
                            primary_room.add_path(path)
                        
                        # Merge door label information
                        for door in range(6):
                            if (door < len(other_room.door_labels) and 
                                other_room.door_labels[door] is not None):
                                if door >= len(primary_room.door_labels):
                                    primary_room.door_labels.extend([None] * (door + 1 - len(primary_room.door_labels)))
                                if primary_room.door_labels[door] is None:
                                    primary_room.door_labels[door] = other_room.door_labels[door]
                        
                        # Remove the merged room
                        if other_room in self.possible_rooms:
                            self.possible_rooms.remove(other_room)
                            merged_count += 1
                    
                    print(f"    Merged into room with paths: {primary_room.paths}")
        
        return merged_count
    
    def consolidate_destination_paths(self) -> int:
        """Consolidate paths that lead to the same destination room from complete rooms"""
        consolidated_count = 0
        
        # Find complete rooms that might have multiple paths leading to the same destinations
        complete_rooms = self.get_complete_rooms()
        
        for complete_room in complete_rooms:
            if not complete_room.door_labels:
                continue
                
            # Group doors by destination label
            destinations = {}
            for door, label in enumerate(complete_room.door_labels):
                if label is not None:
                    if label not in destinations:
                        destinations[label] = []
                    destinations[label].append(door)
            
            # For each destination label that has multiple doors
            for label, doors in destinations.items():
                if len(doors) > 1:
                    # Find rooms that correspond to these doors
                    target_rooms = []
                    base_path = complete_room.paths[0]
                    
                    for door in doors:
                        door_path = base_path + [door]
                        for room in self.possible_rooms:
                            if door_path in room.paths and room.label == label:
                                target_rooms.append((door, room))
                    
                    # If we found multiple rooms for the same destination label, consolidate them
                    if len(target_rooms) > 1:
                        # Use the first room as the primary room
                        primary_door, primary_room = target_rooms[0]
                        
                        # Merge all other rooms into the primary room
                        for door, other_room in target_rooms[1:]:
                            if other_room != primary_room:
                                print(f"    Consolidating room {other_room.get_fingerprint()} into {primary_room.get_fingerprint()}")
                                # Merge paths
                                for path in other_room.paths:
                                    primary_room.add_path(path)
                                
                                # Merge door information
                                if other_room.door_labels:
                                    for i, door_label in enumerate(other_room.door_labels):
                                        if door_label is not None:
                                            if i >= len(primary_room.door_labels):
                                                primary_room.door_labels.extend([None] * (i + 1 - len(primary_room.door_labels)))
                                            if primary_room.door_labels[i] is None:
                                                primary_room.door_labels[i] = door_label
                                
                                # Remove the consolidated room
                                if other_room in self.possible_rooms:
                                    self.possible_rooms.remove(other_room)
                                    consolidated_count += 1
        
        return consolidated_count
    
    def _get_partial_fingerprint_for_room(self, room) -> Optional[str]:
        """Get a partial fingerprint for a room - ONLY when ALL doors are known"""
        # CRITICAL: We can only merge rooms when we have COMPLETE door information
        # AND we have performed navigation-based verification using label-editing
        
        if not room.door_labels or len(room.door_labels) < 6:
            return None  # Need all 6 doors
            
        # Count how many doors we know about
        known_doors = sum(1 for label in room.door_labels if label is not None)
        
        # Only create fingerprints when we have ALL 6 door labels
        # This prevents ANY premature merging before verification
        if known_doors < 6:
            return None
            
        # Create fingerprint with all known doors
        door_str = ""
        for i in range(6):
            door_str += str(room.door_labels[i])
        
        return f"{room.label}-{door_str}"
    
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
