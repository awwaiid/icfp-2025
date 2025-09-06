"""
API Client for the ICFP 2025 room exploration problem
"""

import json
import requests
from typing import List, Optional, Dict, Any


class ApiClient:
    """Handles all API interactions with the exploration service"""

    def __init__(
        self,
        user_id: str = "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A",
        base_url: str = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com",
    ):
        self.user_id = user_id
        self.base_url = base_url

    def select_problem(self, problem_name: str) -> requests.Response:
        """Select a problem using the API"""
        print(f"Selecting problem {problem_name}")

        data = {"id": self.user_id, "problemName": problem_name}
        response = requests.post(
            f"{self.base_url}/select",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)
        return response

    def explore(self, plans: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Explore with given plans and return parsed results"""
        if not plans:
            print("No plans to explore!")
            return None

        # Convert plans to API format
        plan_strings = ["".join(str(door) for door in plan) for plan in plans]
        print(f"Exploring with plans: {plan_strings}")

        data = {"id": self.user_id, "plans": plan_strings}
        response = requests.post(
            f"{self.base_url}/explore",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        # Process results
        if response.status_code == 200:
            try:
                result = response.json()
                if "results" in result:
                    # Return both the plans and results for processing
                    return {
                        "plans": plans,
                        "results": result["results"],
                        "response": response,
                    }
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return {"plans": plans, "results": [], "response": response}
