"""
API Client for the ICFP 2025 room exploration problem
"""

import json
import os
import requests
import re
from typing import List, Optional, Dict, Any, Tuple


class ApiClient:
    """Handles all API interactions with the exploration service"""

    def __init__(
        self,
        user_id: str = "awwaiid@thelackthereof.org zFPVkfKRKAgDUdmVr2Oi1A",
        base_url: Optional[str] = None,
    ):
        self.user_id = user_id
        self.base_url = base_url or os.environ.get(
            "ICFP_API_URL", "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"
        )

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

    def explore(self, plans) -> Optional[Dict[str, Any]]:
        """Explore with given plans and return parsed results
        
        Plans can be:
        - List[List[int]]: Traditional door sequences like [[0,1,2], [3,4]]  
        - List[str]: Exploration strings with label editing like ["01[2]3", "4[1]56"]
        """
        if not plans:
            print("No plans to explore!")
            return None

        # Convert plans to API format - handle both int lists and strings
        plan_strings = []
        original_plans = []
        
        for plan in plans:
            if isinstance(plan, str):
                # Already a string with potential label editing syntax
                plan_strings.append(plan)
                original_plans.append(plan)
            elif isinstance(plan, list):
                # Convert list of ints to string
                plan_string = "".join(str(door) for door in plan)
                plan_strings.append(plan_string)
                original_plans.append(plan)
            else:
                raise ValueError(f"Unknown plan type: {type(plan)}")
        
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
                        "plans": original_plans,
                        "plan_strings": plan_strings,
                        "results": result["results"],
                        "response": response,
                    }
            except json.JSONDecodeError:
                print("Failed to parse response JSON")

        return {"plans": original_plans, "plan_strings": plan_strings, "results": [], "response": response}
    
    def count_label_edits_in_plan(self, plan_string: str) -> int:
        """Count number of label edits [label] in a plan string"""
        return len(re.findall(r'\[[0-3]\]', plan_string))
    
    def parse_response_with_echoes(self, plan_string: str, response_labels: str) -> Tuple[List[int], List[int]]:
        """Parse response labels, separating actual room labels from echoes
        
        Args:
            plan_string: The exploration string sent (e.g. "0[1]23")
            response_labels: The response labels from API (e.g. "221100" if we edited a label to 1)
            
        Returns:
            Tuple of (actual_room_labels, echo_labels)
        """
        num_edits = self.count_label_edits_in_plan(plan_string)
        
        # Convert response to list of ints
        all_labels = [int(c) for c in response_labels]
        
        if num_edits == 0:
            # No edits, all labels are room labels
            return all_labels, []
        
        # The response contains num_edits extra echo labels
        # They appear in the sequence as confirmations of our edits
        # For now, assume echoes are interspersed in order of the edits
        
        # Extract the edit labels from the plan string
        edit_matches = re.findall(r'\[([0-3])\]', plan_string)
        expected_echoes = [int(label) for label in edit_matches]
        
        # Separate actual room labels from echoes
        # This is a simplified approach - in reality we might need more sophisticated parsing
        actual_labels = []
        echo_labels = []
        echo_index = 0
        
        for i, label in enumerate(all_labels):
            # Check if this label matches the next expected echo
            if echo_index < len(expected_echoes) and label == expected_echoes[echo_index]:
                echo_labels.append(label)
                echo_index += 1
            else:
                actual_labels.append(label)
        
        return actual_labels, echo_labels
