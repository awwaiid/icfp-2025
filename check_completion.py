#!/usr/bin/env python3
"""
Check if the current problem state is complete and should stop exploring
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem

def check_completion(observations_file="observations.json"):
    """Check if the problem is complete"""
    print("=== Checking Problem Completion Status ===")
    
    # Create problem and load observations
    problem = Problem(room_count=6)
    
    try:
        problem.load_observations(observations_file)
        print(f"Loaded observations from {observations_file}")
    except FileNotFoundError:
        print(f"Observations file {observations_file} not found - using current state")
    
    # Get current state
    complete_rooms = problem.room_manager.get_complete_rooms()
    incomplete_rooms = problem.room_manager.get_incomplete_rooms()
    
    print(f"\nCurrent state:")
    print(f"  Total rooms: {len(problem.room_manager.get_all_rooms())}")
    print(f"  Complete rooms: {len(complete_rooms)}")
    print(f"  Incomplete rooms: {len(incomplete_rooms)}")
    
    # Check unique complete rooms
    unique_fingerprints = set(room.get_fingerprint() for room in complete_rooms)
    print(f"  Unique complete room fingerprints: {len(unique_fingerprints)}")
    
    for fp in sorted(unique_fingerprints):
        print(f"    {fp}")
    
    # Check if all connections are verified
    all_verified = True
    for room in complete_rooms:
        connections = problem.room_manager.get_absolute_connections(room)
        unverified = sum(1 for conn in connections if conn is None)
        if unverified > 0:
            all_verified = False
            print(f"    {room.get_fingerprint()} has {unverified} unverified connections")
    
    # Determine if exploration should stop
    should_stop = (
        len(unique_fingerprints) >= problem.room_count 
        and all_verified
    )
    
    print(f"\n=== COMPLETION CHECK ===")
    print(f"Target room count: {problem.room_count}")
    print(f"Unique complete rooms found: {len(unique_fingerprints)}")
    print(f"All connections verified: {all_verified}")
    print(f"Should stop exploration: {should_stop}")
    
    if should_stop:
        print("🎉 EXPLORATION COMPLETE! Ready to generate solution.")
        
        # Try manual cleanup
        print(f"\nPerforming cleanup...")
        removed = problem.cleanup_redundant_rooms()
        print(f"Cleanup removed {removed} redundant rooms")
        
        # Show final state
        print(f"\nFinal state: {len(problem.room_manager.get_all_rooms())} total rooms")
        
    else:
        print("⚠️ Exploration not yet complete")
        
        # Check what exploration work remains
        unknown_connections = problem.exploration_strategy.get_unknown_connections_to_verify()
        missing_connections = problem.exploration_strategy.get_missing_connections_from_complete_rooms()
        partial_explorations = problem.exploration_strategy.get_partial_rooms_to_explore()
        
        print(f"  Unknown connections: {len(unknown_connections)}")
        print(f"  Missing connections: {len(missing_connections)}")  
        print(f"  Partial explorations: {len(partial_explorations)}")
    
    return should_stop

if __name__ == "__main__":
    import sys
    obs_file = sys.argv[1] if len(sys.argv) > 1 else "observations.json"
    check_completion(obs_file)