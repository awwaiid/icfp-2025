#!/usr/bin/env python3

import os
import sys
sys.path.append('slowly')
sys.path.append('ambiguously')

from slowly.api_client import ApiClient

def test_room_equivalence():
    client = ApiClient()
    client.base_url = "http://127.0.0.1:8080"
    
    # Select simple-2
    client.select_problem("simple-2")
    
    # Test the actual issue: paths [] and [0,0] should lead to the same room
    print("=== Testing room equivalence in simple-2 ===")
    
    # Test what each path leads to
    result = client.explore(["", "00"])
    print(f"Paths '' and '00' results: {result}")
    
    # Test the disambiguation approach: edit one room and check if it shows up in the other
    result = client.explore(["[1]", "00[1]"])
    print(f"Edit tests '[1]' and '00[1]' results: {result}")
    
    # The key insight: if rooms are the same, editing one should show up in the other
    # Let's test: go to root, edit it to 1, then navigate to [0,0] - should show 1 if same room
    result = client.explore(["[1]00"])
    print(f"Edit root then go to [0,0]: {result}")

if __name__ == "__main__":
    test_room_equivalence()