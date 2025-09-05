"""
Modular Problem class that coordinates all the components
"""

import json
import requests
from .core.room_data import ProblemData
from .analysis.room_identity import RoomIdentityAnalyzer
from .visualization.graphviz_renderer import GraphvizRenderer, TextRenderer


class ModularProblem:
    """Main problem solver that coordinates data, analysis, and exploration"""

    def __init__(
        self, room_count, user_id="awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A"
    ):
        self.data = ProblemData(room_count, user_id)
        self.analyzer = RoomIdentityAnalyzer(self.data)
        self.visualizer = GraphvizRenderer(self.data, self.analyzer)
        self.text_renderer = TextRenderer(self.data, self.analyzer)
        self.current_strategy = None

    def set_strategy(self, strategy_class, **kwargs):
        """Set the exploration strategy"""
        self.current_strategy = strategy_class(self.data, self.analyzer, **kwargs)
        print(f"Set exploration strategy: {self.current_strategy.name}")

    def add_observation(self, path, rooms):
        """Add an observation and update analysis"""
        if len(rooms) != len(path) + 1:
            raise ValueError("rooms list should have one more element than path")

        # Store the raw observation
        self.data.add_observation(path, rooms)

        # Process incrementally
        current_room = self._get_or_create_starting_room(rooms[0])

        for i, door in enumerate(path):
            destination_label = rooms[i + 1]
            destination_room = self._process_door_destination(
                current_room, door, destination_label, path[: i + 1], rooms[: i + 2]
            )
            current_room = destination_room

        # Update analysis
        self.analyzer.update_room_identities()

    def _get_or_create_starting_room(self, label):
        """Get or create the starting room with given label"""
        sequence_key = ((), (label,))

        if sequence_key in self.data.room_sequence_map:
            return self.data.room_sequence_map[sequence_key]
        else:
            room = self.data.create_room(label)
            self.data.room_sequence_map[sequence_key] = room
            return room

    def _process_door_destination(
        self, from_room, door, destination_label, path_so_far, rooms_so_far
    ):
        """Process a door leading to a room with destination_label"""
        sequence_key = (tuple(path_so_far), tuple(rooms_so_far))

        # Check if we've seen this exact sequence before
        if sequence_key in self.data.room_sequence_map:
            destination_room = self.data.room_sequence_map[sequence_key]
            from_room.confirm_door_destination(door, destination_room)
            return destination_room

        # Find all existing rooms with the destination label as possibilities
        possible_destinations = self.data.get_rooms_by_label(destination_label)

        # Create a new room as another possibility
        new_room = self.data.create_room(destination_label)
        self.data.room_sequence_map[sequence_key] = new_room

        # Add all possibilities to the door
        for room in possible_destinations:
            from_room.add_door_possibility(door, room)
        from_room.add_door_possibility(door, new_room)

        # For this specific path, confirm it leads to the new room
        from_room.confirm_door_destination(door, new_room)

        # Mark all same-label rooms as potentially identical
        for room in possible_destinations:
            new_room.possible_identities.add(room)
            room.possible_identities.add(new_room)

        return new_room

    # API Methods
    def select_problem(self, problem_name):
        """Select a problem using the API"""
        print(f"Selecting problem {problem_name}")

        data = {"id": self.data.user_id, "problemName": problem_name}
        response = requests.post(
            f"{self.data.base_url}/select",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def explore(self, plans):
        """Explore with the given plans using the API"""
        plan_strings = ["".join(str(door) for door in plan) for plan in plans]
        print(f"Exploring with {len(plans)} plan(s): {', '.join(plan_strings)}")

        data = {"id": self.data.user_id, "plans": plan_strings}
        response = requests.post(
            f"{self.data.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        # Parse and add observations if successful
        if response.status_code == 200:
            try:
                result = response.json()
                if "results" in result:
                    for plan, rooms_result in zip(plans, result["results"]):
                        print(f"Adding observation: path={plan}, rooms={rooms_result}")
                        self.add_observation(plan, rooms_result)
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return response

    def explore_with_strategy(self, max_iterations=10, max_paths_per_iteration=10):
        """Explore using the current strategy"""
        if not self.current_strategy:
            print("No exploration strategy set! Use set_strategy() first.")
            return

        iteration = 0
        while (
            iteration < max_iterations
            and self.current_strategy.should_continue_exploring()
        ):
            print(f"\nIteration {iteration + 1}:")
            paths = self.current_strategy.generate_next_paths(max_paths_per_iteration)

            if not paths:
                print("No more paths to explore")
                break

            print(f"Generated {len(paths)} paths")
            self.explore(paths)
            self.current_strategy.print_stats()

            iteration += 1

        print(f"\nExploration completed after {iteration} iterations")

    def submit_guess(self, map_data):
        """Submit a guess using the API"""
        print("Submitting guess")

        data = {"id": self.data.user_id, "map": map_data}
        response = requests.post(
            f"{self.data.base_url}/guess",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    # File I/O
    def save_observations(self, filename):
        """Save all observations to a JSON file"""
        data = {"observations": self.data.observations}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def load_observations(self, filename):
        """Load observations from a JSON file and process them"""
        with open(filename, "r") as f:
            data = json.load(f)

        for obs in data["observations"]:
            self.add_observation(obs["path"], obs["rooms"])

    # Visualization
    def generate_graphviz(self, filename, render_png=True, show_possibilities=True):
        """Generate graphviz visualization"""
        self.visualizer.generate_graphviz(filename, render_png, show_possibilities)

    def print_summary(self):
        """Print text summary of current state"""
        self.text_renderer.print_room_summary()
        if self.current_strategy:
            self.current_strategy.print_stats()

    # Analysis
    def print_identity_analysis(self):
        """Print room identity analysis"""
        self.analyzer.print_identity_summary()

        impossible_paths = self.analyzer.detect_impossible_paths()
        if impossible_paths:
            print(f"\nDetected {len(impossible_paths)} impossible paths (cycles)")
            suggestions = self.analyzer.suggest_merges_from_cycles(impossible_paths)
            if suggestions:
                print("Suggested merges from cycle detection:")
                for suggestion in suggestions[:5]:  # Show first 5
                    print(
                        f"  Label {suggestion['repeated_label']} at positions {suggestion['positions']}"
                    )
