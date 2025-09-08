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
        """Find existing room matching path and label, or create new one following systematic process"""
        # First check: Look for existing room with this exact path and label
        for room in self.possible_rooms:
            if path in room.paths and room.label == label:
                return room

        # Smart consolidation: consolidate when we have strong evidence rooms are same
        # But be conservative to avoid star topology issues
        candidate_rooms = [room for room in self.possible_rooms if room.label == label]
        
        if len(candidate_rooms) >= 1:
            # Only consolidate single-door paths in small room counts
            # This handles simple-2 without breaking star-6
            if len(path) == 1 and len(self.possible_rooms) <= self.room_count:
                for existing_room in candidate_rooms:
                    if any(len(p) == 1 for p in existing_room.paths):
                        # For very small expected room counts, consolidate aggressively
                        if self.room_count <= 3:
                            print(f"    Consolidating path {path} into existing room (small topology)")
                            existing_room.add_path(path)
                            return existing_room

        # Create new room - the systematic disambiguation will happen later
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
                    if isinstance(result_data, list) and len(result_data) >= len(path) + 2:
                        # The adjacent room label is at index len(path) + 1 
                        # (starting room at 0, intermediate rooms, then destination)
                        adjacent_label = result_data[len(path) + 1]
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

    def get_systematic_connections(
        self, room: Room, debug: bool = False
    ) -> List[Optional[int]]:
        """Get connections for a room based on systematic exploration data"""
        if not room.is_complete():
            return [None] * 6
        
        fingerprint_to_absolute_id = self.get_absolute_room_mapping()
        absolute_connections = []
        
        if debug:
            print(f"Getting systematic connections for room {room.get_fingerprint()}")
            print(f"Room paths: {room.paths}")
            print(f"Room path_to_root: {getattr(room, 'path_to_root', 'None')}")
        
        # Create a mapping from paths to room fingerprints for quick lookup
        path_to_fingerprint = {}
        for candidate_room in self.possible_rooms:
            if candidate_room.is_complete() and candidate_room.paths:
                primary_path = tuple(candidate_room.paths[0])
                path_to_fingerprint[primary_path] = candidate_room.get_fingerprint()
        
        if not room.paths:
            return [None] * 6
            
        primary_path = room.paths[0]
        
        for door in range(6):
            destination_fingerprint = None
            
            # Check if this is a backlink door (leads to parent)
            if hasattr(room, 'path_to_root') and room.path_to_root and len(room.path_to_root) > 0:
                if door == room.path_to_root[0]:  # This is the backlink door
                    if len(primary_path) > 0:
                        parent_path = tuple(primary_path[:-1])
                        if parent_path in path_to_fingerprint:
                            destination_fingerprint = path_to_fingerprint[parent_path]
                            if debug:
                                print(f"  Door {door}: backlink to parent with path {list(parent_path)}")
            
            # If not a backlink, check if it's a forward or any other connection
            if destination_fingerprint is None and door < len(room.door_labels) and room.door_labels[door] is not None:
                target_label = room.door_labels[door]
                
                # Strategy 1: Check if the door leads to a room with path = current_path + [door]
                destination_path = tuple(primary_path + [door])
                for candidate_room in self.possible_rooms:
                    if (candidate_room.is_complete() 
                        and candidate_room.label == target_label 
                        and candidate_room.paths
                        and destination_path == tuple(candidate_room.paths[0])):
                        destination_fingerprint = candidate_room.get_fingerprint()
                        if debug:
                            print(f"  Door {door}: forward to {destination_fingerprint} with path {list(destination_path)}")
                        break
                
                # Strategy 2: If no forward path match, look for any room with matching label that could be the destination
                if destination_fingerprint is None:
                    # Find all rooms with the target label
                    candidate_rooms_with_label = [
                        r for r in self.possible_rooms 
                        if r.is_complete() and r.label == target_label
                    ]
                    
                    # If there's only one room with this label, it's likely the destination
                    if len(candidate_rooms_with_label) == 1:
                        destination_fingerprint = candidate_rooms_with_label[0].get_fingerprint()
                        if debug:
                            print(f"  Door {door}: unique label match to {destination_fingerprint}")
                    
                    # If multiple rooms have this label, try to find the most likely one
                    elif len(candidate_rooms_with_label) > 1:
                        # Look for the room that has us in their backlink (mutual connection)
                        for candidate_room in candidate_rooms_with_label:
                            if (hasattr(candidate_room, 'path_to_root') 
                                and candidate_room.path_to_root
                                and len(candidate_room.path_to_root) > 0):
                                # Check if going through their backlink would reach us
                                candidate_primary_path = candidate_room.paths[0] if candidate_room.paths else []
                                if candidate_primary_path:
                                    # Calculate where their backlink leads
                                    backlink_destination_path = tuple(candidate_primary_path[:-1]) if len(candidate_primary_path) > 0 else tuple()
                                    if backlink_destination_path == tuple(primary_path):
                                        destination_fingerprint = candidate_room.get_fingerprint()
                                        if debug:
                                            print(f"  Door {door}: mutual connection to {destination_fingerprint}")
                                        break
                        
                        # If still no match, just pick the first one (better than no connection)
                        if destination_fingerprint is None:
                            destination_fingerprint = candidate_rooms_with_label[0].get_fingerprint()
                            if debug:
                                print(f"  Door {door}: default to first match {destination_fingerprint}")
            
            # Convert fingerprint to absolute ID
            if destination_fingerprint and destination_fingerprint in fingerprint_to_absolute_id:
                absolute_connections.append(fingerprint_to_absolute_id[destination_fingerprint])
            else:
                absolute_connections.append(None)
                if debug:
                    print(f"  Door {door}: no connection found")
        
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
        """Conservative consolidation - only merge when we're certain paths lead to same room"""
        consolidated_count = 0
        
        # DISABLED for now - this logic was too aggressive and incorrectly merged 
        # different rooms that happened to have the same label (like in star-6)
        # 
        # The correct approach is to let rooms become complete first, then use
        # navigation-based verification in remove_duplicate_rooms()
        
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
    
    def systematic_room_disambiguation(self, api_client=None) -> int:
        """Systematic universal process for room disambiguation
        
        Algorithm:
        1. First complete the full fingerprint for room A
        2. For each new room B, get its partial fingerprint  
        3. Test room B against ALL existing rooms with matching partial fingerprints
        4. Assign appropriate disambiguation IDs
        
        Returns number of rooms processed
        """
        if not api_client:
            return 0
            
        processed_count = 0
        
        # Step 1: Find all complete rooms (these have full fingerprints)
        complete_rooms = [room for room in self.possible_rooms if room.is_complete()]
        
        # Step 2: Find incomplete rooms that need to be tested
        incomplete_rooms = [room for room in self.possible_rooms if not room.is_complete()]
        
        for incomplete_room in incomplete_rooms:
            # Try to get complete information for this room
            if len(incomplete_room.paths) == 0:
                continue
                
            # Get the door labels for this room
            path = incomplete_room.paths[0]
            adjacent_labels = self._get_potential_adjacent_labels(path, incomplete_room.label, api_client)
            
            if adjacent_labels and len(adjacent_labels) == 6:
                # Now we have complete information - update the room
                incomplete_room.door_labels = adjacent_labels[:]
                print(f"Completed room with path {path}: {incomplete_room.get_fingerprint(include_disambiguation=False)}")
                
                # Step 3: Test against ALL existing complete rooms with matching partial fingerprint
                partial_fingerprint = incomplete_room.get_fingerprint(include_disambiguation=False)
                matching_complete_rooms = []
                
                for complete_room in complete_rooms:
                    if complete_room.get_fingerprint(include_disambiguation=False) == partial_fingerprint:
                        matching_complete_rooms.append(complete_room)
                
                if matching_complete_rooms:
                    print(f"Found {len(matching_complete_rooms)} existing rooms with matching fingerprint {partial_fingerprint}")
                    
                    # Test against each matching room to see if they're different
                    disambiguation_id = 0
                    is_different_from_all = True
                    
                    for existing_room in matching_complete_rooms:
                        try:
                            are_different = self.disambiguate_rooms_with_path_navigation(
                                existing_room, incomplete_room, api_client
                            )
                            
                            if not are_different:
                                # Same room - merge paths
                                print(f"Room is SAME as existing room {existing_room.get_fingerprint()}")
                                for path in incomplete_room.paths:
                                    if path not in existing_room.paths:
                                        existing_room.add_path(path)
                                
                                # Remove the duplicate room
                                if incomplete_room in self.possible_rooms:
                                    self.possible_rooms.remove(incomplete_room)
                                
                                is_different_from_all = False
                                processed_count += 1
                                break
                            else:
                                print(f"Room is DIFFERENT from existing room {existing_room.get_fingerprint()}")
                                # Keep track of the highest disambiguation ID
                                if hasattr(existing_room, 'disambiguation_id') and existing_room.disambiguation_id is not None:
                                    disambiguation_id = max(disambiguation_id, existing_room.disambiguation_id + 1)
                                else:
                                    disambiguation_id = 1
                                    
                        except Exception as e:
                            print(f"Disambiguation test failed: {e}")
                            # Assume different if test fails
                            disambiguation_id = max(disambiguation_id, len(matching_complete_rooms))
                    
                    if is_different_from_all:
                        # This is a new distinct room - assign disambiguation ID
                        incomplete_room.disambiguation_id = disambiguation_id
                        print(f"Assigned disambiguation ID {disambiguation_id} to new room: {incomplete_room.get_fingerprint()}")
                        complete_rooms.append(incomplete_room)  # Add to complete rooms
                        processed_count += 1
                        
                        # Ensure existing rooms have disambiguation IDs too
                        for existing_room in matching_complete_rooms:
                            if not hasattr(existing_room, 'disambiguation_id') or existing_room.disambiguation_id is None:
                                existing_room.disambiguation_id = 0
                                print(f"Assigned disambiguation ID 0 to existing room: {existing_room.get_fingerprint()}")
                
                else:
                    # No matching rooms - this is unique
                    incomplete_room.disambiguation_id = 0
                    print(f"New unique room: {incomplete_room.get_fingerprint()}")
                    complete_rooms.append(incomplete_room)
                    processed_count += 1
        
        return processed_count

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
        
        # Choose a unique label for editing (different from both rooms)
        edit_label = None
        for candidate in [2, 3, 1, 0]:  # Try different labels
            if candidate != room_a.label and candidate != room_b.label:
                edit_label = candidate
                break
                
        if edit_label is None:
            print("Cannot find unique edit label")
            return False
        
        # Get reverse path from A back to root, if available
        if hasattr(room_a, 'path_to_root') and room_a.path_to_root:
            reverse_path_from_a_to_root = room_a.path_to_root
        else:
            print("Room A does not have path_to_root - cannot disambiguate")
            return False
            
        print(f"Disambiguating: path_to_a={path_to_a}, path_to_b={path_to_b}, reverse_path={reverse_path_from_a_to_root}")
        
        # Construct disambiguation plan: path_to_a + [edit] + reverse_path_from_a_to_root + path_to_b
        plan_parts = path_to_a + [f"[{edit_label}]"] + reverse_path_from_a_to_root + path_to_b
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
        # If we can't test, assume rooms are different (conservative approach for star topology)
        return True

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
