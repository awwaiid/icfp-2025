import json
import subprocess
import requests
from room import Room


class Problem:
    def __init__(
        self, room_count, user_id="awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A"
    ):
        self.num_rooms = room_count  # number of rooms in the problem
        self.final_room = None  # instance of the final room we need to reach
        self.rooms = {}  # dictionary of room instances, keyed by unique identifier
        self.next_room_id = 0  # counter for assigning unique room IDs
        self.observations = []  # store all observations for saving
        self.room_sequence_map = {}  # maps (path_prefix, room_labels) to room instances
        self.user_id = user_id  # API user ID
        self.base_url = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"

    def add_observation(self, path, rooms):
        """
        Add an observation of a path through rooms using incremental door tracking.
        path: list of door numbers taken [0, 2, 0]
        rooms: list of room labels visited [0, 1, 2, 3] (one more than doors)
        """
        if len(rooms) != len(path) + 1:
            raise ValueError("rooms list should have one more element than path")

        # Store the observation
        self.observations.append({"path": path, "rooms": rooms})

        # Process incrementally: for each step in the path
        current_room = self.get_or_create_starting_room(rooms[0])

        for i, door in enumerate(path):
            destination_label = rooms[i + 1]

            # Find or create destination room possibilities
            destination_room = self.process_door_destination(
                current_room, door, destination_label, path[: i + 1], rooms[: i + 2]
            )

            # Move to the destination for next iteration
            current_room = destination_room

        # Update room identity tracking after new observation
        self.update_room_identities()

    def get_or_create_starting_room(self, label):
        """Get or create the starting room with given label"""
        sequence_key = ((), (label,))  # Empty path, just the starting room

        if sequence_key in self.room_sequence_map:
            return self.room_sequence_map[sequence_key]
        else:
            room = Room(room_index=self.next_room_id, label=label)
            room_id = f"{self.next_room_id}_{label}"
            self.rooms[room_id] = room
            self.room_sequence_map[sequence_key] = room
            self.next_room_id += 1
            return room

    def process_door_destination(
        self, from_room, door, destination_label, path_so_far, rooms_so_far
    ):
        """Process a door leading to a room with destination_label"""
        sequence_key = (tuple(path_so_far), tuple(rooms_so_far))

        # Check if we've seen this exact sequence before
        if sequence_key in self.room_sequence_map:
            destination_room = self.room_sequence_map[sequence_key]
            from_room.confirm_door_destination(door, destination_room)
            return destination_room

        # Find all existing rooms with the destination label as possibilities
        possible_destinations = []
        for room in self.rooms.values():
            if room.label == destination_label:
                possible_destinations.append(room)

        # Create a new room as another possibility
        new_room = Room(room_index=self.next_room_id, label=destination_label)
        room_id = f"{self.next_room_id}_{destination_label}"
        self.rooms[room_id] = new_room
        self.room_sequence_map[sequence_key] = new_room
        self.next_room_id += 1

        # Add all possibilities to the door
        for room in possible_destinations:
            from_room.add_door_possibility(door, room)
        from_room.add_door_possibility(door, new_room)

        # For this specific path, confirm it leads to the new room
        from_room.confirm_door_destination(door, new_room)

        # Mark all same-label rooms as potentially identical
        for room in possible_destinations:
            new_room.possible_identities.add(room)
            room.possible_identities.add(new_room)

        return new_room

    def save_observations(self, filename):
        """Save all observations to a JSON file"""
        data = {"observations": self.observations}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def load_observations(self, filename):
        """Load observations from a JSON file and process them"""
        with open(filename, "r") as f:
            data = json.load(f)

        for obs in data["observations"]:
            self.add_observation(obs["path"], obs["rooms"])

    def generate_graphviz(self, filename, render_png=True):
        """Generate a Graphviz diagram of the mapped rooms"""
        dot_filename = filename if filename.endswith(".dot") else f"{filename}.dot"

        # Find definite merges to represent as single nodes
        definite_merges = self.find_definite_merges()
        merged_rooms = set()
        room_groups = {}  # Maps representative room to list of all rooms in group

        # Process merges to create room groups
        for room1, room2 in definite_merges:
            # Find which group each room belongs to (if any)
            group1 = next((k for k, v in room_groups.items() if room1 in v), room1)
            group2 = next((k for k, v in room_groups.items() if room2 in v), room2)

            if group1 == group2:
                continue  # Already in same group

            # Merge groups or create new group
            if group1 in room_groups and group2 in room_groups:
                # Merge two existing groups
                room_groups[group1].extend(room_groups[group2])
                del room_groups[group2]
                merged_rooms.update(room_groups[group1])
            elif group1 in room_groups:
                room_groups[group1].append(room2)
                merged_rooms.add(room2)
            elif group2 in room_groups:
                room_groups[group2].append(room1)
                merged_rooms.add(room1)
            else:
                # Create new group
                room_groups[room1] = [room1, room2]
                merged_rooms.update([room1, room2])

        with open(dot_filename, "w") as f:
            f.write("digraph rooms {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box];\n")

            # Write nodes for merged groups
            for representative, room_list in room_groups.items():
                room_ids = [self.get_room_id(r) for r in room_list]
                paths_info = f"\\nPaths: {len(representative.paths)}"
                identities_info = (
                    f"\\nPossible IDs: {len(representative.possible_identities)}"
                )

                f.write(
                    f'  "{self.get_room_id(representative)}" [label="Merged Room\\nLabel: {representative.label}{paths_info}{identities_info}\\nContains: {", ".join(room_ids)}" fillcolor=lightblue style=filled];\n'
                )

            # Write nodes for unmerged rooms
            for room_id, room in self.rooms.items():
                if room not in merged_rooms:
                    color = ""
                    if room.confirmed_unique:
                        color = " fillcolor=lightgreen style=filled"
                    elif len(room.possible_identities) > 0:
                        color = " fillcolor=lightyellow style=filled"

                    identities_info = (
                        f"\\nPossible IDs: {len(room.possible_identities)}"
                        if len(room.possible_identities) > 0
                        else ""
                    )
                    f.write(
                        f'  "{room_id}" [label="Room {room.room_index}\\nLabel: {room.label}{identities_info}"{color}];\n'
                    )

            # Write edges (door connections)
            drawn_edges = set()
            for room_id, room in self.rooms.items():
                # Use representative if this room is merged
                source_id = room_id
                if room in merged_rooms:
                    representative = next(
                        k for k, v in room_groups.items() if room in v
                    )
                    source_id = self.get_room_id(representative)

                for door in range(6):
                    confirmed_dest = room.get_door_destination(door)
                    possibilities = room.get_door_possibilities(door)

                    if confirmed_dest is not None:
                        # Draw confirmed connection with solid line
                        target_id = self.get_room_id(confirmed_dest)
                        if confirmed_dest in merged_rooms:
                            representative = next(
                                k for k, v in room_groups.items() if confirmed_dest in v
                            )
                            target_id = self.get_room_id(representative)

                        edge_key = (source_id, target_id, door)
                        if edge_key not in drawn_edges:
                            f.write(
                                f'  "{source_id}" -> "{target_id}" [label="door {door}" color=black];\n'
                            )
                            drawn_edges.add(edge_key)

                    elif len(possibilities) > 1:
                        # Draw multiple possibilities with dashed lines
                        for possible_dest in possibilities:
                            target_id = self.get_room_id(possible_dest)
                            if possible_dest in merged_rooms:
                                representative = next(
                                    k
                                    for k, v in room_groups.items()
                                    if possible_dest in v
                                )
                                target_id = self.get_room_id(representative)

                            edge_key = (source_id, target_id, door)
                            if edge_key not in drawn_edges:
                                f.write(
                                    f'  "{source_id}" -> "{target_id}" [label="door {door}?" style=dashed color=gray];\n'
                                )
                                drawn_edges.add(edge_key)

            f.write("}\n")

        if render_png:
            png_filename = dot_filename.replace(".dot", ".png")
            try:
                subprocess.run(
                    ["dot", "-Tpng", dot_filename, "-o", png_filename], check=True
                )
                print(f"Generated {dot_filename} and {png_filename}")
            except subprocess.CalledProcessError:
                print(
                    f"Generated {dot_filename} (dot command failed for PNG generation)"
                )
            except FileNotFoundError:
                print(
                    f"Generated {dot_filename} (dot command not found for PNG generation)"
                )
        else:
            print(f"Generated {dot_filename}")

    def get_room_id(self, room):
        """Get the room ID for a given room object"""
        for room_id, r in self.rooms.items():
            if r is room:
                return room_id
        return None

    def select_problem(self, problem_name):
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

    def explore(self, plans):
        """Explore with the given plans using the API"""
        # Convert plans from arrays of integers to strings for the API
        plan_strings = ["".join(str(door) for door in plan) for plan in plans]
        print(f"Exploring with {len(plans)} plan(s): {', '.join(plan_strings)}")

        data = {"id": self.user_id, "plans": plan_strings}

        response = requests.post(
            f"{self.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        # Parse and add observations if successful
        if response.status_code == 200:
            try:
                result = response.json()
                if "results" in result:
                    self.parse_exploration_results(plans, result["results"])
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return response

    def parse_exploration_results(self, plans, results):
        """Parse exploration results and add observations"""
        for i, (plan, result) in enumerate(zip(plans, results)):
            # Plan is already a list of integers
            path = plan
            # Result contains the room labels encountered
            rooms = result

            print(f"Adding observation: path={path}, rooms={rooms}")
            self.add_observation(path, rooms)

    def explore_tree(self, depth):
        """Generate all possible paths up to given depth and explore them"""
        if depth <= 0:
            return

        paths = []

        # Generate all paths from depth 1 to depth
        for current_depth in range(1, depth + 1):
            # Generate all combinations of doors for this depth
            def generate_paths(current_path, remaining_depth):
                if remaining_depth == 0:
                    paths.append(current_path[:])
                    return

                for door in range(6):  # doors 0-5
                    current_path.append(door)
                    generate_paths(current_path, remaining_depth - 1)
                    current_path.pop()

            generate_paths([], current_depth)

        print(f"Generated {len(paths)} paths up to depth {depth}")
        return self.explore(paths)

    def submit_guess(self, map_data):
        """Submit a guess using the API"""
        print("Submitting guess")

        data = {"id": self.user_id, "map": map_data}

        response = requests.post(
            f"{self.base_url}/guess",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def submit_guess_from_file(self, map_file):
        """Submit a guess from a JSON file"""
        try:
            with open(map_file, "r") as f:
                map_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{map_file}' not found")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{map_file}': {e}")
            return None

        return self.submit_guess(map_data)

    def update_room_identities(self):
        """Update possible identities for all rooms based on current knowledge"""
        rooms_by_label = {}

        # Group rooms by label
        for room_id, room in self.rooms.items():
            if room.label not in rooms_by_label:
                rooms_by_label[room.label] = []
            rooms_by_label[room.label].append(room)

        # For each label group, determine possible identities
        for label, room_list in rooms_by_label.items():
            for i, room1 in enumerate(room_list):
                for j, room2 in enumerate(room_list[i + 1 :], i + 1):
                    # Check if these rooms could be identical
                    if self.could_be_identical(room1, room2):
                        room1.possible_identities.add(room2)
                        room2.possible_identities.add(room1)
                    else:
                        # Remove from possible identities if they were there
                        room1.possible_identities.discard(room2)
                        room2.possible_identities.discard(room1)

        # Mark rooms as unique if they have no possible identities
        for room in self.rooms.values():
            if len(room.possible_identities) == 0:
                room.confirmed_unique = True

    def could_be_identical(self, room1, room2):
        """Check if two rooms could be the same room"""
        # Must have same label
        if room1.label != room2.label:
            return False

        # Check door connections - if they connect to rooms with different labels, they're different
        for door in range(6):
            conn1 = room1.get_door_destination(door)
            conn2 = room2.get_door_destination(door)

            # If one has a confirmed connection and the other doesn't, they could still be identical
            # (we might not have explored both doors yet)
            if conn1 is not None and conn2 is not None:
                # Both have confirmed connections - check if they go to rooms with different labels
                if conn1.label != conn2.label:
                    return False

        return True

    def find_definite_merges(self):
        """Find rooms that are definitely the same and should be merged"""
        merges = []

        for room_id, room in self.rooms.items():
            if len(room.possible_identities) == 1:
                other_room = next(iter(room.possible_identities))
                if len(
                    other_room.possible_identities
                ) == 1 and other_room.possible_identities == {room}:
                    # Mutual single identity - these are definitely the same room
                    merges.append((room, other_room))

        return merges

    def detect_cycles_and_update(self):
        """Detect cycles in paths longer than num_rooms and update room identities"""
        for room_id, room in self.rooms.items():
            for path, rooms_sequence, position in room.paths:
                if len(rooms_sequence) > self.num_rooms:
                    # This path is too long - there must be a cycle
                    # We could implement cycle detection logic here
                    print(f"Cycle detected in path: {path} -> {rooms_sequence}")
                    # TODO: Implement cycle detection and room merging
