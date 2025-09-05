import json
import subprocess
import requests
from room import Room


class Problem:
    def __init__(self, room_count, user_id="awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A"):
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
        Add an observation of a path through rooms.
        path: list of door numbers taken [0, 2, 0]
        rooms: list of room labels visited [0, 1, 2, 3] (one more than doors)
        """
        if len(rooms) != len(path) + 1:
            raise ValueError("rooms list should have one more element than path")

        # Store the observation
        self.observations.append({"path": path, "rooms": rooms})

        # Create or find room instances, reusing existing ones for matching sequences
        room_instances = []
        for i, room_label in enumerate(rooms):
            # Create a key based on the path taken to reach this room and the room sequence
            path_to_here = tuple(path[:i])  # path taken to reach this position
            room_sequence_to_here = tuple(
                rooms[: i + 1]
            )  # room sequence up to this point
            sequence_key = (path_to_here, room_sequence_to_here)

            if sequence_key in self.room_sequence_map:
                # Reuse existing room instance
                room_instances.append(self.room_sequence_map[sequence_key])
            else:
                # Create new room instance
                room_instance = Room(room_index=self.next_room_id, label=room_label)
                self.rooms[f"{self.next_room_id}_{room_label}"] = room_instance
                self.room_sequence_map[sequence_key] = room_instance
                self.next_room_id += 1
                room_instances.append(room_instance)

        # Record the path in each room
        for i, room in enumerate(room_instances):
            room.paths.append(
                (path, rooms, i)
            )  # store path, rooms, and position in sequence

        # Record door connections
        for i, door in enumerate(path):
            from_room = room_instances[i]
            to_room = room_instances[i + 1]
            from_room.doors[door] = to_room
            from_room.door_connections[door] = to_room.label

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
        dot_filename = filename if filename.endswith('.dot') else f"{filename}.dot"
        
        with open(dot_filename, "w") as f:
            f.write("digraph rooms {\n")
            f.write("  node [shape=box];\n")
            
            # Write nodes
            for room_id, room in self.rooms.items():
                f.write(f'  "{room_id}" [label="Room {room.room_index}\\nLabel: {room.label}"];\n')
            
            # Write edges (door connections)
            drawn_edges = set()
            for room_id, room in self.rooms.items():
                for door, connected_room in enumerate(room.doors):
                    if connected_room is not None:
                        connected_id = None
                        # Find the connected room's ID
                        for cid, croom in self.rooms.items():
                            if croom is connected_room:
                                connected_id = cid
                                break
                        
                        if connected_id:
                            edge_key = (room_id, connected_id, door)
                            if edge_key not in drawn_edges:
                                f.write(f'  "{room_id}" -> "{connected_id}" [label="door {door}"];\n')
                                drawn_edges.add(edge_key)
            
            f.write("}\n")
        
        if render_png:
            png_filename = dot_filename.replace('.dot', '.png')
            try:
                subprocess.run(['dot', '-Tpng', dot_filename, '-o', png_filename], check=True)
                print(f"Generated {dot_filename} and {png_filename}")
            except subprocess.CalledProcessError:
                print(f"Generated {dot_filename} (dot command failed for PNG generation)")
            except FileNotFoundError:
                print(f"Generated {dot_filename} (dot command not found for PNG generation)")
        else:
            print(f"Generated {dot_filename}")

    def select_problem(self, problem_name):
        """Select a problem using the API"""
        print(f"Selecting problem {problem_name}")
        
        data = {
            "id": self.user_id,
            "problemName": problem_name
        }
        
        response = requests.post(
            f"{self.base_url}/select",
            headers={"Content-Type": "application/json"},
            json=data
        )
        
        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def explore(self, plans):
        """Explore with the given plans using the API"""
        print(f"Exploring with {len(plans)} plan(s): {', '.join(plans)}")
        
        data = {
            "id": self.user_id,
            "plans": plans
        }
        
        response = requests.post(
            f"{self.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data
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
            # Convert plan string to list of door numbers
            path = [int(door) for door in plan]
            # Result contains the room labels encountered
            rooms = result
            
            print(f"Adding observation: path={path}, rooms={rooms}")
            self.add_observation(path, rooms)

    def submit_guess(self, map_data):
        """Submit a guess using the API"""
        print("Submitting guess")
        
        data = {
            "id": self.user_id,
            "map": map_data
        }
        
        response = requests.post(
            f"{self.base_url}/guess",
            headers={"Content-Type": "application/json"},
            json=data
        )
        
        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def submit_guess_from_file(self, map_file):
        """Submit a guess from a JSON file"""
        try:
            with open(map_file, 'r') as f:
                map_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{map_file}' not found")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{map_file}': {e}")
            return None
        
        return self.submit_guess(map_data)
