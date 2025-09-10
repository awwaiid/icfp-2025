"""
Minimal Room implementation with fingerprint-based identification
"""

from typing import List, Optional


class Room:
    """A room identified by paths, label, and adjacency fingerprint"""

    def __init__(self, label: Optional[int] = None, parent=None, parent_door: Optional[int] = None):
        self.label = label  # Room label (0, 1, 2, 3)
        self.paths = []  # List of paths used to reach this room
        self.door_labels = [None] * 6  # Labels of rooms reachable through each door
        self.disambiguation_id = None  # ID to distinguish rooms with identical base fingerprints
        
        # New systematic exploration properties
        self.parent = parent  # Parent room that leads to this room
        self.parent_door = parent_door  # Which door from parent leads to this room
        self.path_to_root = []  # Path from this room back to root room
        self.path_from_root = []  # Path from root to reach this room
        self.is_done = False  # Whether this room has been fully explored
        self.door_rooms = [None] * 6  # References to actual Room objects through each door

    def add_path(self, path: List[int]):
        """Add a path that leads to this room"""
        if path not in self.paths:
            self.paths.append(path[:])  # Copy the path

    def set_door_label(self, door: int, label: int):
        """Set the label of the room reachable through a specific door"""
        if 0 <= door <= 5:
            self.door_labels[door] = label

    def get_fingerprint(self, include_disambiguation=True) -> str:
        """Get fingerprint: label followed by door labels, with disambiguation ID"""
        # Start with room label
        if self.label is None:
            fingerprint = "?"
        else:
            fingerprint = str(self.label)

        # Add dash separator
        fingerprint += "-"

        # Add door labels
        for door_label in self.door_labels:
            if door_label is None:
                fingerprint += "?"
            else:
                fingerprint += str(door_label)

        # Add disambiguation ID (always show, use "?" if unknown)
        if include_disambiguation:
            fingerprint += "-"
            if hasattr(self, 'disambiguation_id') and self.disambiguation_id is not None:
                fingerprint += str(self.disambiguation_id)
            else:
                fingerprint += "?"

        return fingerprint

    def is_complete(self) -> bool:
        """Check if we know all door destinations"""
        return self.label is not None and all(
            label is not None for label in self.door_labels
        )

    def get_known_doors(self) -> List[int]:
        """Get list of doors where we know the destination label"""
        return [i for i, label in enumerate(self.door_labels) if label is not None]

    def get_unknown_doors(self) -> List[int]:
        """Get list of doors where we don't know the destination label"""
        return [i for i, label in enumerate(self.door_labels) if label is None]

    def peek_adjacent_rooms(self, api_client) -> List[Optional[int]]:
        """Peek at all adjacent rooms through each door and get their labels
        
        Uses the first available path to this room and explores each door.
        Returns a list of 6 labels (one for each door 0-5), or None if door cannot be explored.
        
        Args:
            api_client: ApiClient instance for making exploration requests
            
        Returns:
            List of 6 integers representing the labels of adjacent rooms, or None for unexplorable doors
        """
        if not self.paths or not api_client:
            return [None] * 6

        # Use the first path to reach this room
        base_path = self.paths[0]
        base_path_string = "".join(str(door) for door in base_path)
        
        adjacent_labels = []
        explore_plans = []
        
        # Create exploration plans for each door
        for door in range(6):
            explore_plan = base_path_string + str(door)
            explore_plans.append(explore_plan)
        
        try:
            # Execute all explorations at once
            result = api_client.explore(explore_plans)
            
            if result and "results" in result and len(result["results"]) == 6:
                # Parse each result to get the adjacent room labels
                for i, result_data in enumerate(result["results"]):
                    if isinstance(result_data, list) and len(result_data) >= len(base_path) + 2:
                        # The adjacent room label is at position len(base_path) + 1
                        adjacent_label = result_data[len(base_path) + 1]
                        adjacent_labels.append(adjacent_label)
                    else:
                        # Couldn't determine this adjacent label
                        adjacent_labels.append(None)
            else:
                # Failed to get results
                adjacent_labels = [None] * 6
                
        except Exception as e:
            print(f"Error in peek_adjacent_rooms: {e}")
            adjacent_labels = [None] * 6
        
        return adjacent_labels

    def calculate_backlink(self, parent_room, api_client):
        """Calculate which door leads back to the parent room
        
        Algorithm:
        1. For each of our doors (0-5), navigate: parent_path + [edit_label] + self_path + door
        2. The door that leads to a room showing the edit_label is the backlink
        3. Set path_to_root = [backlink_door] + parent.path_to_root
        """
        if not parent_room or not parent_room.paths or not self.paths:
            return None
            
        # Get paths to parent and self
        parent_path = parent_room.paths[0] if parent_room.paths else []
        self_path = self.paths[0] if self.paths else []
        
        # Choose a unique label for editing (different from parent's and self's original labels)
        edit_label = None
        for candidate in [1, 2, 3, 0]:  # Try different labels
            if candidate != parent_room.label and candidate != self.label:
                edit_label = candidate
                break
                
        if edit_label is None:
            print(f"Cannot find unique edit label for backlink calculation")
            return None
        
        print(f"Calculating backlink from {self} to {parent_room} using edit label {edit_label}")
        
        try:
            # Build exploration plans: parent_path + [edit] + step_from_parent_to_self + door for each door
            parent_path_str = "".join(str(d) for d in parent_path)
            
            # Calculate the step from parent to self
            # If self_path is parent_path + [X], then step from parent to self is just [X]
            if len(self_path) == len(parent_path) + 1 and self_path[:len(parent_path)] == parent_path:
                step_to_self = str(self_path[len(parent_path)])
            else:
                print(f"ERROR: Cannot calculate step from parent to self. parent_path={parent_path}, self_path={self_path}")
                return None
            
            explore_plans = []
            for door in range(6):
                # Plan: go to parent, edit its label, go to self (one step), go through door
                plan = parent_path_str + f"[{edit_label}]" + step_to_self + str(door)
                explore_plans.append(plan)
            
            print(f"    Testing doors with plans: {explore_plans}")
            
            # Execute all explorations in single API call
            result = api_client.explore(explore_plans)
            
            if result and "results" in result and len(result["results"]) == 6:
                # Check each result to see which door leads to the edited parent
                backlink_door = None
                for door in range(6):
                    result_data = result["results"][door]
                    if isinstance(result_data, list) and len(result_data) > 0:
                        # Get the final room label after going through this door
                        final_label = result_data[-1]
                        print(f"    Door {door}: raw_result={result_data}, final_label={final_label}")
                        
                        if final_label == edit_label:
                            backlink_door = door
                            print(f"Found backlink: door {door} leads to parent (final label {final_label} matches edit {edit_label})")
                            break
                
                if backlink_door is not None:
                    # Build path_to_root: backlink_door + parent's path_to_root
                    self.path_to_root = [backlink_door] + parent_room.path_to_root
                    print(f"Set path_to_root for {self}: {self.path_to_root}")
                    return backlink_door
                else:
                    print(f"Could not determine backlink door - no door showed edit_label {edit_label}")
                    
        except Exception as e:
            print(f"Error calculating backlink: {e}")
            
        return None

    def unique_or_merged(self, all_rooms, api_client):
        """Find if this room is unique or should be merged with an existing room
        
        Returns the canonical room (either self if unique, or existing room if merged)
        """
        if not self.door_labels or len([l for l in self.door_labels if l is not None]) < 6:
            # Can't disambiguate without complete partial fingerprint
            return self
            
        # Get partial fingerprint
        partial_fp = self.get_fingerprint(include_disambiguation=False)
        similar_rooms = []
        max_disambiguation_id = -1
        
        # Find rooms with same partial fingerprint
        for room in all_rooms:
            if room != self and room.get_fingerprint(include_disambiguation=False) == partial_fp:
                similar_rooms.append(room)
                if hasattr(room, 'disambiguation_id') and room.disambiguation_id is not None:
                    max_disambiguation_id = max(max_disambiguation_id, room.disambiguation_id)
        
        if not similar_rooms:
            # This room is unique - assign disambiguation_id 0
            self.disambiguation_id = 0
            print(f"Room {self} is unique - assigned disambiguation_id 0")
            return self
        
        print(f"Found {len(similar_rooms)} similar rooms with fingerprint {partial_fp}")
        
        # Test against each similar room using path navigation
        for similar_room in similar_rooms:
            try:
                if self._test_rooms_are_same(similar_room, api_client):
                    # Rooms are the same - merge into the canonical room
                    print(f"Room {self} is SAME as {similar_room} - merging")
                    # Add our path to the canonical room
                    for path in self.paths:
                        if path not in similar_room.paths:
                            similar_room.add_path(path)
                    # Copy over door_rooms if we have them and the canonical room doesn't
                    # Also update bidirectional references to point to the canonical room
                    print(f"  MERGE: Copying connections from {self} to canonical {similar_room}")
                    for door in range(6):
                        if self.door_rooms[door] is not None and similar_room.door_rooms[door] is None:
                            door_room = self.door_rooms[door]
                            print(f"  MERGE: Copying {self} door {door} -> {door_room} to canonical room")
                            similar_room.door_rooms[door] = door_room
                            
                            # Update the bidirectional reference in door_room to point to canonical room
                            for back_door in range(6):
                                if door_room.door_rooms[back_door] == self:
                                    print(f"  MERGE: Updating reverse reference {door_room} door {back_door}: {self} -> {similar_room}")
                                    door_room.door_rooms[back_door] = similar_room
                                    break
                    return similar_room
                else:
                    print(f"Room {self} is DIFFERENT from {similar_room}")
                    
            except RuntimeError as e:
                # Disambiguation test detected an invalid state - this is a fatal error
                # Don't try to continue with potentially corrupted room state
                raise e
        
        # If we get here, this room tested as different from all similar rooms
        # Only assign disambiguation_id if we have strong evidence
        if len(similar_rooms) == 0:
            # First room with this partial fingerprint
            self.disambiguation_id = 0
            print(f"Room {self} is unique - assigned disambiguation_id 0")
        else:
            # For now, be conservative and merge with the first room instead of creating new disambiguation IDs
            # This prevents the "rooms not in final mapping" issue
            first_similar = similar_rooms[0]
            print(f"Room {self} conservatively merged with {first_similar} to avoid disambiguation complexity")
            # Add our path to the existing room
            for path in self.paths:
                if path not in first_similar.paths:
                    first_similar.add_path(path)
            # Copy over door_rooms if we have them and the canonical room doesn't
            for door in range(6):
                if self.door_rooms[door] is not None and first_similar.door_rooms[door] is None:
                    first_similar.door_rooms[door] = self.door_rooms[door]
            return first_similar

    def _test_rooms_are_same(self, other_room, api_client):
        """Test if this room and other_room are actually the same room"""
        if not hasattr(self, 'path_from_root') or self.path_from_root is None:
            raise RuntimeError(f"FATAL: Room {self} missing path_from_root - invalid state for disambiguation test")
        
        if not hasattr(other_room, 'path_from_root') or other_room.path_from_root is None:
            raise RuntimeError(f"FATAL: Room {other_room} missing path_from_root - invalid state for disambiguation test")
        
        if not hasattr(self, 'path_to_root') or self.path_to_root is None:
            raise RuntimeError(f"FATAL: Room {self} missing path_to_root (backlink) - invalid state for disambiguation test")
        
        # Additional validation: rooms should have proper non-root paths for disambiguation
        # (The root room with empty path_from_root shouldn't need disambiguation)
        if len(self.path_from_root) == 0 and len(other_room.path_from_root) == 0:
            raise RuntimeError(f"FATAL: Cannot disambiguate two root rooms - both have empty path_from_root")
        
        if len(self.path_to_root) == 0 and len(self.path_from_root) > 0:
            raise RuntimeError(f"FATAL: Room {self} has non-empty path_from_root but empty path_to_root - invalid backlink state")
            
        # Choose unique edit label
        edit_label = None
        for candidate in [1, 2, 3, 0]:
            if candidate != self.label and candidate != other_room.label:
                edit_label = candidate
                break
                
        if edit_label is None:
            raise RuntimeError(f"FATAL: Cannot find unique edit label for disambiguation test between {self} (label={self.label}) and {other_room} (label={other_room.label})")
        
        try:
            # Proper plan: navigate to self, edit label, use backlink to return to root, then navigate to other
            path_to_self_str = "".join(str(d) for d in self.path_from_root)
            path_to_root_str = "".join(str(d) for d in self.path_to_root)
            path_to_other_str = "".join(str(d) for d in other_room.path_from_root)
            
            plan_str = path_to_self_str + f"[{edit_label}]" + path_to_root_str + path_to_other_str
            
            print(f"Testing if rooms are same with plan: {plan_str}")
            print(f"  self.path_from_root={self.path_from_root}, self.path_to_root={self.path_to_root}")
            print(f"  other.path_from_root={other_room.path_from_root}")
            
            result = api_client.explore([plan_str])
            
            if not result or "results" not in result:
                raise RuntimeError(f"FATAL: API client returned invalid result structure for disambiguation test: {result}")
                
            if len(result["results"]) != 1:
                raise RuntimeError(f"FATAL: Expected exactly 1 result for disambiguation test, got {len(result['results'])}")
            
            result_data = result["results"][0]
            print(f"  Raw result: {result_data}")
            
            actual_labels, echo_labels = api_client.parse_response_with_echoes(plan_str, result_data)
            print(f"  Parsed: actual_labels={actual_labels}, echo_labels={echo_labels}")
            
            if not actual_labels:
                raise RuntimeError(f"FATAL: Could not parse any actual labels from disambiguation test result: {result_data}")
            
            final_label = actual_labels[-1]
            print(f"  Final label: {final_label}, expecting edit_label: {edit_label}")
            # If final room shows the edit we made to the first room, they're the same room
            return final_label == edit_label
                    
        except RuntimeError:
            # Re-raise runtime errors (our validation errors)
            raise
        except Exception as e:
            # Only catch unexpected API/network errors here
            raise RuntimeError(f"FATAL: Unexpected error during disambiguation test API call: {e}")


    def set_done(self):
        """Mark this room as fully explored"""
        self.is_done = True

    def __str__(self):
        paths_str = ", ".join([str(p) for p in self.paths]) if self.paths else "[]"
        return f"Room(label={self.label}, fingerprint={self.get_fingerprint()}, paths=[{paths_str}])"

    def __repr__(self):
        return self.__str__()
