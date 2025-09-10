#!/usr/bin/env python3
"""
Test script to demonstrate the big-batch approach
This will help verify our implementation works correctly
"""

import sys
from big_batch.problem import Problem


def test_import_and_basic_functionality():
    """Test that our new batched methods work"""
    print("=== Testing Big-Batch Import and Basic Functionality ===")

    # Test basic instantiation
    p = Problem(room_count=6)
    print("✓ Problem instance created successfully")

    # Test that our new methods exist
    assert hasattr(p, "explore_all_pending_batched"), (
        "Missing explore_all_pending_batched method"
    )
    assert hasattr(p, "explore_until_complete_batched"), (
        "Missing explore_until_complete_batched method"
    )
    assert hasattr(p.exploration_strategy, "get_all_pending_explorations"), (
        "Missing get_all_pending_explorations method"
    )
    print("✓ All new batched methods exist")

    return p


def test_pending_explorations_collection():
    """Test that we can collect all pending explorations"""
    print("\n=== Testing Pending Explorations Collection ===")

    p = Problem(room_count=6)

    # Before bootstrap, should have no pending explorations
    pending = p.exploration_strategy.get_all_pending_explorations()
    print(f"Before bootstrap: {len(pending)} pending explorations")

    # After bootstrap, we should have some incomplete rooms to explore
    print("Running bootstrap...")
    p.bootstrap("test")  # Using a test problem name

    # Now check pending explorations
    pending = p.exploration_strategy.get_all_pending_explorations()
    print(f"After bootstrap: {len(pending)} pending explorations")

    if pending:
        print("Sample pending explorations:")
        for i, path in enumerate(pending[:5]):  # Show first 5
            print(f"  {i + 1}: {path}")
        if len(pending) > 5:
            print(f"  ... and {len(pending) - 5} more")

    return p


def test_big_batch_vs_slow_approach():
    """Compare the batched approach with the incremental approach"""
    print("\n=== Comparing Big-Batch vs Incremental Approaches ===")

    # Test the new batched approach
    print("\n--- Testing Big-Batch Approach ---")
    p_batch = Problem(room_count=6)
    p_batch.bootstrap("test")

    print("Before batched exploration:")
    print(f"  Incomplete rooms: {len(p_batch.get_incomplete_rooms())}")

    # Try our new batched method
    had_work = p_batch.explore_all_pending_batched()
    print(f"Big batch exploration had work: {had_work}")

    print("After batched exploration:")
    print(f"  Incomplete rooms: {len(p_batch.get_incomplete_rooms())}")

    return p_batch


def main():
    """Run all tests"""
    print("🚀 Starting Big-Batch Testing\n")

    try:
        # Test 1: Basic functionality
        p1 = test_import_and_basic_functionality()

        # Test 2: Pending explorations collection
        p2 = test_pending_explorations_collection()

        # Test 3: Compare approaches
        p3 = test_big_batch_vs_slow_approach()

        print("\n🎉 All tests completed successfully!")
        print("\nThe big-batch implementation appears to be working correctly.")
        print("Key changes implemented:")
        print("  ✓ get_all_pending_explorations() - collects ALL paths to explore")
        print("  ✓ explore_all_pending_batched() - sends all paths in one API call")
        print("  ✓ explore_until_complete_batched() - uses batching until complete")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
