
import json
from room import Room

class Problem:
    def __init__(self, room_count):
        self.num_rooms = room_count  # number of rooms in the problem
        self.final_room = None  # instance of the final room we need to reach
        self.rooms = {}  # dictionary of room instances, keyed by unique identifier
        self.next_room_id = 0  # counter for assigning unique room IDs
        self.observations = []  # store all observations for saving
        self.room_sequence_map = {}  # maps (path_prefix, room_labels) to room instances
        
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
            room_sequence_to_here = tuple(rooms[:i+1])  # room sequence up to this point
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
            room.paths.append((path, rooms, i))  # store path, rooms, and position in sequence
            
        # Record door connections
        for i, door in enumerate(path):
            from_room = room_instances[i]
            to_room = room_instances[i + 1]
            from_room.doors[door] = to_room
            from_room.door_connections[door] = to_room.label
            
    def save_observations(self, filename):
        """Save all observations to a JSON file"""
        data = {"observations": self.observations}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
