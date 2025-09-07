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
        starting_room = self.room_manager.find_or_create_room_for_path(
            [], starting_label, self.api_client
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
                
                # Check if this is a new connection (door wasn't known before)
                was_door_unknown = current_room.door_labels[door] is None
                current_room.set_door_label(door, destination_label)

                # Find or create the destination room
                path_to_destination = path[: i + 1]
                print(
                    f"  Looking for destination room with path={path_to_destination} and label={destination_label}"
                )
                destination_room = self.room_manager.find_or_create_room_for_path(
                    path_to_destination, destination_label, self.api_client
                )
                print(f"  Using destination room: {destination_room}")
                
                # If this was a new connection and both rooms exist, discover the return door
                if was_door_unknown and current_room.is_complete() and len(destination_room.paths) == 1:
                    print(f"  Triggering return door discovery from {destination_room.label} back to {current_room.label}")
                    try:
                        self.discover_return_door(current_room, destination_room, door)
                    except Exception as e:
                        print(f"  Return door discovery failed: {e}")

                current_room = destination_room

    def populate_explored_paths_from_observations(self):
        """Populate explored paths from existing observations"""
        self.explored_paths.clear()
        for obs in self.observations:
            path_tuple = tuple(obs["plan"])
            self.explored_paths.add(path_tuple)
        print(f"Populated {len(self.explored_paths)} explored paths from observations")

    def bootstrap(self, problem_name: str):
        """Minimal bootstrap: just create the starting room and prepare for exploration"""
        print("=== Minimal Bootstrap ===")

        # Select problem (uncomment if needed)
        # self.select_problem(problem_name)

        # Create the starting room with no door information
        # The main exploration loop will handle discovering all door connections
        starting_room = self.room_manager.find_or_create_room_for_path(
            [], 0, self.api_client  # Assume label 0 for starting room
        )
        print(f"Created starting room: {starting_room}")
        print(f"Bootstrap complete - starting room ready for exploration")
        
        self.print_fingerprints()

    def _consolidate_obvious_duplicates(self):
        """Consolidate partial rooms that are provably the same based on path tracing
        
        NOTE: Path tracing has been removed. Room deduplication now relies entirely on
        navigation and label editing during the disambiguation phase.
        """
        pass

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
            
            # Since disambiguation now happens during room creation, we don't need aggressive cleanup

        # After all exploration, final check for and remove duplicates (with disambiguation)
        removed = self.room_manager.remove_duplicate_rooms(self.api_client)
        if removed > 0:
            print("Updated room list after removing duplicates:")
            self.print_fingerprints()

        # DISABLED: Clean up redundant partial rooms that can be traced to complete rooms
        # This was too aggressive for star layout - peripheral rooms were being incorrectly merged
        # cleaned_partial = self.room_manager.cleanup_all_traceable_partial_rooms()
        # if cleaned_partial > 0:
        #     print(f"Cleaned up {cleaned_partial} redundant partial rooms")

        # Check if we can do aggressive cleanup now that we might have complete coverage
        cleaned = self.room_manager.cleanup_all_partial_rooms_when_complete()
        if cleaned > 0:
            print("Final clean room list:")
            self.print_fingerprints()

    def explore_with_connection_queue(self, max_iterations: int = 1000):
        """Queue-based exploration that systematically completes room connections
        
        Algorithm:
        1. Start with incomplete rooms in queue
        2. For each room: use peek_adjacent_rooms() to get complete partial fingerprint
        3. Update room's door_labels with the adjacent room labels
        4. Add all connected rooms to queue if not already verified
        5. Use disambiguation for rooms with identical partial fingerprints
        6. Continue until queue is empty or we have enough rooms
        """
        from collections import deque
        
        print("=== Queue-Based Connection Exploration ===")
        
        # Initialize queue with incomplete rooms
        room_queue = deque()
        processed_rooms = set()  # Track rooms we've already processed
        
        # Add all existing incomplete rooms to queue
        incomplete_rooms = self.room_manager.get_incomplete_rooms()
        for room in incomplete_rooms:
            if room.paths:  # Only queue rooms with paths
                room_queue.append(room)
                print(f"Queued incomplete room: {room}")
        
        # If no incomplete rooms, try to add some complete rooms to verify connections
        if not room_queue:
            complete_rooms = self.room_manager.get_complete_rooms()
            for room in complete_rooms[:3]:  # Add first few complete rooms
                room_queue.append(room)
                print(f"Queued complete room for connection verification: {room}")
        
        iteration = 0
        while room_queue and iteration < max_iterations:
            iteration += 1
            current_room = room_queue.popleft()
            
            # Skip if we've already processed this room
            room_key = (tuple(current_room.paths[0]) if current_room.paths else (), current_room.label)
            if room_key in processed_rooms:
                continue
                
            processed_rooms.add(room_key)
            print(f"\n--- Iteration {iteration}: Processing room {current_room} ---")
            
            # Step 1: Complete this room's partial fingerprint using peek_adjacent_rooms
            if not current_room.is_complete():
                print("Getting complete adjacent room information...")
                adjacent_labels = current_room.peek_adjacent_rooms(self.api_client)
                
                if adjacent_labels and len(adjacent_labels) == 6:
                    # Update room's door labels
                    current_room.door_labels = adjacent_labels[:]
                    print(f"Updated room partial fingerprint: {current_room.get_fingerprint(include_disambiguation=False)}")
                    
                    # Step 2: Check for disambiguation needed
                    self._handle_room_disambiguation(current_room)
                    
                else:
                    print(f"Failed to get adjacent room labels for {current_room}")
                    continue
            
            # Step 3: Add connected rooms to queue if not already processed
            if current_room.is_complete():
                print("Room is complete - checking connections...")
                for door, adjacent_label in enumerate(current_room.door_labels):
                    if adjacent_label is not None:
                        # Find or create rooms with this label that we can reach
                        connected_rooms = self._find_or_create_connected_rooms(current_room, door, adjacent_label)
                        
                        for connected_room in connected_rooms:
                            connected_key = (tuple(connected_room.paths[0]) if connected_room.paths else (), connected_room.label)
                            if connected_key not in processed_rooms and connected_room not in room_queue:
                                room_queue.append(connected_room)
                                print(f"  Queued connected room via door {door}: {connected_room}")
            
            # Step 4: Check if we have enough complete rooms
            complete_rooms = self.room_manager.get_complete_rooms()
            unique_complete_count = len(set(room.get_fingerprint() for room in complete_rooms))
            print(f"Progress: {unique_complete_count}/{self.room_count} unique complete rooms")
            
            if unique_complete_count >= self.room_count:
                print(f"🎉 Target reached! Found {unique_complete_count} complete rooms")
                break
                
            # Step 5: Remove duplicates periodically
            if iteration % 5 == 0:
                removed = self.room_manager.remove_duplicate_rooms(self.api_client)
                if removed > 0:
                    print(f"Removed {removed} duplicate rooms during processing")
        
        print(f"\nQueue-based exploration completed after {iteration} iterations")
        print(f"Rooms processed: {len(processed_rooms)}")
        print(f"Queue remaining: {len(room_queue)}")
        
        return iteration

    def _handle_room_disambiguation(self, room):
        """Handle disambiguation for a room with complete partial fingerprint"""
        base_fp = room.get_fingerprint(include_disambiguation=False)
        
        # Find other complete rooms with same base fingerprint
        matching_rooms = []
        for other_room in self.room_manager.get_complete_rooms():
            if other_room != room and other_room.get_fingerprint(include_disambiguation=False) == base_fp:
                matching_rooms.append(other_room)
        
        if matching_rooms:
            print(f"Found {len(matching_rooms)} rooms with same base fingerprint - need disambiguation")
            
            # Use existing disambiguation logic
            for other_room in matching_rooms:
                if hasattr(other_room, 'disambiguation_id') and other_room.disambiguation_id is not None:
                    continue  # Already disambiguated
                    
                try:
                    are_different = self.room_manager.disambiguate_rooms_with_path_navigation(
                        room, other_room, self.api_client
                    )
                    
                    if are_different:
                        # Assign disambiguation IDs
                        if not hasattr(room, 'disambiguation_id') or room.disambiguation_id is None:
                            room.disambiguation_id = 0
                        if not hasattr(other_room, 'disambiguation_id') or other_room.disambiguation_id is None:
                            other_room.disambiguation_id = 1
                        print(f"Rooms confirmed different - assigned IDs: {room.get_fingerprint()}, {other_room.get_fingerprint()}")
                    else:
                        # Same room - merge paths
                        print(f"Rooms confirmed same - merging paths")
                        for path in other_room.paths:
                            if path not in room.paths:
                                room.add_path(path)
                        if other_room in self.room_manager.possible_rooms:
                            self.room_manager.possible_rooms.remove(other_room)
                            
                except Exception as e:
                    print(f"Disambiguation failed: {e} - assuming different")
                    if not hasattr(room, 'disambiguation_id') or room.disambiguation_id is None:
                        room.disambiguation_id = 0
                    if not hasattr(other_room, 'disambiguation_id') or other_room.disambiguation_id is None:
                        other_room.disambiguation_id = len(matching_rooms)
        else:
            # Unique room - assign ID 0
            if not hasattr(room, 'disambiguation_id') or room.disambiguation_id is None:
                room.disambiguation_id = 0

    def _find_or_create_connected_rooms(self, from_room, door, target_label):
        """Find or create rooms that are connected through a specific door"""
        if not from_room.paths:
            return []
            
        # Create path to reach the connected room
        base_path = from_room.paths[0]
        connected_path = base_path + [door]
        
        # Look for existing rooms with this path and label
        existing_rooms = []
        for room in self.room_manager.get_all_rooms():
            if room.label == target_label and connected_path in room.paths:
                existing_rooms.append(room)
        
        if existing_rooms:
            return existing_rooms
        
        # Create new room if none exists
        new_room = self.room_manager.find_or_create_room_for_path(connected_path, target_label, self.api_client)
        return [new_room] if new_room else []

    def explore_systematic(self, max_iterations: int = 1000):
        """Systematic exploration algorithm following the pseudocode exactly
        
        Algorithm:
        1. Bootstrap by creating root room with disambiguation_id = 0
        2. Queue-based exploration: process each room completely before moving to next
        3. For each room: create child rooms through each door, with disambiguation
        4. Calculate backlinks and build proper parent-child relationships
        5. Continue until queue empty or target room count reached
        """
        from collections import deque
        
        print("=== Systematic Exploration Algorithm ===")
        
        # First, bootstrap by creating root room
        all_rooms = []  # Global room registry
        
        # Get the starting room (should already exist from bootstrap)
        existing_rooms = self.room_manager.get_all_rooms()
        if not existing_rooms:
            print("No existing rooms found - need to bootstrap first")
            return 0
            
        root_room = existing_rooms[0]  # Use first room as root
        print(f"Using root room: {root_room}")
        
        # Make sure root room has complete partial fingerprint
        if not root_room.is_complete():
            print("Completing root room partial fingerprint...")
            adjacent_labels = root_room.peek_adjacent_rooms(self.api_client)
            if adjacent_labels and len(adjacent_labels) == 6:
                root_room.door_labels = adjacent_labels[:]
                print(f"Root room completed: {root_room.get_fingerprint(include_disambiguation=False)}")
            else:
                print("Failed to complete root room")
                return 0
        
        # Set root room properties
        root_room.disambiguation_id = 0  # Root is official immediately
        root_room.path_to_root = []  # Root has empty path to self
        root_room.path_from_root = []  # Root is reached by empty path from self
        all_rooms.append(root_room)
        
        # Initialize exploration queue
        rooms_to_explore_queue = deque([root_room])
        
        iteration = 0
        while rooms_to_explore_queue and iteration < max_iterations:
            iteration += 1
            current_room = rooms_to_explore_queue.popleft()
            
            print(f"\n--- Systematic Iteration {iteration}: Exploring {current_room} ---")
            
            # Skip if room is already done
            if current_room.is_done:
                print("Room already done - skipping")
                continue
            
            # Process each door (0-5)
            for door in range(6):
                door_label = current_room.door_labels[door]
                print(f"Processing door {door} -> label {door_label}")
                
                # Create path to child room
                if current_room.paths:
                    child_path = current_room.paths[0] + [door]
                else:
                    child_path = [door]
                
                # Create child room
                child_room = Room(label=door_label, parent=current_room, parent_door=door)
                child_room.add_path(child_path)
                
                # Set path_from_root: parent's path_from_root + door
                child_room.path_from_root = current_room.path_from_root + [door]
                
                # Get complete partial fingerprint for child
                print(f"  Getting partial fingerprint for child room...")
                adjacent_labels = child_room.peek_adjacent_rooms(self.api_client)
                
                if adjacent_labels and len(adjacent_labels) == 6:
                    child_room.door_labels = adjacent_labels[:]
                    print(f"  Child partial fingerprint: {child_room.get_fingerprint(include_disambiguation=False)}")
                    
                    # Calculate backlink to parent
                    print(f"  Calculating backlink to parent...")
                    backlink_door = child_room.calculate_backlink(current_room, self.api_client)
                    if backlink_door is not None:
                        print(f"  Backlink calculated: door {backlink_door} leads to parent")
                    
                    # Disambiguate and get canonical room
                    canonical_room = child_room.unique_or_merged(all_rooms, self.api_client)
                    
                    # Set door reference in parent
                    current_room.door_rooms[door] = canonical_room
                    
                    # Add to global registry if it's a new room
                    if canonical_room not in all_rooms:
                        all_rooms.append(canonical_room)
                        print(f"  Added new room to registry: {canonical_room.get_fingerprint()}")
                    
                    # Queue for exploration if not done
                    if not canonical_room.is_done:
                        rooms_to_explore_queue.append(canonical_room)
                        print(f"  Queued child room for exploration")
                    
                else:
                    print(f"  Failed to get complete partial fingerprint for child")
            
            # Mark current room as done
            current_room.set_done()
            print(f"Marked {current_room} as done")
            
            # Check progress
            complete_rooms = [r for r in all_rooms if r.is_complete() and hasattr(r, 'disambiguation_id') and r.disambiguation_id is not None]
            print(f"Progress: {len(complete_rooms)}/{self.room_count} complete rooms")
            
            if len(complete_rooms) >= self.room_count:
                print(f"🎉 Target reached! Found {len(complete_rooms)} complete rooms")
                break
        
        print(f"\nSystematic exploration completed after {iteration} iterations")
        print(f"Total rooms in registry: {len(all_rooms)}")
        print(f"Rooms remaining in queue: {len(rooms_to_explore_queue)}")
        
        # Update the room manager with our systematic rooms
        self.room_manager.possible_rooms = all_rooms
        
        # Connection mappings are handled by get_systematic_connections method
        
        return iteration

    def explore_until_complete(self, max_iterations: int = 10000):
        """Keep exploring incomplete rooms until all are complete or max iterations reached"""
        print("=== Exploring Until Complete ===")

        # Quick check: if we have complete coverage, exit immediately
        complete_rooms = self.room_manager.get_complete_rooms()
        unique_complete_count = len(set(room.get_fingerprint() for room in complete_rooms))
        print(f"Initial check: {unique_complete_count} unique complete rooms, target={self.room_count}")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Early termination check: if we have enough complete rooms, stop
            complete_rooms = self.room_manager.get_complete_rooms()
            unique_complete_count = len(complete_rooms)
            
            if unique_complete_count >= self.room_count:
                print(f"🎉 Found {unique_complete_count} complete rooms - target reached!")
                break

            # Check if we have any incomplete rooms or unknown connections
            incomplete_rooms = self.room_manager.get_incomplete_rooms()

            # Also check for unknown connections in complete rooms
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
                # Check if we've found the expected number of rooms
                unique_rooms = self.room_manager.get_complete_rooms()
                unique_count = len(unique_rooms)
                
                if unique_count >= self.room_count:
                    print("🎉 All rooms complete and all connections verified!")
                    break
                else:
                    print(f"⚠️ No more exploration work but only found {unique_count}/{self.room_count} unique rooms")
                    print("This may indicate the exploration strategy missed some rooms")
                    print("Let's try more aggressive exploration...")
                    
                    # Try to find more rooms by exploring deeper paths
                    # Look for any doors that haven't been fully explored
                    additional_work_found = False
                    
                    for room in unique_rooms:
                        for door_idx, connection_id in enumerate(self.room_manager.get_absolute_connections(room)):
                            if connection_id is not None:
                                dest_room = None
                                for r in unique_rooms:
                                    if self.room_manager.get_absolute_room_mapping().get(r.get_fingerprint()) == connection_id:
                                        dest_room = r
                                        break
                                
                                if dest_room:
                                    # Try deeper exploration from this connection
                                    current_paths = [path for path in room.paths if len(path) <= 2]
                                    if current_paths:
                                        # Explore one more level deep
                                        deeper_path = current_paths[0] + [door_idx, 0]  # Add door and first exploration
                                        try:
                                            print(f"Trying deeper exploration: {deeper_path}")
                                            self.explore([[deeper_path]])
                                            additional_work_found = True
                                            break
                                        except:
                                            pass
                    
                    if not additional_work_found:
                        print("No additional exploration opportunities found")
                        break

            print(
                f"Work remaining: {len(incomplete_rooms)} incomplete rooms, {len(unknown_connections)} unknown connections, {len(missing_connections)} missing connections, {len(partial_explorations)} partial explorations"
            )

            # Do one round of exploration
            self.explore_incomplete_rooms()

            # Apply the systematic room disambiguation process
            processed_count = self.room_manager.systematic_room_disambiguation(self.api_client)
            if processed_count > 0:
                print(f"Systematically processed {processed_count} rooms for disambiguation")
            
            # Consolidate destination paths from newly completed rooms
            consolidated_count = self.room_manager.consolidate_destination_paths()
            if consolidated_count > 0:
                print(f"Consolidated {consolidated_count} destination paths")

            # Also try to remove duplicate rooms using navigation-based testing (backup)
            removed = self.room_manager.remove_duplicate_rooms(self.api_client)
            if removed > 0:
                print(f"Removed {removed} duplicate rooms via navigation testing")

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
                absolute_id = self.room_manager.get_absolute_room_mapping().get(
                    fingerprint, "?"
                )
                known_rooms.add((absolute_id, room.label))

        print(f"All known complete rooms ({len(known_rooms)}):")
        for abs_id, room_label in sorted(known_rooms):
            # Find the room with this absolute ID
            for room in all_rooms:
                if room.is_complete():
                    fp = room.get_fingerprint()
                    if self.room_manager.get_absolute_room_mapping().get(fp) == abs_id:
                        connections = self.room_manager.get_absolute_connections(room)
                        verified_count = sum(
                            1 for conn in connections if conn is not None
                        )
                        status = (
                            "COMPLETE"
                            if verified_count == 6
                            else f"INCOMPLETE ({verified_count}/6)"
                        )
                        print(f"  Room {abs_id}(L{room_label}): {status}")
                        break

        incomplete_rooms = self.room_manager.get_incomplete_rooms()
        print(f"\nIncomplete rooms ({len(incomplete_rooms)}): (fingerprints not shown)")

        # Show what exploration options we have
        exploration_batch = self.exploration_strategy.get_next_exploration_batch()
        if exploration_batch:
            print(
                f"\nNext exploration: {exploration_batch['type']} (priority {exploration_batch['priority']})"
            )
        else:
            print("\nNo more exploration needed!")

    def discover_return_door(self, from_room: Room, to_room: Room, forward_door: int):
        """Discover which door in to_room leads back to from_room using label editing
        
        Process:
        1. Modify from_room's label to a unique temporary value
        2. From to_room, check all 6 doors to see which one's destination changed
        3. That door leads back to from_room - record it in to_room.door_labels
        """
        if not from_room.paths or not to_room.paths:
            print(f"Cannot discover return door: missing paths")
            return
            
        # Choose a temporary label different from both rooms' current labels
        temp_label = None
        for candidate in [0, 1, 2, 3]:
            if candidate != from_room.label and candidate != to_room.label:
                temp_label = candidate
                break
                
        if temp_label is None:
            print("Cannot find unique temporary label for return door discovery")
            return
            
        print(f"Discovering return door from {to_room.label} back to {from_room.label}")
        print(f"  Using temporary label {temp_label} for room {from_room.label}")
        
        # Get base path to from_room (we'll modify its label)
        from_room_path = from_room.paths[0]  # Use first path to from_room
        to_room_path = to_room.paths[0]      # Use first path to to_room
        
        # Create exploration plans to check each door from to_room after modifying from_room's label
        # Plan format: path_to_from_room + "[temp_label]" + path_from_from_to_to + door_to_check
        
        # First, we need to navigate to from_room and change its label, then get to to_room
        if not to_room_path or to_room_path[-1] != forward_door:
            print(f"Warning: Expected to_room path to end with forward door {forward_door}")
            
        exploration_plans = []
        for check_door in range(6):
            # Plan: go to from_room, edit label, go to to_room, try door
            plan = from_room_path + [f"[{temp_label}]"] + [forward_door] + [check_door]
            plan_string = "".join(str(x) for x in plan)
            exploration_plans.append(plan_string)
            
        print(f"  Checking doors with plans: {exploration_plans}")
        
        # Execute the exploration
        result = self.api_client.explore(exploration_plans)
        
        if not result or "results" not in result:
            print("Failed to get results from return door discovery")
            return
            
        # Process results to find which door showed the modified label
        plan_strings = result.get("plan_strings", [])
        results = result["results"]
        
        for i, (plan_string, response_labels) in enumerate(zip(plan_strings, results)):
            check_door = i  # Door we were checking
            
            # Parse the response to separate actual labels from echoes
            actual_labels, echo_labels = self.api_client.parse_response_with_echoes(
                plan_string, response_labels
            )
            
            print(f"  Door {check_door}: response='{response_labels}', actual={actual_labels}, echoes={echo_labels}")
            
            # The destination of check_door should be the last actual label
            if actual_labels:
                destination_label = actual_labels[-1]
                
                # If this destination has the temporary label, this door leads back to from_room
                if destination_label == temp_label:
                    print(f"  Found return door: {check_door} leads back to room with temp label {temp_label} (original label {from_room.label})")
                    
                    # Record this in to_room's door labels - use the original label, not temp
                    to_room.set_door_label(check_door, from_room.label)
                    return
                    
        print("Could not identify return door")
    
    def cleanup_redundant_rooms(self):
        """Manual cleanup of all redundant rooms - useful after loading observations"""
        print("=== Manual Cleanup of Redundant Rooms ===")
        
        initial_count = len(self.room_manager.possible_rooms)
        
        # Remove duplicate complete rooms (with disambiguation)
        removed_dupes = self.room_manager.remove_duplicate_rooms(self.api_client)
        
        # Remove traceable partial rooms
        removed_partial = self.room_manager.cleanup_all_traceable_partial_rooms()
        
        # Final cleanup if we have complete coverage
        removed_final = self.room_manager.cleanup_all_partial_rooms_when_complete()
        
        final_count = len(self.room_manager.possible_rooms)
        total_removed = initial_count - final_count
        
        print(f"Cleanup complete: removed {total_removed} rooms ({initial_count} -> {final_count})")
        print(f"  Duplicates: {removed_dupes}, Traceable partials: {removed_partial}, Final cleanup: {removed_final}")
        
        if total_removed > 0:
            self.print_fingerprints()
        
        return total_removed
    
    def detect_and_resolve_ambiguous_rooms(self):
        """Detect and resolve rooms with identical fingerprints"""
        print("=== Detecting and Resolving Ambiguous Rooms ===")
        
        disambiguation_count = self.room_manager.detect_and_resolve_ambiguous_rooms()
        
        if disambiguation_count > 0:
            print(f"Assigned disambiguation IDs to {disambiguation_count} ambiguous rooms")
            self.print_fingerprints()
        else:
            print("No ambiguous rooms detected")
            
        return disambiguation_count
