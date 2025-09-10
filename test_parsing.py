#!/usr/bin/env python3

import os
import sys
sys.path.append('slowly')
sys.path.append('ambiguously')

from ambiguously.api_client import ApiClient

def test_parsing():
    client = ApiClient()
    client.base_url = "http://127.0.0.1:8080"
    
    # Select simple-2
    client.select_problem("simple-2")
    
    print("=== Testing parsing of plan 00[1] ===")
    result = client.explore(["00[1]"])
    print(f"Raw result: {result}")
    
    # Parse it manually
    plan = "00[1]"
    result_data = result["results"][0]
    actual_labels, echo_labels = client.parse_response_with_echoes(plan, result_data)
    
    print(f"Plan: {plan}")
    print(f"Raw result_data: {result_data}")
    print(f"Parsed actual_labels: {actual_labels}")
    print(f"Parsed echo_labels: {echo_labels}")
    print(f"Final actual label: {actual_labels[-1] if actual_labels else None}")

if __name__ == "__main__":
    test_parsing()