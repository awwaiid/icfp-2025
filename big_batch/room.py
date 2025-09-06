"""
Minimal Room implementation with fingerprint-based identification
"""

from typing import List, Optional


class Room:
    """A room identified by paths, label, and adjacency fingerprint"""

    def __init__(self, label: Optional[int] = None):
        self.label = label  # Room label (0, 1, 2, 3)
        self.paths = []  # List of paths used to reach this room
        self.door_labels = [None] * 6  # Labels of rooms reachable through each door

    def add_path(self, path: List[int]):
        """Add a path that leads to this room"""
        if path not in self.paths:
            self.paths.append(path[:])  # Copy the path

    def set_door_label(self, door: int, label: int):
        """Set the label of the room reachable through a specific door"""
        if 0 <= door <= 5:
            self.door_labels[door] = label

    def get_fingerprint(self) -> str:
        """Get fingerprint: label followed by door labels"""
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

    def __str__(self):
        paths_str = ", ".join([str(p) for p in self.paths]) if self.paths else "[]"
        return f"Room(label={self.label}, fingerprint={self.get_fingerprint()}, paths=[{paths_str}])"

    def __repr__(self):
        return self.__str__()
