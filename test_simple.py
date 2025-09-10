#!/usr/bin/env python3
"""
Simple test to verify big-batch works without all the verbose output
"""

import subprocess
import time
import signal
import sys
import os
import requests
from big_batch.problem_local import LocalProblem


def start_mock_server():
    """Start the mock server"""
    process = subprocess.Popen(
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
                return process
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    return None


def test_probatio():
    """Test the 3-room probatio problem"""
    print("Testing probatio (3 rooms)...")

    problem = LocalProblem(room_count=3)
    problem.bootstrap("probatio")

    print(f"After bootstrap: {len(problem.get_incomplete_rooms())} incomplete rooms")

    # Count exploration iterations
    iterations = problem.explore_until_complete_batched(max_iterations=5)

    incomplete_after = len(problem.get_incomplete_rooms())
    print(f"After exploration: {incomplete_after} incomplete rooms")
    print(f"Completed in {iterations} iterations")

    # Try to submit solution
    try:
        correct = problem.submit_solution()
        print(f"Solution correct: {correct}")
        return correct
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main test"""
    print("🧪 Simple Big-Batch Test")

    # Start server
    server = start_mock_server()
    if not server:
        print("❌ Failed to start server")
        return False

    try:
        success = test_probatio()

        if success:
            print("✅ SUCCESS: Big-batch implementation working!")
        else:
            print("❌ FAILED: Solution was incorrect")

        return success

    finally:
        # Stop server
        os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        server.wait()
        print("Server stopped")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
