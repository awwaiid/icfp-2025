# Connection-Based Room Exploration

This directory contains an incremental connection-based approach to room exploration. Instead of tracking complete rooms, we build a table of door-to-door connections.

## Core Concept

We start in room-0 and incrementally build a connection table where each entry represents:
- **From**: (room_id, room_label, door_number)  
- **To**: (room_id, room_label, door_number)

## Key Features

1. **Incremental Discovery**: Always start from room-0, explore all 6 doors
2. **Connection Table**: Build up from-to links as we explore
3. **Breadth-First**: Systematically explore rooms with incomplete door mappings
4. **Merge Detection**: Find identical connection patterns for room merging
5. **Confirmed vs Inferred**: Track which connections we've actually traversed

## Data Structures

### Connection
```python
@dataclass
class Connection:
    from_room_id: int
    from_room_label: int  
    from_door: int
    to_room_id: Optional[int]
    to_room_label: Optional[int]
    to_door: Optional[int]  # Unknown initially
    confirmed: bool  # True if directly traversed
```

### ConnectionTable
- Stores all connections
- Fast lookups by room_id and door
- Tracks completion statistics
- Finds mergeable patterns

## Usage

```python
from connections.connection_problem import ConnectionProblem

# Create problem
p = ConnectionProblem(room_count=6)

# Bootstrap from room-0
p.bootstrap("primus")

# Explore systematically
p.explore_breadth_first(max_iterations=10)

# View results
p.print_full_state()
p.analyze_connections()
```

## REPL

```bash
uv run python connections/start_connections_repl.py
```

## Algorithm

1. **Bootstrap**: Start at room-0, explore all 6 doors to discover:
   - Starting room label
   - 6 initial connections (from room-0 to various destinations)

2. **Breadth-First**: For each known room with incomplete door mappings:
   - Explore all 6 doors from that room
   - Add new connections to table
   - Discover new rooms to explore

3. **Connection Analysis**: 
   - Find connections with same from_label → to_label patterns
   - These represent potential room merges
   - Max connections = room_count × 6 (but will be less due to connectivity)

## Benefits

- **Incremental**: Build knowledge piece by piece
- **Systematic**: Never miss exploring a room's doors  
- **Efficient**: Focus on incomplete areas
- **Mergeable**: Clear identification of identical patterns
- **Traceable**: Know which connections are confirmed vs inferred