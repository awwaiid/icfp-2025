"""
Room identity analysis - logic for determining which rooms might be identical
"""


class RoomIdentityAnalyzer:
    """Analyzes room relationships to determine possible identities and merges"""

    def __init__(self, problem_data):
        self.data = problem_data

    def update_room_identities(self):
        """Update possible identities for all rooms based on current knowledge"""
        rooms_by_label = self._group_rooms_by_label()

        # For each label group, determine possible identities
        for label, room_list in rooms_by_label.items():
            for i, room1 in enumerate(room_list):
                for j, room2 in enumerate(room_list[i + 1 :], i + 1):
                    if self.could_be_identical(room1, room2):
                        room1.possible_identities.add(room2)
                        room2.possible_identities.add(room1)
                    else:
                        # Remove from possible identities if they were there
                        room1.possible_identities.discard(room2)
                        room2.possible_identities.discard(room1)

        # Mark rooms as unique if they have no possible identities
        for room in self.data.rooms.values():
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

            # If both have confirmed connections, check if they go to different labels
            if conn1 is not None and conn2 is not None:
                if conn1.label != conn2.label:
                    return False

        return True

    def find_definite_merges(self):
        """Find rooms that are definitely the same and should be merged"""
        merges = []

        for room in self.data.rooms.values():
            if len(room.possible_identities) == 1:
                other_room = next(iter(room.possible_identities))
                if len(
                    other_room.possible_identities
                ) == 1 and other_room.possible_identities == {room}:
                    # Mutual single identity - these are definitely the same room
                    merges.append((room, other_room))

        return merges

    def detect_impossible_paths(self):
        """Detect paths that are longer than num_rooms (must contain cycles)"""
        impossible_paths = []

        for room in self.data.rooms.values():
            for path, rooms_sequence, position in room.paths:
                if len(rooms_sequence) > self.data.num_rooms:
                    impossible_paths.append((path, rooms_sequence, room, position))

        return impossible_paths

    def suggest_merges_from_cycles(self, impossible_paths):
        """Suggest room merges based on detected cycles"""
        suggestions = []

        for path, rooms_sequence, room, position in impossible_paths:
            # Simple heuristic: if we see the same label at positions that are num_rooms apart,
            # those are likely the same room
            for i in range(len(rooms_sequence) - self.data.num_rooms):
                if rooms_sequence[i] == rooms_sequence[i + self.data.num_rooms]:
                    suggestions.append(
                        {
                            "cycle_detected": True,
                            "repeated_label": rooms_sequence[i],
                            "positions": (i, i + self.data.num_rooms),
                            "path": path,
                            "rooms_sequence": rooms_sequence,
                        }
                    )

        return suggestions

    def get_ambiguous_rooms(self):
        """Get rooms that still have ambiguous identities"""
        return [
            room
            for room in self.data.rooms.values()
            if len(room.possible_identities) > 0 and not room.confirmed_unique
        ]

    def get_unique_rooms(self):
        """Get rooms that are confirmed unique"""
        return [room for room in self.data.rooms.values() if room.confirmed_unique]

    def _group_rooms_by_label(self):
        """Group rooms by their labels"""
        rooms_by_label = {}
        for room in self.data.rooms.values():
            if room.label not in rooms_by_label:
                rooms_by_label[room.label] = []
            rooms_by_label[room.label].append(room)
        return rooms_by_label

    def print_identity_summary(self):
        """Print a summary of room identity status"""
        unique = self.get_unique_rooms()
        ambiguous = self.get_ambiguous_rooms()
        merges = self.find_definite_merges()

        print(f"Room Identity Summary:")
        print(f"  Total rooms: {len(self.data.rooms)}")
        print(f"  Confirmed unique: {len(unique)}")
        print(f"  Still ambiguous: {len(ambiguous)}")
        print(f"  Ready to merge: {len(merges)} pairs")

        if ambiguous:
            print(f"  Ambiguous rooms by label:")
            by_label = {}
            for room in ambiguous:
                if room.label not in by_label:
                    by_label[room.label] = []
                by_label[room.label].append(room)

            for label, rooms in by_label.items():
                print(f"    Label {label}: {len(rooms)} rooms")
