#!/usr/bin/env python3

class TerminalVisualizer:
    """
    Terminal-based visualization for room states, doors, and connections.
    Provides multiple views: room details, connection matrix, and ASCII maps.
    """
    
    def __init__(self, problem):
        self.problem = problem
        self.door_symbols = ['↑', '↗', '→', '↘', '↓', '↙']  # Visual door directions
        self.connection_chars = {
            'confirmed': '●',      # Solid connection
            'possible': '◐',       # Possible connection  
            'unknown': '○',        # No connection info
            'blocked': '✗'         # No connection
        }
    
    def print_room_summary(self):
        """Print a summary of all rooms with their basic info"""
        print("=" * 60)
        print("ROOM SUMMARY")
        print("=" * 60)
        
        for room_id, room in sorted(self.problem.rooms.items()):
            identity_count = len(room.possible_identities)
            unique_status = "UNIQUE" if room.confirmed_unique else f"{identity_count} possible"
            
            print(f"Room {room.room_index:2} (Label: {room.label}) - {unique_status}")
            print(f"  ID: {room_id}")
            print(f"  Paths recorded: {len(room.paths)}")
            
            # Show door connections briefly
            door_summary = []
            for door in range(6):
                dest = room.get_door_destination(door)
                poss = room.get_door_possibilities(door)
                
                if dest:
                    door_summary.append(f"{door} → {dest.label}")
                elif len(poss) > 1:
                    labels = [str(p.label) for p in poss]
                    door_summary.append(f"{door} → {{{','.join(labels)}}}")
                elif len(poss) == 1:
                    door_summary.append(f"{door} → {poss[0].label}?")
                else:
                    door_summary.append(f"{door} → ?")
            
            print(f"  Doors: {' | '.join(door_summary)}")
            print()
    
    def print_room_details(self, room_id=None):
        """Print detailed view of a specific room or all rooms"""
        rooms_to_show = [room_id] if room_id else sorted(self.problem.rooms.keys())
        
        for rid in rooms_to_show:
            if rid not in self.problem.rooms:
                print(f"Room {rid} not found!")
                continue
                
            room = self.problem.rooms[rid]
            print("=" * 50)
            print(f"ROOM {room.room_index} (ID: {rid})")
            print("=" * 50)
            print(f"Label: {room.label}")
            print(f"Confirmed Unique: {room.confirmed_unique}")
            print(f"Possible Identities: {len(room.possible_identities)}")
            
            if room.possible_identities:
                identity_ids = []
                for other_room in room.possible_identities:
                    other_id = self.problem.get_room_id(other_room)
                    identity_ids.append(f"{other_room.room_index}({other_id})")
                print(f"  → {', '.join(identity_ids)}")
            
            print(f"\nPaths to this room: {len(room.paths)}")
            for i, (path, rooms_seq, pos) in enumerate(room.paths[:3]):  # Show first 3
                print(f"  {i+1}: {path} → {rooms_seq}")
            if len(room.paths) > 3:
                print(f"  ... and {len(room.paths) - 3} more")
            
            print("\nDOOR CONNECTIONS:")
            print("Door | Status    | Destination(s)")
            print("-" * 40)
            
            for door in range(6):
                symbol = self.door_symbols[door]
                dest = room.get_door_destination(door)
                possibilities = room.get_door_possibilities(door)
                
                if dest:
                    dest_id = self.problem.get_room_id(dest)
                    print(f" {door} {symbol} | Confirmed | Room {dest.room_index} (Label: {dest.label}, ID: {dest_id})")
                elif len(possibilities) > 1:
                    dest_info = []
                    for p in possibilities:
                        p_id = self.problem.get_room_id(p)
                        dest_info.append(f"Room {p.room_index}(L:{p.label}, {p_id})")
                    print(f" {door} {symbol} | Possible  | {' OR '.join(dest_info)}")
                elif len(possibilities) == 1:
                    p = possibilities[0]
                    p_id = self.problem.get_room_id(p)
                    print(f" {door} {symbol} | Tentative | Room {p.room_index} (Label: {p.label}, ID: {p_id})")
                else:
                    print(f" {door} {symbol} | Unknown   | ?")
            
            print()
    
    def print_connection_matrix(self):
        """Print a matrix showing all room-to-room connections"""
        rooms = list(self.problem.rooms.values())
        if not rooms:
            print("No rooms to display!")
            return
            
        print("=" * 80)
        print("CONNECTION MATRIX")
        print("=" * 80)
        print("Legend: ● = confirmed, ◐ = possible, ○ = unknown, ✗ = no connection")
        print()
        
        # Header row with room indices
        print("From\\To ", end="")
        for room in rooms:
            print(f"{room.room_index:>4}", end="")
        print()
        
        # Separator
        print("-" * (8 + len(rooms) * 4))
        
        # Each room's connections
        for from_room in rooms:
            print(f"R{from_room.room_index:>2}     ", end="")
            
            for to_room in rooms:
                if from_room == to_room:
                    print("   .", end="")  # Self
                    continue
                
                # Check all doors for connections to this room
                connection_type = 'blocked'
                for door in range(6):
                    dest = from_room.get_door_destination(door)
                    possibilities = from_room.get_door_possibilities(door)
                    
                    if dest == to_room:
                        connection_type = 'confirmed'
                        break
                    elif to_room in possibilities:
                        if connection_type != 'confirmed':
                            connection_type = 'possible'
                    elif len(possibilities) == 0:
                        if connection_type not in ['confirmed', 'possible']:
                            connection_type = 'unknown'
                
                char = self.connection_chars[connection_type]
                print(f"   {char}", end="")
            
            print()  # New line after each row
        print()
    
    def print_door_usage_summary(self):
        """Print summary of how doors are used across all rooms"""
        print("=" * 60)
        print("DOOR USAGE SUMMARY")
        print("=" * 60)
        
        door_stats = {i: {'confirmed': 0, 'possible': 0, 'unknown': 0} 
                     for i in range(6)}
        
        for room in self.problem.rooms.values():
            for door in range(6):
                dest = room.get_door_destination(door)
                possibilities = room.get_door_possibilities(door)
                
                if dest:
                    door_stats[door]['confirmed'] += 1
                elif len(possibilities) > 1:
                    door_stats[door]['possible'] += 1
                else:
                    door_stats[door]['unknown'] += 1
        
        print("Door | Symbol | Confirmed | Possible | Unknown | Total")
        print("-" * 55)
        
        for door in range(6):
            symbol = self.door_symbols[door]
            stats = door_stats[door]
            total = sum(stats.values())
            print(f" {door}   |   {symbol}    |    {stats['confirmed']:2}     |    {stats['possible']:2}    |   {stats['unknown']:2}   | {total:3}")
        
        print()
    
    def print_ascii_map(self, max_width=80, max_height=20):
        """Print an ASCII representation of the room layout"""
        print("=" * 60)
        print("ASCII ROOM MAP")
        print("=" * 60)
        print("Note: This is a conceptual layout, not spatially accurate")
        print()
        
        if not self.problem.rooms:
            print("No rooms to display!")
            return
        
        rooms = list(self.problem.rooms.values())
        
        # Simple grid placement - arrange rooms in a grid
        import math
        grid_size = math.ceil(math.sqrt(len(rooms)))
        
        # Create grid
        grid = [['   ' for _ in range(grid_size * 4)] for _ in range(grid_size * 3)]
        room_positions = {}
        
        # Place rooms in grid
        for i, room in enumerate(rooms):
            row = (i // grid_size) * 3 + 1
            col = (i % grid_size) * 4 + 1
            
            if row < len(grid) and col < len(grid[0]) - 2:
                room_positions[room] = (row, col)
                # Room representation: [Label]
                grid[row][col] = f"[{room.label}]"[0:3]
        
        # Add connections
        for room in rooms:
            if room not in room_positions:
                continue
                
            row, col = room_positions[room]
            
            for door in range(6):
                dest = room.get_door_destination(door)
                if dest and dest in room_positions:
                    dest_row, dest_col = room_positions[dest]
                    
                    # Simple connection drawing (just mark direction)
                    if door == 0 and row > 0:  # Up
                        grid[row-1][col+1] = ' ↑ '
                    elif door == 2 and col < len(grid[0]) - 4:  # Right  
                        grid[row][col+3] = '→'
                    elif door == 4 and row < len(grid) - 2:  # Down
                        grid[row+1][col+1] = ' ↓ '
                    elif door == 1 and row > 0 and col < len(grid[0]) - 4:  # Up-right
                        grid[row-1][col+3] = '↗'
        
        # Print grid
        for row in grid:
            if any(cell != '   ' for cell in row):
                print(''.join(row).rstrip())
        
        print("\nRoom Legend:")
        for room in rooms[:10]:  # Show first 10 rooms
            pos = room_positions.get(room, (None, None))
            print(f"  [{room.label}] = Room {room.room_index} at position {pos}")
        
        if len(rooms) > 10:
            print(f"  ... and {len(rooms) - 10} more rooms")
        print()
    
    def print_all(self):
        """Print all visualization views"""
        self.print_room_summary()
        self.print_connection_matrix() 
        self.print_door_usage_summary()
        self.print_ascii_map()
        
        print("=" * 60)
        print("DETAILED ROOM VIEWS")
        print("=" * 60)
        self.print_room_details()