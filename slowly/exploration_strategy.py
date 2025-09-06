"""
Exploration Strategy for the ICFP 2025 room exploration problem
"""

from typing import List, Dict, Any, Optional, Tuple
from .room import Room


class ExplorationStrategy:
    """Handles exploration decision-making and prioritization"""

    def __init__(self, room_manager, observations: List[Dict], explored_paths: set):
        self.room_manager = room_manager
        self.observations = observations
        self.explored_paths = explored_paths

    def get_missing_connections_from_complete_rooms(self) -> List[Dict[str, Any]]:
        """Find connections from complete rooms to labels we haven't fully explored"""
        missing_connections = []
        complete_rooms = self.room_manager.get_complete_rooms()

        for room in complete_rooms:
            if not room.paths:
                continue

            base_path = room.paths[0]  # Use first path to this room

            # Check each door in this complete room
            for door, target_label in enumerate(room.door_labels):
                if target_label is not None:
                    # Check if we have a complete room with this label
                    complete_targets = [
                        r
                        for r in self.room_manager.get_all_rooms()
                        if r.label == target_label and r.is_complete()
                    ]

                    if not complete_targets:
                        # We don't have a complete room with this target label yet
                        # But only suggest this if we haven't already explored this path
                        target_path = base_path + [door]
                        path_tuple = tuple(target_path)

                        if path_tuple not in self.explored_paths:
                            missing_connections.append(
                                {
                                    "from_room": room,
                                    "door": door,
                                    "target_label": target_label,
                                    "path": target_path,
                                    "priority": "complete_to_unknown",
                                }
                            )

        return missing_connections

    def get_unknown_connections_to_verify(self) -> List[Dict[str, Any]]:
        """Find unknown connections in complete rooms that need verification or specific partial rooms that block verification"""
        unknown_connections = []
        complete_rooms = self.room_manager.get_complete_rooms()

        for room in complete_rooms:
            if not room.paths:
                continue

            # Get the absolute connections to see which are unknown
            absolute_connections = self.room_manager.get_absolute_connections(room)

            # Find doors with unknown connections (None)
            for door, connection in enumerate(absolute_connections):
                if connection is None:
                    base_path = room.paths[0]  # Use first path to this room

                    # Check if we have an observation for this door that shows the destination
                    destination_info = self.get_door_destination_info(room, door)

                    if destination_info:
                        # We have an observation, check if destination room is complete
                        destination_path, destination_label = destination_info
                        destination_room = self.find_room_by_path_and_label(
                            destination_path, destination_label
                        )

                        if destination_room and not destination_room.is_complete():
                            # We found the blocking partial room - prioritize completing it with all doors
                            batch_paths = []
                            for dest_door in range(6):
                                dest_exploration_path = destination_path + [dest_door]
                                path_tuple = tuple(dest_exploration_path)

                                if path_tuple not in self.explored_paths:
                                    batch_paths.append(dest_exploration_path)

                            if batch_paths:
                                unknown_connections.append(
                                    {
                                        "from_room": room,
                                        "door": door,
                                        "blocking_room": destination_room,
                                        "paths": batch_paths,  # Multiple paths for batch exploration
                                        "priority": "complete_blocking_partial_room_batch",
                                        "reason": f"Complete destination room to verify {room.get_fingerprint()} door {door}",
                                    }
                                )
                                return (
                                    unknown_connections  # Focus on one room at a time
                                )

                    # Fallback: try direct exploration if no observation yet
                    exploration_path = base_path + [door]
                    unknown_connections.append(
                        {
                            "from_room": room,
                            "door": door,
                            "path": exploration_path,
                            "priority": "verify_complete_room_connection",
                        }
                    )

        return unknown_connections

    def get_door_destination_info(
        self, from_room: Room, door: int
    ) -> Optional[Tuple[List[int], int]]:
        """Get destination path and label for a door, if we have an observation"""
        for obs in self.observations:
            if len(obs["plan"]) >= 1 and len(obs["rooms"]) >= 2:
                # Check if this observation shows us going through this door from this room
                for from_path in from_room.paths:
                    if len(obs["plan"]) > len(from_path):
                        if (
                            obs["plan"][: len(from_path)] == from_path
                            and obs["plan"][len(from_path)] == door
                        ):
                            # Found matching observation
                            if len(obs["rooms"]) > len(from_path) + 1:
                                destination_label = obs["rooms"][len(from_path) + 1]
                                destination_path = obs["plan"][: len(from_path) + 1]
                                return destination_path, destination_label
        return None

    def find_room_by_path_and_label(
        self, path: List[int], label: int
    ) -> Optional[Room]:
        """Find a room with the given path and label"""
        for room in self.room_manager.get_all_rooms():
            if room.label == label and path in room.paths:
                return room
        return None

    def get_partial_rooms_to_explore(self) -> List[Dict[str, Any]]:
        """Find partial rooms that we could explore further"""
        partial_explorations = []

        # Find partial rooms that we haven't fully explored from
        partial_rooms = self.room_manager.get_incomplete_rooms()

        for room in partial_rooms:
            if not room.paths:
                continue

            base_path = room.paths[0]  # Use first path to reach this room

            # Try to explore all doors from this partial room
            for door in range(6):
                exploration_path = base_path + [door]
                path_tuple = tuple(exploration_path)

                # Only suggest if we haven't explored this path yet
                if path_tuple not in self.explored_paths:
                    partial_explorations.append(
                        {
                            "from_room": room,
                            "door": door,
                            "path": exploration_path,
                            "priority": "partial_room_expansion",
                        }
                    )

        return partial_explorations

    def get_doors_worth_exploring(self, room: Room) -> List[int]:
        """Get doors that are worth exploring (lead to unknown destinations)"""
        if not room.paths:
            return []

        unknown_doors = room.get_unknown_doors()
        doors_worth_exploring = []

        for door in unknown_doors:
            # For now, explore all unknown doors - the duplicate removal will handle
            # cases where we discover rooms we already knew about
            doors_worth_exploring.append(door)

        return doors_worth_exploring

    def should_explore_path(self, plan: List[int]) -> bool:
        """Determine if we should explore this path"""
        plan_tuple = tuple(plan)

        # Always explore if we've never been there
        if plan_tuple not in self.explored_paths:
            return True

        # Don't re-explore paths we've already been on
        print(f"Skipping already explored path: {plan}")
        return False

    def get_next_exploration_batch(self) -> Optional[Dict[str, Any]]:
        """Get the next batch of paths to explore with priority information"""
        # First priority: Verify unknown connections in complete rooms
        unknown_connections = self.get_unknown_connections_to_verify()
        if unknown_connections:
            return {
                "type": "unknown_connections",
                "data": unknown_connections[0],
                "priority": 1,
            }

        # Second priority: Explore missing connections from complete rooms
        missing_connections = self.get_missing_connections_from_complete_rooms()
        if missing_connections:
            return {
                "type": "missing_connections",
                "data": missing_connections[0],
                "priority": 2,
            }

        # Third priority: Explore from partial rooms we discovered
        partial_explorations = self.get_partial_rooms_to_explore()
        if partial_explorations:
            return {
                "type": "partial_explorations",
                "data": partial_explorations[0],
                "priority": 3,
            }

        # Fourth priority: Regular incomplete room exploration
        incomplete_rooms = self.room_manager.get_incomplete_rooms()
        if incomplete_rooms:
            for room in incomplete_rooms:
                doors_to_explore = self.get_doors_worth_exploring(room)
                if doors_to_explore and room.paths:
                    base_path = room.paths[0]
                    plans = []
                    for door in doors_to_explore:
                        plan = base_path + [door]
                        plans.append(plan)

                    return {
                        "type": "incomplete_rooms",
                        "data": {
                            "room": room,
                            "doors": doors_to_explore,
                            "plans": plans,
                        },
                        "priority": 4,
                    }

        return None
