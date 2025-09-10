#!/usr/bin/env python3

import os
import sys
sys.path.append('slowly')
sys.path.append('ambiguously')

from ambiguously.api_client import ApiClient

def test_identity():
    client = ApiClient()
    client.base_url = "http://127.0.0.1:8080"
    client.select_problem("simple-2")
    
    print("=== Testing if [] and [0,0] are the same room ===")
    
    # Test A: Edit root, then navigate to [0,0]
    result = client.explore(["[1]00"])
    print(f"Plan '[1]00' (edit root, navigate to [0,0]): {result['results'][0]}")
    
    # Test B: Navigate to [0,0], edit, then navigate back to root  
    result = client.explore(["00[1]"])
    print(f"Plan '00[1]' (go to [0,0], edit): {result['results'][0]}")
    
    # Test C: Reset and test the reverse
    client.select_problem("simple-2")  # Reset
    result = client.explore(["00[2]"])
    print(f"Plan '00[2]' (go to [0,0], edit to 2): {result['results'][0]}")
    
    # If [] and [0,0] are the same room, then editing root should show up at [0,0]
    # and editing [0,0] should show up at root
    print("\nIf rooms are the same:")
    print("- '[1]00' should end with 1 (edit root, then see it at [0,0])")
    print("- '00[1]' should end with 1 (edit [0,0], should stay at edited room)")
    print()
    print("Checking the most direct test...")
    
    # Most direct test: Edit root, navigate away and back via different path
    client.select_problem("simple-2")  # Reset
    result = client.explore(["[3]100"])  # Edit root to 3, go to other room, come back via [0,0]
    print(f"Plan '[3]100' (edit root to 3, door 1, door 0, door 0): {result['results'][0]}")

if __name__ == "__main__":
    test_identity()