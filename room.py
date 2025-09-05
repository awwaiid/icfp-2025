class Room:
    def __init__(self, room_index=None, label=None):
        self.room_index = room_index  # true room "index"
        self.label = label  # which is 0, 1, 2, or 3
        self.paths = []  # array of paths for how we got here
        self.door_possibilities = [
            [] for _ in range(6)
        ]  # door_possibilities[i] = [list of possible Room destinations]
        self.door_confirmed = [
            None
        ] * 6  # door_confirmed[i] = definitely connected Room (or None if unconfirmed)
        self.possible_identities = (
            set()
        )  # set of other Room objects this might be identical to
        self.confirmed_unique = (
            False  # True when we know this room is definitely unique
        )

    def add_door_possibility(self, door, destination_room):
        """Add a possible destination for a door"""
        if destination_room not in self.door_possibilities[door]:
            self.door_possibilities[door].append(destination_room)

    def confirm_door_destination(self, door, destination_room):
        """Confirm that a door definitely leads to a specific room"""
        self.door_confirmed[door] = destination_room
        # Remove other possibilities since we now know for certain
        self.door_possibilities[door] = [destination_room]

    def get_door_destination(self, door):
        """Get the confirmed destination, or None if ambiguous"""
        return self.door_confirmed[door]

    def get_door_possibilities(self, door):
        """Get all possible destinations for a door"""
        return self.door_possibilities[door]
