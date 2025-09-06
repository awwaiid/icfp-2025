# Ambiguously - Minimal Fingerprint-Based Room Exploration

This is a minimal, clean implementation focused on **room fingerprints** for identification and exploration.

## Core Concept

Each room is identified by a **fingerprint** consisting of:
- **Room label** (0, 1, 2, 3) 
- **Door destination labels** (what rooms each of the 6 doors leads to)

**Format**: `label-door0door1door2door3door4door5`

**Examples**:
- `1-210012` = Room with label 1, door 0→room with label 2, door 1→room with label 1, etc.
- `2-??1??3` = Room with label 2, doors 0&1 unknown, door 2→label 1, doors 3&4 unknown, door 5→label 3

## Data Structures

### Room
- `label`: Room's own label  
- `paths`: List of paths used to reach this room
- `door_labels`: Array of 6 destination labels (one per door)
- `get_fingerprint()`: Returns fingerprint string

### Problem  
- `possible_rooms`: List of discovered room possibilities
- `bootstrap()`: Discover starting room by exploring all 6 doors
- `explore_incomplete_rooms()`: Fill in missing door information
- `print_fingerprints()`: Show all room fingerprints

## Algorithm

1. **Bootstrap**: Start from room 0, explore all 6 doors to get initial fingerprint
2. **Incremental**: For each incomplete room, explore unknown doors  
3. **Fingerprint Tracking**: Maintain clear picture of what we know vs don't know
4. **Path-Based Identity**: Rooms reached by different paths might be the same

## Usage

```bash
# Start REPL
uv run python ambiguously/start_repl.py

# Or run example
uv run python -m ambiguously.example
```

```python
p = Problem(room_count=6)
p.bootstrap("primus")       # Discover starting room
p.print_fingerprints()      # Show: Room 0: 1-210012 [COMPLETE]

p.explore_incomplete_rooms() # Fill in any missing doors
p.print_fingerprints()      # Show updated fingerprints
```

## Benefits

- **Visual**: Easy to see exactly what we know and don't know
- **Minimal**: Clean, simple implementation  
- **Incremental**: Clear progression from incomplete to complete
- **Pattern Recognition**: Identical fingerprints = identical rooms
- **Debug-Friendly**: Fingerprint strings are human-readable

## Example Output

```
=== Room Fingerprints (3 rooms) ===
Room 0: 0-022001 [COMPLETE] paths=[[]]
Room 1: 2-?????  [PARTIAL (0/6)] paths=[[0]]  
Room 2: 1-?????  [PARTIAL (0/6)] paths=[[2]]
```

This shows:
- **Room 0**: Label 0, all doors mapped, starting room (empty path)
- **Room 1**: Label 2, no doors mapped yet, reached via door 0
- **Room 2**: Label 1, no doors mapped yet, reached via door 2

Perfect for understanding the problem step-by-step and seeing exactly what information we have!