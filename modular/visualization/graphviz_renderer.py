"""
Graphviz visualization for room maps
"""

import subprocess


class GraphvizRenderer:
    """Renders room maps using Graphviz"""

    def __init__(self, problem_data, identity_analyzer):
        self.data = problem_data
        self.analyzer = identity_analyzer

    def generate_graphviz(self, filename, render_png=True, show_possibilities=True):
        """Generate a Graphviz diagram of the mapped rooms"""
        dot_filename = filename if filename.endswith(".dot") else f"{filename}.dot"

        # Find definite merges to represent as single nodes
        definite_merges = self.analyzer.find_definite_merges()
        merged_rooms = set()
        room_groups = self._create_room_groups(definite_merges, merged_rooms)

        with open(dot_filename, "w") as f:
            f.write("digraph rooms {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box];\n")

            # Write nodes for merged groups
            self._write_merged_nodes(f, room_groups)

            # Write nodes for unmerged rooms
            self._write_individual_nodes(f, merged_rooms)

            # Write edges (door connections)
            self._write_edges(f, room_groups, merged_rooms, show_possibilities)

            f.write("}\n")

        if render_png:
            self._render_png(dot_filename)
        else:
            print(f"Generated {dot_filename}")

    def _create_room_groups(self, definite_merges, merged_rooms):
        """Create groups of rooms that should be merged"""
        room_groups = {}

        for room1, room2 in definite_merges:
            # Find which group each room belongs to (if any)
            group1 = next((k for k, v in room_groups.items() if room1 in v), room1)
            group2 = next((k for k, v in room_groups.items() if room2 in v), room2)

            if group1 == group2:
                continue  # Already in same group

            # Merge groups or create new group
            if group1 in room_groups and group2 in room_groups:
                # Merge two existing groups
                room_groups[group1].extend(room_groups[group2])
                del room_groups[group2]
                merged_rooms.update(room_groups[group1])
            elif group1 in room_groups:
                room_groups[group1].append(room2)
                merged_rooms.add(room2)
            elif group2 in room_groups:
                room_groups[group2].append(room1)
                merged_rooms.add(room1)
            else:
                # Create new group
                room_groups[group1] = [room1, room2]
                merged_rooms.update([room1, room2])

        return room_groups

    def _write_merged_nodes(self, f, room_groups):
        """Write nodes for merged room groups"""
        for representative, room_list in room_groups.items():
            room_ids = [self.data.get_room_id(r) for r in room_list]
            paths_info = f"\\nPaths: {len(representative.paths)}"
            identities_info = (
                f"\\nPossible IDs: {len(representative.possible_identities)}"
            )

            f.write(
                f'  "{self.data.get_room_id(representative)}" [label="Merged Room\\nLabel: {representative.label}{paths_info}{identities_info}\\nContains: {", ".join(room_ids)}" fillcolor=lightblue style=filled];\n'
            )

    def _write_individual_nodes(self, f, merged_rooms):
        """Write nodes for individual (unmerged) rooms"""
        for room_id, room in self.data.rooms.items():
            if room not in merged_rooms:
                color = self._get_room_color(room)

                identities_info = (
                    f"\\nPossible IDs: {len(room.possible_identities)}"
                    if len(room.possible_identities) > 0
                    else ""
                )

                unconfirmed_doors = len(room.get_unconfirmed_doors())
                doors_info = (
                    f"\\nUnconfirmed doors: {unconfirmed_doors}"
                    if unconfirmed_doors > 0
                    else ""
                )

                f.write(
                    f'  "{room_id}" [label="Room {room.room_index}\\nLabel: {room.label}{identities_info}{doors_info}"{color}];\n'
                )

    def _get_room_color(self, room):
        """Get color for room node based on its status"""
        if room.confirmed_unique:
            return " fillcolor=lightgreen style=filled"
        elif len(room.possible_identities) > 0:
            return " fillcolor=lightyellow style=filled"
        else:
            return ""

    def _write_edges(self, f, room_groups, merged_rooms, show_possibilities):
        """Write edges showing door connections"""
        drawn_edges = set()

        for room_id, room in self.data.rooms.items():
            source_id = self._get_display_id(room, room_id, room_groups, merged_rooms)

            for door in range(6):
                self._write_door_edges(
                    f,
                    room,
                    door,
                    source_id,
                    room_groups,
                    merged_rooms,
                    drawn_edges,
                    show_possibilities,
                )

    def _get_display_id(self, room, room_id, room_groups, merged_rooms):
        """Get the display ID for a room (might be merged representative)"""
        if room in merged_rooms:
            representative = next(k for k, v in room_groups.items() if room in v)
            return self.data.get_room_id(representative)
        return room_id

    def _write_door_edges(
        self,
        f,
        room,
        door,
        source_id,
        room_groups,
        merged_rooms,
        drawn_edges,
        show_possibilities,
    ):
        """Write edges for a specific door"""
        confirmed_dest = room.get_door_destination(door)
        possibilities = room.get_door_possibilities(door)

        if confirmed_dest is not None:
            # Draw confirmed connection with solid line
            target_id = self._get_display_id(
                confirmed_dest,
                self.data.get_room_id(confirmed_dest),
                room_groups,
                merged_rooms,
            )

            edge_key = (source_id, target_id, door)
            if edge_key not in drawn_edges:
                f.write(
                    f'  "{source_id}" -> "{target_id}" [label="door {door}" color=black];\n'
                )
                drawn_edges.add(edge_key)

        elif show_possibilities and len(possibilities) > 1:
            # Draw multiple possibilities with dashed lines
            for possible_dest in possibilities:
                target_id = self._get_display_id(
                    possible_dest,
                    self.data.get_room_id(possible_dest),
                    room_groups,
                    merged_rooms,
                )

                edge_key = (source_id, target_id, door)
                if edge_key not in drawn_edges:
                    f.write(
                        f'  "{source_id}" -> "{target_id}" [label="door {door}?" style=dashed color=gray];\n'
                    )
                    drawn_edges.add(edge_key)

    def _render_png(self, dot_filename):
        """Render PNG from DOT file"""
        png_filename = dot_filename.replace(".dot", ".png")
        try:
            subprocess.run(
                ["dot", "-Tpng", dot_filename, "-o", png_filename], check=True
            )
            print(f"Generated {dot_filename} and {png_filename}")
        except subprocess.CalledProcessError:
            print(f"Generated {dot_filename} (dot command failed for PNG generation)")
        except FileNotFoundError:
            print(
                f"Generated {dot_filename} (dot command not found for PNG generation)"
            )


class TextRenderer:
    """Simple text-based renderer for room maps"""

    def __init__(self, problem_data, identity_analyzer):
        self.data = problem_data
        self.analyzer = identity_analyzer

    def print_room_summary(self):
        """Print a text summary of the room map"""
        print(f"\nRoom Map Summary ({len(self.data.rooms)} rooms):")
        print("=" * 50)

        for room_id, room in self.data.rooms.items():
            self._print_room_details(room_id, room)

        self._print_identity_summary()

    def _print_room_details(self, room_id, room):
        """Print details for a single room"""
        status = (
            "UNIQUE"
            if room.confirmed_unique
            else f"AMBIGUOUS({len(room.possible_identities)})"
        )
        print(f"\n{room_id}: Label {room.label} [{status}]")

        # Door connections
        for door in range(6):
            confirmed = room.get_door_destination(door)
            possibilities = room.get_door_possibilities(door)

            if confirmed:
                dest_id = self.data.get_room_id(confirmed)
                print(f"  Door {door}: -> {dest_id} (confirmed)")
            elif len(possibilities) > 1:
                dest_ids = [self.data.get_room_id(p) for p in possibilities]
                print(f"  Door {door}: -> {dest_ids} (possible)")
            elif len(possibilities) == 1:
                dest_id = self.data.get_room_id(possibilities[0])
                print(f"  Door {door}: -> {dest_id} (unconfirmed)")
            else:
                print(f"  Door {door}: unexplored")

    def _print_identity_summary(self):
        """Print summary of room identity analysis"""
        self.analyzer.print_identity_summary()
