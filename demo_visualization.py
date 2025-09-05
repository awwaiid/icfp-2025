#!/usr/bin/env python3

from problem import Problem

def create_sample_data():
    """Create some sample room data to demonstrate the visualization"""
    p = Problem(room_count=3)
    
    # Add some sample observations to build room connections
    # These represent paths taken through rooms with their labels
    
    # Path 1: Start at room labeled 0, take door 1, end at room labeled 1
    #p.add_observation([1], [0, 1])
    
    # Path 2: Start at room labeled 0, take door 2, end at room labeled 2  
    #p.add_observation([2], [0, 2])
    
    # Path 3: More complex path - start at 0, door 1 to label 1, door 3 to label 0
    #p.add_observation([1, 3], [0, 1, 0])
    
    # Path 4: Another path showing potential room identity ambiguity
    #p.add_observation([2, 0], [0, 2, 1])
    
    # Path 5: Longer path to show more connections
    #p.add_observation([1, 4, 2], [0, 1, 3, 2])
    
    # Path 6: Return path that might create ambiguity
    #p.add_observation([0, 1, 5], [1, 2, 1, 0])
    
    return p

def demo_all_views():
    """Demonstrate all visualization views"""
    print("Creating sample problem with room observations...")
    p = create_sample_data()
    
    print(f"\nCreated problem with {len(p.rooms)} rooms and {len(p.observations)} observations")
    print("\n" + "="*80)
    print("DEMONSTRATION OF ALL VISUALIZATION VIEWS")
    print("="*80)
    
    # Show each view type
    views = ["summary", "matrix", "doors", "map", "details"]
    
    for view in views:
        print(f"\n📋 SHOWING VIEW: {view.upper()}")
        print("-" * 40)
        p.print_state(view)
        input("Press Enter to continue to next view...")
    
    print("\n🎯 SHOWING ALL VIEWS AT ONCE:")
    print("-" * 40)
    p.print_state("all")

def interactive_demo():
    """Interactive demo allowing user to explore different views"""
    p = create_sample_data()
    
    print("🏠 Interactive Room Visualization Demo")
    print("="*50)
    print(f"Loaded problem with {len(p.rooms)} rooms")
    print("\nAvailable commands:")
    print("  summary  - Show room summary")
    print("  matrix   - Show connection matrix") 
    print("  doors    - Show door usage stats")
    print("  map      - Show ASCII map")
    print("  details  - Show detailed room info")
    print("  all      - Show all views")
    print("  add      - Add a new observation")
    print("  quit     - Exit demo")
    
    while True:
        print("\n" + "-"*30)
        command = input("Enter command: ").strip().lower()
        
        if command == "quit":
            print("Goodbye!")
            break
        elif command in ["summary", "matrix", "doors", "map", "details", "all"]:
            print()
            p.print_state(command)
        elif command == "add":
            try:
                print("\nAdd a new observation (path through doors to room labels)")
                path_str = input("Enter path (e.g., '1,2,3' for doors 1,2,3): ")
                rooms_str = input("Enter room labels (e.g., '0,1,2,0' - one more than path): ")
                
                path = [int(x.strip()) for x in path_str.split(',') if x.strip()]
                rooms = [int(x.strip()) for x in rooms_str.split(',') if x.strip()]
                
                if len(rooms) == len(path) + 1:
                    p.add_observation(path, rooms)
                    print(f"✓ Added observation: path={path}, rooms={rooms}")
                    print(f"Total rooms now: {len(p.rooms)}")
                else:
                    print("❌ Error: Room labels should be exactly one more than path length")
            except ValueError:
                print("❌ Error: Please enter valid numbers separated by commas")
        else:
            print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_demo()
    else:
        demo_all_views()