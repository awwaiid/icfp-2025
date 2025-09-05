"""
Systematic exploration strategy - explores all paths up to a certain depth
"""

from .base_strategy import ExplorationStrategy


class SystematicStrategy(ExplorationStrategy):
    """Systematically explores all paths up to increasing depths"""

    def __init__(self, problem_data, identity_analyzer, max_depth=3):
        super().__init__(problem_data, identity_analyzer)
        self.name = "SystematicStrategy"
        self.max_depth = max_depth
        self.current_depth = 1
        self.explored_at_depth = {}  # depth -> set of explored paths

    def generate_next_paths(self, max_paths=None):
        """Generate all paths at current depth that haven't been explored"""
        if self.current_depth > self.max_depth:
            return []

        if self.current_depth not in self.explored_at_depth:
            self.explored_at_depth[self.current_depth] = set()

        paths = []
        explored_set = self.explored_at_depth[self.current_depth]

        # Generate all combinations for current depth
        def generate_paths(current_path, remaining_depth):
            if remaining_depth == 0:
                path_tuple = tuple(current_path)
                if path_tuple not in explored_set:
                    paths.append(current_path[:])
                    explored_set.add(path_tuple)
                return

            for door in range(6):
                current_path.append(door)
                generate_paths(current_path, remaining_depth - 1)
                current_path.pop()

        generate_paths([], self.current_depth)

        # If we've exhausted current depth, move to next
        if not paths:
            self.current_depth += 1
            return self.generate_next_paths(max_paths)

        # Limit paths if requested
        if max_paths and len(paths) > max_paths:
            paths = paths[:max_paths]

        return paths

    def should_continue_exploring(self):
        """Continue until max depth reached or all doors confirmed"""
        if self.current_depth > self.max_depth:
            return False

        stats = self.get_exploration_stats()
        return stats["unexplored_doors"] > 0


class TreeExplorationStrategy(ExplorationStrategy):
    """Explores using tree expansion from known rooms"""

    def __init__(self, problem_data, identity_analyzer):
        super().__init__(problem_data, identity_analyzer)
        self.name = "TreeExplorationStrategy"

    def generate_next_paths(self, max_paths=10):
        """Generate paths that expand from unconfirmed doors"""
        unexplored = self.get_unexplored_doors()

        if not unexplored:
            return []

        paths = []

        # For each unexplored door, create a path to it
        for room, door in unexplored[:max_paths]:
            # Find a path to this room
            path_to_room = self._find_path_to_room(room)
            if path_to_room is not None:
                # Extend with the unexplored door
                full_path = path_to_room + [door]
                paths.append(full_path)

        return paths

    def _find_path_to_room(self, target_room):
        """Find a path from starting room to target room"""
        # Simple: use the first path we know about for this room
        if target_room.paths:
            path, rooms, position = target_room.paths[0]
            return path[:position]  # path up to this room
        return []  # Starting room

    def should_continue_exploring(self):
        """Continue while there are unexplored doors"""
        return len(self.get_unexplored_doors()) > 0
