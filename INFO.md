# ICFP 2025 Room Exploration Problem

## Problem Overview

We are exploring a graph-based maze where:
- **Rooms** have labels (0, 1, 2, 3) but labels are not unique identifiers
- **Each room has 6 doors** (numbered 0-5) 
- **Doors connect to other rooms** (could be the same room)
- **Goal**: Map the complete room connectivity to submit a solution
- **Constraint**: Limited number of rooms (typically 6) but unknown connectivity

## API Interface

### Endpoints
- **`/select`**: Choose a problem to work on
- **`/explore`**: Submit exploration plans, get back room sequences  
- **`/guess`**: Submit final room map solution

### Exploration API
- **Input**: Array of plans (each plan is a string of door numbers like "012")
- **Output**: Array of room label sequences for each plan
- **Example**: Plan "01" → `[0, 2, 1]` means "start in room with label 0, door 0 leads to label 2, door 1 leads to label 1"

## Key Challenges

### 1. **Room Identity Ambiguity**
- Multiple rooms can have the same label
- Must determine which rooms with identical labels are actually the same physical room
- Evidence for merging: identical door connection patterns
- Evidence against merging: different door connection patterns

### 2. **Incremental Discovery** 
- Can't see the full graph upfront
- Must build understanding through limited API calls
- Each exploration gives partial information
- Must decide where to explore next based on incomplete knowledge

### 3. **Connection Completeness**
- API tells us "door X leads to room with label Y"
- API doesn't tell us "door X leads to door Z in room Y" 
- Bidirectional connection info requires separate exploration

## Approaches Tried

### 1. **Room-Based Approach** (`problem.py`, `room.py`)
**Strategy**: Create Room objects, track paths, merge identical rooms
**Data Structure**: 
```python
class Room:
    label: int
    doors: List[Room]  # 6 doors pointing to other rooms
    paths: List[tuple]  # All paths that led here
    possible_identities: Set[Room]  # Rooms this might be identical to
```

**Pros**: 
- Natural object-oriented representation
- Clear room identity tracking
- Path history for analysis

**Cons**:
- Complex room merging logic
- Difficult to handle ambiguous connections
- Can create duplicate rooms unnecessarily

### 2. **Modular Approach** (`modular/`)
**Strategy**: Separate concerns into pluggable components
**Components**:
- **Core**: Pure data structures (Room, ProblemData)
- **Analysis**: Room identity analysis and merging
- **Strategies**: Different exploration algorithms (systematic, random, adaptive)  
- **Visualization**: Graphviz rendering

**Benefits**:
- Clean separation of concerns
- Multiple strategies can be tested in parallel
- Easy to extend with new approaches
- Good for collaborative development

### 3. **Connection-Based Approach** (`connections/`)
**Strategy**: Build table of door-to-door connections instead of room objects
**Data Structure**:
```python
class Connection:
    from_room_id: int
    from_room_label: int  
    from_door: int
    to_room_id: Optional[int]
    to_room_label: Optional[int]
    to_door: Optional[int]  # Often unknown
    confirmed: bool  # Actually traversed vs inferred
```

**Algorithm**:
1. Bootstrap from room-0, explore all 6 doors
2. For each discovered room, explore all 6 doors
3. Build complete connection table
4. Identify mergeable connection patterns

**Pros**:
- Systematic and complete
- Clear completion criteria  
- Easy to spot identical patterns
- Incremental progress tracking

**Cons**:
- Missing `to_door` information in many cases
- May create more room instances than necessary
- Connection table can get large

## Exploration Strategies

### Systematic Strategies
1. **Depth-First**: Explore all paths up to depth N
2. **Breadth-First**: Explore from each known room systematically
3. **Tree Expansion**: Follow unexplored doors from known rooms

### Random/Adaptive Strategies  
1. **Pure Random Walk**: Random door choices
2. **Biased Random**: Random biased toward unexplored areas
3. **Adaptive**: Switch between strategies based on progress

### Targeted Strategies
1. **Identity-Focused**: Prioritize exploring rooms with ambiguous identities
2. **Connection-Completion**: Focus on completing partial connections
3. **Cycle-Detection**: Use path length > room_count to identify revisits

## Key Insights

### Room Identity Resolution
- **Same label + same door patterns** = likely same room
- **Same label + different door patterns** = definitely different rooms  
- **Path length > room_count** = must contain cycles (revisited rooms)
- **Bidirectional verification**: If A→B and B→A with same labels, confirms connection

### Exploration Efficiency
- **Front-loading**: Explore all doors from known rooms before going deeper
- **Completion tracking**: Know exactly what's been explored vs guessed
- **Pattern recognition**: Identical connection patterns indicate room merging opportunities

### API Optimization
- **Batch exploration**: Explore multiple doors in single API call
- **Path reuse**: Don't re-explore known connections
- **Strategic planning**: Target exploration to resolve ambiguities

## Recommended Next Steps

### 1. **Hybrid Approach**
Combine connection-based discovery with room-based analysis:
- Use connection table for systematic exploration
- Use room objects for identity analysis and merging
- Convert connection table to room graph for final solution

### 2. **Bidirectional Exploration**
To complete connection information:
- For each connection A→B, explore from B to find reverse connection B→A  
- Use this to determine exact door-to-door mappings
- May require longer paths or different exploration strategies

### 3. **Solution Generation**
Need to convert exploration data to final guess format:
```json
{
  "rooms": [int],           // List of room numbers
  "startingRoom": int,      // Starting room number  
  "connections": [          // Door-to-door connections
    {
      "from": {"room": int, "door": int},
      "to": {"room": int, "door": int}
    }
  ]
}
```

### 4. **Validation and Testing**
- **Mock API**: Test strategies against known small graphs
- **Consistency checking**: Verify connection table consistency
- **Completion metrics**: Track progress toward full mapping

## Current Status

### Working Systems
- ✅ **Connection-based exploration**: Systematic room discovery
- ✅ **Modular framework**: Multiple strategy support  
- ✅ **Visualization**: Graphviz room mapping
- ✅ **Data persistence**: Save/load exploration results

### Known Issues  
- ❓ **Incomplete connections**: Missing `to_door` information
- ❓ **Room merging**: Need better heuristics for identical room detection
- ❓ **Solution format**: Need converter from exploration data to guess format
- ❓ **Optimization**: Minimize API calls while maximizing information

### Next Priorities
1. **Complete connection-based exploration** on several test problems
2. **Develop solution generator** from connection table to guess format
3. **Test and validate** solutions against API
4. **Optimize exploration** strategies based on success rates