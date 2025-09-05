"""
Connection-based room exploration data structures
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class Connection:
    """A connection from one room-door to another room-door"""

    from_room_id: int
    from_room_label: int
    from_door: int
    to_room_id: Optional[int] = None  # None if unknown
    to_room_label: Optional[int] = None  # None if unknown
    to_door: Optional[int] = None  # None if unknown
    confirmed: bool = False  # True when we've actually traversed this connection

    def __str__(self):
        from_str = f"Room{self.from_room_id}(label={self.from_room_label}):door{self.from_door}"
        if self.to_room_id is not None:
            to_str = (
                f"Room{self.to_room_id}(label={self.to_room_label}):door{self.to_door}"
            )
            status = "confirmed" if self.confirmed else "inferred"
            return f"{from_str} -> {to_str} [{status}]"
        else:
            return f"{from_str} -> UNKNOWN"

    def is_complete(self):
        """Check if connection has all information filled in"""
        return all(
            [
                self.to_room_id is not None,
                self.to_room_label is not None,
                self.to_door is not None,
            ]
        )

    def matches_pattern(self, other: "Connection") -> bool:
        """Check if this connection could be the same as another (same from/to labels)"""
        if not (self.is_complete() and other.is_complete()):
            return False
        return (
            self.from_room_label == other.from_room_label
            and self.to_room_label == other.to_room_label
        )


class ConnectionTable:
    """Table of all room-to-room door connections"""

    def __init__(self, max_rooms: int):
        self.max_rooms = max_rooms
        self.connections: List[Connection] = []
        self.next_room_id = 0

        # Quick lookups
        self.by_from: Dict[
            Tuple[int, int], List[Connection]
        ] = {}  # (room_id, door) -> connections
        self.by_room_id: Dict[
            int, List[Connection]
        ] = {}  # room_id -> all connections from that room

    def add_connection(
        self,
        from_room_id: int,
        from_room_label: int,
        from_door: int,
        to_room_id: Optional[int] = None,
        to_room_label: Optional[int] = None,
        to_door: Optional[int] = None,
        confirmed: bool = False,
    ) -> Connection:
        """Add a new connection to the table"""

        # Check if connection already exists
        existing = self.get_connection(from_room_id, from_door)
        if existing:
            # Update existing connection with new information
            if to_room_id is not None:
                existing.to_room_id = to_room_id
            if to_room_label is not None:
                existing.to_room_label = to_room_label
            if to_door is not None:
                existing.to_door = to_door
            if confirmed:
                existing.confirmed = True
            return existing

        # Create new connection
        connection = Connection(
            from_room_id=from_room_id,
            from_room_label=from_room_label,
            from_door=from_door,
            to_room_id=to_room_id,
            to_room_label=to_room_label,
            to_door=to_door,
            confirmed=confirmed,
        )

        self.connections.append(connection)
        self._update_indices(connection)
        return connection

    def _update_indices(self, connection: Connection):
        """Update lookup indices for a connection"""
        # Index by (room_id, door)
        key = (connection.from_room_id, connection.from_door)
        if key not in self.by_from:
            self.by_from[key] = []
        self.by_from[key].append(connection)

        # Index by room_id
        if connection.from_room_id not in self.by_room_id:
            self.by_room_id[connection.from_room_id] = []
        self.by_room_id[connection.from_room_id].append(connection)

    def get_connection(self, from_room_id: int, from_door: int) -> Optional[Connection]:
        """Get connection from specific room and door"""
        connections = self.by_from.get((from_room_id, from_door), [])
        return connections[0] if connections else None

    def get_room_connections(self, room_id: int) -> List[Connection]:
        """Get all connections from a specific room"""
        return self.by_room_id.get(room_id, [])

    def get_incomplete_connections(self) -> List[Connection]:
        """Get connections that don't have complete to_room information"""
        return [conn for conn in self.connections if not conn.is_complete()]

    def get_unconfirmed_connections(self) -> List[Connection]:
        """Get connections that haven't been directly traversed"""
        return [conn for conn in self.connections if not conn.confirmed]

    def find_mergeable_connections(self) -> List[Tuple[Connection, Connection]]:
        """Find pairs of connections that could be merged (same pattern)"""
        complete_connections = [conn for conn in self.connections if conn.is_complete()]
        merges = []

        for i, conn1 in enumerate(complete_connections):
            for conn2 in complete_connections[i + 1 :]:
                if conn1.matches_pattern(conn2):
                    merges.append((conn1, conn2))

        return merges

    def get_next_room_id(self) -> int:
        """Get next available room ID"""
        room_id = self.next_room_id
        self.next_room_id += 1
        return room_id

    def get_stats(self) -> Dict:
        """Get statistics about the connection table"""
        total = len(self.connections)
        complete = len([c for c in self.connections if c.is_complete()])
        confirmed = len([c for c in self.connections if c.confirmed])
        unique_rooms = len(set(c.from_room_id for c in self.connections))
        mergeable = len(self.find_mergeable_connections())

        return {
            "total_connections": total,
            "complete_connections": complete,
            "confirmed_connections": confirmed,
            "unique_rooms": unique_rooms,
            "mergeable_pairs": mergeable,
            "max_possible": self.max_rooms * 6,
        }

    def print_table(self):
        """Print the connection table"""
        print(f"\nConnection Table ({len(self.connections)} connections):")
        print("=" * 80)

        for connection in self.connections:
            print(f"  {connection}")

        stats = self.get_stats()
        print(
            f"\nStats: {stats['complete_connections']}/{stats['total_connections']} complete, "
            f"{stats['confirmed_connections']} confirmed, "
            f"{stats['unique_rooms']} unique rooms, "
            f"{stats['mergeable_pairs']} mergeable pairs"
        )

    def print_by_room(self):
        """Print connections grouped by room"""
        print(f"\nConnections by Room:")
        print("=" * 50)

        for room_id in sorted(self.by_room_id.keys()):
            connections = self.get_room_connections(room_id)
            if connections:
                room_label = connections[0].from_room_label
                print(f"\nRoom {room_id} (label {room_label}):")
                for conn in connections:
                    status = (
                        "✓" if conn.confirmed else "?" if conn.is_complete() else "○"
                    )
                    to_info = (
                        f"-> Room{conn.to_room_id}(L{conn.to_room_label}):D{conn.to_door}"
                        if conn.is_complete()
                        else "-> UNKNOWN"
                    )
                    print(f"  [{status}] Door {conn.from_door}: {to_info}")
