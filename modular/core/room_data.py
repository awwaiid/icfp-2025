"""
Core Room data structure - pure data with no analysis logic
"""


class Room:
    def __init__(self, room_index=None, label=None):
        self.room_index = room_index  # unique index for this room instance
        self.label = label  # room label from API (0,1,2,3)
        self.paths = []  # array of paths for how we got here
        self.door_possibilities = [
            [] for _ in range(6)
        ]  # possible destinations for each door
        self.door_confirmed = [None] * 6  # confirmed destinations for each door
        self.possible_identities = set()  # rooms this might be identical to
        self.confirmed_unique = False  # True when definitely unique

    def add_door_possibility(self, door, destination_room):
        """Add a possible destination for a door"""
        if destination_room not in self.door_possibilities[door]:
            self.door_possibilities[door].append(destination_room)

    def confirm_door_destination(self, door, destination_room):
        """Confirm that a door definitely leads to a specific room"""
        self.door_confirmed[door] = destination_room
        self.door_possibilities[door] = [destination_room]

    def get_door_destination(self, door):
        """Get the confirmed destination, or None if ambiguous"""
        return self.door_confirmed[door]

    def get_door_possibilities(self, door):
        """Get all possible destinations for a door"""
        return self.door_possibilities[door]

    def has_confirmed_connection(self, door):
        """Check if door has a confirmed destination"""
        return self.door_confirmed[door] is not None

    def get_unconfirmed_doors(self):
        """Get list of doors without confirmed destinations"""
        return [i for i in range(6) if not self.has_confirmed_connection(i)]


class ProblemData:
    """Core problem data structure - holds rooms and observations"""

    def __init__(
        self, room_count, user_id="awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A"
    ):
        self.num_rooms = room_count
        self.rooms = {}  # room_id -> Room object
        self.next_room_id = 0
        self.observations = []  # raw observations from API
        self.room_sequence_map = {}  # (path, room_sequence) -> Room
        self.user_id = user_id
        self.base_url = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"

    def create_room(self, label):
        """Create a new room with given label"""
        room = Room(room_index=self.next_room_id, label=label)
        room_id = f"{self.next_room_id}_{label}"
        self.rooms[room_id] = room
        self.next_room_id += 1
        return room

    def get_room_id(self, room):
        """Get the room ID for a given room object"""
        for room_id, r in self.rooms.items():
            if r is room:
                return room_id
        return None

    def get_rooms_by_label(self, label):
        """Get all rooms with a specific label"""
        return [room for room in self.rooms.values() if room.label == label]

    def add_observation(self, path, rooms):
        """Store an observation (path and room sequence)"""
        self.observations.append({"path": path, "rooms": rooms})
