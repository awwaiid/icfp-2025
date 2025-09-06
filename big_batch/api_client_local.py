"""
Local API Client for testing with the mock server
"""

import json
import requests
from typing import List, Optional, Dict, Any


class LocalApiClient:
    """Handles all API interactions with the local mock server"""

    def __init__(
        self,
        user_id: str = "mock_test_user",
        base_url: str = "http://127.0.0.1:8080",
    ):
        self.user_id = user_id
        self.base_url = base_url

    def register(
        self,
        name: str = "Test Team",
        pl: str = "Python",
        email: str = "test@example.com",
    ) -> str:
        """Register a team and return the team ID"""
        print(f"Registering team: {name}")

        data = {"name": name, "pl": pl, "email": email}
        response = requests.post(
            f"{self.base_url}/register",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Registration status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            self.user_id = result["id"]
            print(f"Registered with ID: {self.user_id}")
            return self.user_id
        else:
            print(f"Registration failed: {response.text}")
            raise Exception("Registration failed")

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

    def guess(self, map_data: Dict[str, Any]) -> bool:
        """Submit a map guess"""
        print("Submitting map guess...")

        data = {"id": self.user_id, "map": map_data}
        response = requests.post(
            f"{self.base_url}/guess",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        print(f"Status: {response.status_code}")
        print(response.text)

        if response.status_code == 200:
            result = response.json()
            return result.get("correct", False)

        return False

    def debug(self) -> Dict[str, Any]:
        """Get debug information about the current team state"""
        response = requests.get(f"{self.base_url}/debug/{self.user_id}")

        if response.status_code == 200:
            return response.json()

        return {}

    def list_problems(self) -> List[str]:
        """List available problems"""
        response = requests.get(f"{self.base_url}/problems")

        if response.status_code == 200:
            result = response.json()
            return result.get("available_problems", [])

        return []
