#!/usr/bin/env python3
"""
Test the big-batch approach against the local mock server
This script demonstrates:
1. Starting the mock server
2. Running the big-batch algorithm
3. Validating the results
"""

import subprocess
import time
import signal
import sys
import os
from big_batch.problem_local import LocalProblem
import requests
from threading import Thread


class MockServerManager:
    """Manages the mock server lifecycle"""

    def __init__(self):
        self.process = None

    def start(self):
        """Start the mock server in a subprocess"""
        print("🚀 Starting mock server...")

        # Start the server
        self.process = subprocess.Popen(
            [sys.executable, "mock_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/")
                if response.status_code == 200:
                    print("✅ Mock server started successfully!")
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)

        print("❌ Failed to start mock server")
        return False

    def stop(self):
        """Stop the mock server"""
        if self.process:
            print("🛑 Stopping mock server...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()
            print("✅ Mock server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def test_problem_solving(problem_name: str, expected_rooms: int):
    """Test solving a specific problem"""
    print(f"\n=== Testing Problem: {problem_name} ===")

    # Create problem instance
    problem = LocalProblem(room_count=expected_rooms)

    # Bootstrap the exploration
    problem.bootstrap(problem_name)

    print(
        f"\nAfter bootstrap - Incomplete rooms: {len(problem.get_incomplete_rooms())}"
    )

    # Run big-batch exploration until complete
    iterations = problem.explore_until_complete_batched()

    print(f"\nCompleted exploration in {iterations} iterations")
    print(f"Final incomplete rooms: {len(problem.get_incomplete_rooms())}")

    # Generate and submit solution
    try:
        correct = problem.submit_solution()
        return correct
    except Exception as e:
        print(f"Error submitting solution: {e}")
        return False


def test_api_endpoints():
    """Test basic API functionality"""
    print("\n=== Testing API Endpoints ===")

    try:
        # Test problems list
        response = requests.get("http://127.0.0.1:8080/problems")
        if response.status_code == 200:
            problems = response.json()
            print(f"✅ Available problems: {problems['available_problems']}")
        else:
            print(f"❌ Failed to get problems list: {response.status_code}")
            return False

        # Test registration
        response = requests.post(
            "http://127.0.0.1:8080/register",
            json={"name": "Test Team", "pl": "Python", "email": "test@example.com"},
        )

        if response.status_code == 200:
            team_data = response.json()
            print(f"✅ Registration successful: {team_data['id']}")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing Big-Batch Implementation with Mock Server")

    # Start mock server
    with MockServerManager():
        # Test API endpoints
        if not test_api_endpoints():
            print("❌ API endpoint tests failed")
            return False

        # Test small problem (probatio - 3 rooms)
        print("\n" + "=" * 60)
        success_probatio = test_problem_solving("probatio", 3)

        if success_probatio:
            print("✅ probatio solved correctly!")
        else:
            print("❌ probatio failed!")

        # Test medium problem (primus - 4 rooms)
        print("\n" + "=" * 60)
        success_primus = test_problem_solving("primus", 4)

        if success_primus:
            print("✅ primus solved correctly!")
        else:
            print("❌ primus failed!")

        # Summary
        print("\n" + "=" * 60)
        print("🎯 SUMMARY")
        print(f"probatio (3 rooms): {'✅ PASS' if success_probatio else '❌ FAIL'}")
        print(f"primus (4 rooms):   {'✅ PASS' if success_primus else '❌ FAIL'}")

        if success_probatio and success_primus:
            print(
                "\n🎉 All tests PASSED! Big-batch implementation is working correctly."
            )
            print("\nKey benefits demonstrated:")
            print("  ✓ Batched API calls reduce server requests")
            print("  ✓ All pending explorations sent at once")
            print("  ✓ Systematic exploration maintains correctness")
            print("  ✓ Local testing enables rapid development")
            return True
        else:
            print("\n❌ Some tests failed. Check the implementation.")
            return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
