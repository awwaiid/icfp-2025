#!/usr/bin/env python3
"""
Test fingerprint display during real exploration
"""

import sys
sys.path.append('.')

from ambiguously.problem import Problem

def test_real_exploration_fingerprints():
    """Test fingerprint display during actual exploration"""
    print("=== Testing Fingerprint Display During Real Exploration ===")
    
    problem = Problem(room_count=6)
    
    print("Step 1: Bootstrap exploration")
    try:
        problem.bootstrap("primus")
        
        print(f"\nStep 2: Run a few exploration iterations to see disambiguation in action")
        
        for iteration in range(2):
            print(f"\n--- Exploration iteration {iteration + 1} ---")
            
            # Check current fingerprints before exploration
            complete_rooms = problem.room_manager.get_complete_rooms()
            print(f"Complete rooms before: {len(complete_rooms)}")
            
            # Do exploration
            problem.explore_incomplete_rooms()
            
            # Check fingerprints after
            complete_rooms = problem.room_manager.get_complete_rooms()
            print(f"Complete rooms after: {len(complete_rooms)}")
            
            # Look for disambiguation IDs
            disambiguated_count = 0
            for room in complete_rooms:
                if hasattr(room, 'disambiguation_id') and room.disambiguation_id is not None:
                    disambiguated_count += 1
            
            if disambiguated_count > 0:
                print(f"🎯 Found {disambiguated_count} rooms with disambiguation IDs")
                break
        
        print(f"\n=== Final Fingerprint Display ===")
        problem.print_fingerprints()
        
    except Exception as e:
        print(f"Real exploration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing real exploration with updated fingerprint display...\n")
    
    test_real_exploration_fingerprints()
    
    print("\nReal exploration fingerprint test completed!")