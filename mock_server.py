#!/usr/bin/env python3
"""
Mock ICFP 2025 Contest Server
Implements the same API as the real contest server for local testing
"""

from flask import Flask, request, jsonify
import json
import time
from typing import Dict, List, Optional, Tuple
import random
import re
import os
from dataclasses import dataclass, asdict

app = Flask(__name__)


def parse_plan_with_labels(plan_str: str):
    """Parse plan string with label editing syntax like '[2]50' into a sequence of actions"""
    actions = []  # List of ('move', door) or ('edit', label) actions
    
    i = 0
    while i < len(plan_str):
        if plan_str[i] == '[':
            # Found label edit - find the closing bracket
            end_bracket = plan_str.find(']', i)
            if end_bracket == -1:
                raise ValueError(f"Unclosed label edit bracket at position {i}")
            
            # Extract the label
            label_str = plan_str[i+1:end_bracket]
            if not label_str.isdigit():
                raise ValueError(f"Invalid label in edit: [{label_str}]")
            
            label = int(label_str)
            actions.append(('edit', label))
            i = end_bracket + 1
            
        elif plan_str[i].isdigit():
            # Found a door move
            door = int(plan_str[i])
            actions.append(('move', door))
            i += 1
            
        else:
            raise ValueError(f"Invalid character in plan: {plan_str[i]}")
    
    return actions

# Mock data storage
teams = {}  # team_id -> team_data
active_problems = {}  # team_id -> problem_data


@dataclass
class Room:
    """Represents a room in the library"""

    label: int  # 2-bit integer (0-3)
    connections: List[int]  # 6 doors, each connects to a room index


@dataclass
class Problem:
    """Represents a problem instance"""

    name: str
    rooms: List[Room]
    starting_room: int
    query_count: int = 0


def load_mock_problems():
    """Load mock problems from JSON files in the mocks/ directory"""
    problems = {}
    mocks_dir = "mocks"
    
    if not os.path.exists(mocks_dir):
        print(f"Warning: {mocks_dir} directory not found, using fallback problems")
        return get_fallback_problems()
    
    try:
        for filename in os.listdir(mocks_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(mocks_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Convert JSON data to Problem object
                rooms = []
                for room_data in data['rooms']:
                    rooms.append(Room(
                        label=room_data['label'],
                        connections=room_data['connections'][:]
                    ))
                
                problem = Problem(
                    name=data['name'],
                    starting_room=data['starting_room'],
                    rooms=rooms
                )
                
                problems[data['name']] = problem
                print(f"Loaded mock problem: {data['name']} ({len(rooms)} rooms) - {data.get('description', 'No description')}")
        
        if not problems:
            print("No mock problems found in mocks/ directory, using fallback problems")
            return get_fallback_problems()
            
        return problems
        
    except Exception as e:
        print(f"Error loading mock problems: {e}, using fallback problems")
        return get_fallback_problems()


def get_fallback_problems():
    """Fallback problems if mocks/ directory is not available"""
    return {
        "probatio": Problem(
            name="probatio",
            starting_room=0,
            rooms=[
                Room(label=0, connections=[1, 2, 2, 1, 2, 2]),  # Room 0
                Room(label=1, connections=[0, 0, 1, 1, 1, 0]),  # Room 1
                Room(label=2, connections=[0, 0, 0, 0, 0, 0]),  # Room 2
            ],
        ),
        "primus": Problem(
            name="primus",
            starting_room=0,
            rooms=[
                # Simple 6-room linear layout with unambiguous connections
                Room(label=0, connections=[1, 1, 1, 1, 1, 1]),  # Room 0 (label 0): all doors lead to room 1
                Room(label=0, connections=[2, 2, 2, 2, 2, 2]),  # Room 1 (label 0): all doors lead to room 2 (duplicate of room 0)
                Room(label=1, connections=[3, 3, 3, 3, 3, 3]),  # Room 2 (label 1): all doors lead to room 3
                Room(label=1, connections=[4, 4, 4, 4, 4, 4]),  # Room 3 (label 1): all doors lead to room 4 (duplicate of room 2)
                Room(label=2, connections=[5, 5, 5, 5, 5, 5]),  # Room 4 (label 2): all doors lead to room 5
                Room(label=3, connections=[0, 0, 0, 0, 0, 0]),  # Room 5 (label 3): all doors lead back to room 0
            ],
        ),
    }


# Load mock problems from external files
MOCK_PROBLEMS = load_mock_problems()


@app.route("/", methods=["GET"])
def home():
    """Basic health check"""
    return jsonify(
        {
            "message": "Mock ICFP 2025 Contest Server",
            "endpoints": ["/register", "/select", "/explore", "/guess"],
            "available_problems": list(MOCK_PROBLEMS.keys()),
        }
    )


@app.route("/register", methods=["POST"])
def register():
    """Register a new team"""
    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Generate a simple team ID
    team_id = f"mock_team_{len(teams) + 1}_{int(time.time())}"

    teams[team_id] = {
        "name": data.get("name", ""),
        "pl": data.get("pl", ""),
        "email": data.get("email", ""),
        "registered_at": time.time(),
    }

    print(f"Registered team: {data.get('name')} with ID: {team_id}")

    return jsonify({"id": team_id})


@app.route("/select", methods=["POST"])
def select_problem():
    """Select a problem to solve"""
    data = request.get_json()

    if not data or "id" not in data or "problemName" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    team_id = data["id"]
    problem_name = data["problemName"]

    # Accept any team ID for mock testing
    if team_id not in teams:
        teams[team_id] = {"name": "Mock Team", "registered_at": time.time()}

    if problem_name not in MOCK_PROBLEMS:
        return jsonify(
            {
                "error": f"Unknown problem: {problem_name}. Available: {list(MOCK_PROBLEMS.keys())}"
            }
        ), 400

    # Create a fresh copy of the problem for this team
    problem = MOCK_PROBLEMS[problem_name]
    active_problems[team_id] = Problem(
        name=problem.name,
        starting_room=problem.starting_room,
        rooms=[Room(r.label, r.connections[:]) for r in problem.rooms],  # Deep copy
        query_count=0,
    )

    print(f"Team {team_id} selected problem: {problem_name}")

    return jsonify({"problemName": problem_name})


@app.route("/explore", methods=["POST"])
def explore():
    """Explore the library with given route plans"""
    data = request.get_json()

    if not data or "id" not in data or "plans" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    team_id = data["id"]
    plans = data["plans"]

    # Accept any team ID for mock testing
    if team_id not in teams:
        teams[team_id] = {"name": "Mock Team", "registered_at": time.time()}

    if team_id not in active_problems:
        return jsonify({"error": "No problem selected. Use /select first"}), 400

    problem = active_problems[team_id]

    # Increment query count (1 for the request + 1 for each plan as per spec)
    problem.query_count += 1 + len(plans)

    results = []

    for plan_str in plans:
        # Parse plan string into actions
        try:
            actions = parse_plan_with_labels(plan_str)
        except ValueError as e:
            return jsonify({"error": f"Invalid plan format: {plan_str} - {str(e)}"}), 400

        # Count move actions for length validation (18n max as per spec)
        move_count = sum(1 for action_type, _ in actions if action_type == 'move')
        max_length = 18 * len(problem.rooms)
        if move_count > max_length:
            return jsonify({"error": f"Plan too long: {move_count} moves > {max_length}"}), 400

        # Execute the plan - create a fresh copy of room labels for this exploration
        room_labels = []
        current_room = problem.starting_room
        
        # Create a fresh copy of the original room labels for this specific plan
        original_room_labels = [room.label for room in problem.rooms]

        # Record starting room label
        current_label = original_room_labels[current_room]
        room_labels.append(current_label)

        # Execute each action
        for action_type, action_value in actions:
            if action_type == 'move':
                door = action_value
                if not (0 <= door <= 5):
                    return jsonify({"error": f"Invalid door number: {door}"}), 400

                # Move through the door to the connected room
                current_room = problem.rooms[current_room].connections[door]

                # Validate room index
                if not (0 <= current_room < len(problem.rooms)):
                    return jsonify(
                        {"error": f"Invalid room connection: {current_room}"}
                    ), 500

                # Record the room label after move (from our temporary copy)
                current_label = original_room_labels[current_room]
                room_labels.append(current_label)

            elif action_type == 'edit':
                # Edit current room's label temporarily and record it
                edited_label = action_value
                original_room_labels[current_room] = edited_label  # Update our temporary copy
                room_labels.append(edited_label)

        results.append(room_labels)

    print(
        f"Team {team_id} explored {len(plans)} plans, query count now: {problem.query_count}"
    )

    return jsonify({"results": results, "queryCount": problem.query_count})


@app.route("/guess", methods=["POST"])
def guess():
    """Submit a candidate map"""
    data = request.get_json()

    if not data or "id" not in data or "map" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    team_id = data["id"]
    submitted_map = data["map"]

    # Accept any team ID for mock testing
    if team_id not in teams:
        teams[team_id] = {"name": "Mock Team", "registered_at": time.time()}

    if team_id not in active_problems:
        return jsonify({"error": "No problem selected. Use /select first"}), 400

    problem = active_problems[team_id]

    # Validate map format
    required_fields = ["rooms", "startingRoom", "connections"]
    for field in required_fields:
        if field not in submitted_map:
            return jsonify({"error": f"Missing map field: {field}"}), 400

    # Check if the map is correct
    correct = validate_map(submitted_map, problem)

    print(f"Team {team_id} submitted map for {problem.name}, correct: {correct}")

    # Clear the problem (as per spec)
    del active_problems[team_id]

    return jsonify({"correct": correct})


def validate_map(submitted_map: Dict, problem: Problem) -> bool:
    """Validate if the submitted map matches the actual problem"""
    try:
        # Check number of rooms
        if len(submitted_map["rooms"]) != len(problem.rooms):
            return False

        # Check starting room
        if submitted_map["startingRoom"] != problem.starting_room:
            return False

        # Check room labels
        submitted_labels = submitted_map["rooms"]
        actual_labels = [room.label for room in problem.rooms]

        if submitted_labels != actual_labels:
            return False

        # Build connection map from submitted connections
        submitted_connections = {}
        for conn in submitted_map["connections"]:
            from_room = conn["from"]["room"]
            from_door = conn["from"]["door"]
            to_room = conn["to"]["room"]
            to_door = conn["to"]["door"]

            # Add bidirectional connection
            if from_room not in submitted_connections:
                submitted_connections[from_room] = {}
            if to_room not in submitted_connections:
                submitted_connections[to_room] = {}

            submitted_connections[from_room][from_door] = to_room
            submitted_connections[to_room][to_door] = from_room

        # Check all connections match
        for room_idx, room in enumerate(problem.rooms):
            for door, target_room in enumerate(room.connections):
                if room_idx not in submitted_connections:
                    return False
                if door not in submitted_connections[room_idx]:
                    return False
                if submitted_connections[room_idx][door] != target_room:
                    return False

        return True

    except (KeyError, TypeError, ValueError) as e:
        print(f"Map validation error: {e}")
        return False


@app.route("/debug/<team_id>", methods=["GET"])
def debug_team(team_id):
    """Debug endpoint to see team state"""
    if team_id not in teams:
        return jsonify({"error": "Team not found"}), 404

    team_data = {"team": teams[team_id], "active_problem": None}

    if team_id in active_problems:
        problem = active_problems[team_id]
        team_data["active_problem"] = {
            "name": problem.name,
            "starting_room": problem.starting_room,
            "query_count": problem.query_count,
            "room_count": len(problem.rooms),
            "rooms": [
                {"label": r.label, "connections": r.connections} for r in problem.rooms
            ],
        }

    return jsonify(team_data)


@app.route("/problems", methods=["GET"])
def list_problems():
    """List available problems"""
    return jsonify(
        {
            "available_problems": list(MOCK_PROBLEMS.keys()),
            "problems": {
                name: {
                    "room_count": len(problem.rooms),
                    "starting_room": problem.starting_room,
                }
                for name, problem in MOCK_PROBLEMS.items()
            },
        }
    )


if __name__ == "__main__":
    print("🚀 Starting Mock ICFP 2025 Contest Server")
    print("Available endpoints:")
    print("  POST /register - Register a team")
    print("  POST /select - Select a problem")
    print("  POST /explore - Explore the library")
    print("  POST /guess - Submit a map")
    print("  GET /debug/<team_id> - Debug team state")
    print("  GET /problems - List available problems")
    print(f"Available problems: {list(MOCK_PROBLEMS.keys())}")

    # Run the server
    app.run(host="127.0.0.1", port=8080, debug=True)
