"""
Random exploration strategies
"""

import random
from .base_strategy import ExplorationStrategy


class RandomWalkStrategy(ExplorationStrategy):
    """Random walk exploration"""

    def __init__(self, problem_data, identity_analyzer, max_path_length=5):
        super().__init__(problem_data, identity_analyzer)
        self.name = "RandomWalkStrategy"
        self.max_path_length = max_path_length

    def generate_next_paths(self, max_paths=10):
        """Generate random paths of varying lengths"""
        paths = []

        for _ in range(max_paths):
            length = random.randint(1, self.max_path_length)
            path = [random.randint(0, 5) for _ in range(length)]
            paths.append(path)

        return paths

    def should_continue_exploring(self):
        """Continue exploring with some probability based on progress"""
        stats = self.get_exploration_stats()

        # More likely to continue if we haven't confirmed many doors
        if stats["confirmed_doors"] < stats["total_doors"] * 0.8:
            return True

        # Random chance to continue even when mostly explored
        return random.random() < 0.3


class BiasedRandomStrategy(ExplorationStrategy):
    """Random exploration biased toward unexplored areas"""

    def __init__(self, problem_data, identity_analyzer, bias_strength=0.7):
        super().__init__(problem_data, identity_analyzer)
        self.name = "BiasedRandomStrategy"
        self.bias_strength = bias_strength  # 0-1, higher = more bias toward unexplored

    def generate_next_paths(self, max_paths=10):
        """Generate random paths biased toward unexplored doors"""
        paths = []
        unexplored = self.get_unexplored_doors()

        if not unexplored:
            # Fall back to pure random if nothing unexplored
            return RandomWalkStrategy(self.data, self.analyzer).generate_next_paths(
                max_paths
            )

        for _ in range(max_paths):
            if random.random() < self.bias_strength and unexplored:
                # Biased toward unexplored door
                room, door = random.choice(unexplored)
                path_to_room = self._find_short_path_to_room(room)
                path = path_to_room + [door]
            else:
                # Pure random path
                length = random.randint(1, 4)
                path = [random.randint(0, 5) for _ in range(length)]

            paths.append(path)

        return paths

    def _find_short_path_to_room(self, target_room):
        """Find a short path to target room"""
        if target_room.paths:
            # Use the shortest known path
            shortest_path = min(target_room.paths, key=lambda x: len(x[0]))
            path, rooms, position = shortest_path
            return path[:position]
        return []

    def should_continue_exploring(self):
        """Continue while significant unexplored area remains"""
        stats = self.get_exploration_stats()
        return stats["unexplored_doors"] > stats["total_doors"] * 0.1


class AdaptiveStrategy(ExplorationStrategy):
    """Adaptive strategy that switches between different approaches"""

    def __init__(self, problem_data, identity_analyzer):
        super().__init__(problem_data, identity_analyzer)
        self.name = "AdaptiveStrategy"
        self.strategies = [
            RandomWalkStrategy(problem_data, identity_analyzer, max_path_length=3),
            BiasedRandomStrategy(problem_data, identity_analyzer, bias_strength=0.8),
        ]
        self.current_strategy_index = 0
        self.switch_threshold = 20  # Switch after this many explorations

    def generate_next_paths(self, max_paths=10):
        """Generate paths using current strategy"""
        current_strategy = self.strategies[self.current_strategy_index]

        # Switch strategies periodically
        if hasattr(self, "exploration_count"):
            self.exploration_count += 1
            if self.exploration_count >= self.switch_threshold:
                self.current_strategy_index = (self.current_strategy_index + 1) % len(
                    self.strategies
                )
                self.exploration_count = 0
                current_strategy = self.strategies[self.current_strategy_index]
                print(f"  Switching to {current_strategy.name}")
        else:
            self.exploration_count = 0

        return current_strategy.generate_next_paths(max_paths)

    def should_continue_exploring(self):
        """Continue based on current strategy"""
        current_strategy = self.strategies[self.current_strategy_index]
        return current_strategy.should_continue_exploring()
