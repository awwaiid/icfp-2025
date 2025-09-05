"""
Base exploration strategy interface
"""

from abc import ABC, abstractmethod


class ExplorationStrategy(ABC):
    """Base class for exploration strategies"""

    def __init__(self, problem_data, identity_analyzer):
        self.data = problem_data
        self.analyzer = identity_analyzer
        self.name = "BaseStrategy"

    @abstractmethod
    def generate_next_paths(self, max_paths=None):
        """Generate the next set of paths to explore"""
        pass

    @abstractmethod
    def should_continue_exploring(self):
        """Determine if exploration should continue"""
        pass

    def get_unexplored_doors(self):
        """Get all doors that haven't been confirmed"""
        unexplored = []
        for room_id, room in self.data.rooms.items():
            for door in range(6):
                if not room.has_confirmed_connection(door):
                    unexplored.append((room, door))
        return unexplored

    def get_exploration_stats(self):
        """Get statistics about current exploration state"""
        total_doors = len(self.data.rooms) * 6
        confirmed_doors = sum(
            1
            for room in self.data.rooms.values()
            for door in range(6)
            if room.has_confirmed_connection(door)
        )

        return {
            "total_rooms": len(self.data.rooms),
            "total_doors": total_doors,
            "confirmed_doors": confirmed_doors,
            "unexplored_doors": total_doors - confirmed_doors,
            "unique_rooms": len(self.analyzer.get_unique_rooms()),
            "ambiguous_rooms": len(self.analyzer.get_ambiguous_rooms()),
            "ready_merges": len(self.analyzer.find_definite_merges()),
        }

    def print_stats(self):
        """Print exploration statistics"""
        stats = self.get_exploration_stats()
        print(f"\n{self.name} Statistics:")
        print(f"  Rooms discovered: {stats['total_rooms']}")
        print(
            f"  Door connections: {stats['confirmed_doors']}/{stats['total_doors']} confirmed"
        )
        print(
            f"  Room identity: {stats['unique_rooms']} unique, {stats['ambiguous_rooms']} ambiguous"
        )
        print(f"  Ready to merge: {stats['ready_merges']} pairs")
