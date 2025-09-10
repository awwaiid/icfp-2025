#!/usr/bin/env python3

import os
import sys
sys.path.append('slowly')
sys.path.append('ambiguously')

from ambiguously.api_client import ApiClient

def debug_mock():
    client = ApiClient()
    client.base_url = "http://127.0.0.1:8080"
    client.select_problem("simple-2")
    
    print("=== Understanding mock server behavior ===")
    
    # Test 1: Basic navigation
    result = client.explore(["00"])  
    print(f"Plan '00': {result['results'][0]}")
    
    # Test 2: Edit without further navigation
    result = client.explore(["[1]"])
    print(f"Plan '[1]': {result['results'][0]}")
    
    # Test 3: Navigate then edit without further navigation  
    result = client.explore(["00[1]"])
    print(f"Plan '00[1]': {result['results'][0]}")
    
    # Test 4: Edit then navigate 
    result = client.explore(["[1]0"])
    print(f"Plan '[1]0': {result['results'][0]}")
    
    # Test 5: Navigate, edit, then navigate again
    result = client.explore(["0[1]0"])  
    print(f"Plan '0[1]0': {result['results'][0]}")
    
    print("\n=== Key insight ===")
    print("If plan '00[1]' gives [0, 0, 0, 1], this means:")
    print("- Position 0: starting room (label 0)")
    print("- Position 1: after door 0 (label 0)")  
    print("- Position 2: after door 0 again (label 0)")
    print("- Position 3: after edit to 1 (shows the edit confirmation)")
    print("")
    print("But if we stay at the edited room, subsequent references should show the new label.")
    print("The question is: does position 3 represent the edited room's new actual label,")
    print("or is it just an 'echo' confirming the edit was made?")
    
    # Test to clarify: navigate to a room, edit it, then navigate away and back
    result = client.explore(["0[1]00"])
    print(f"\nPlan '0[1]00' (edit room then navigate away and back): {result['results'][0]}")

if __name__ == "__main__":
    debug_mock()