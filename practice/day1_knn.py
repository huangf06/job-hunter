# Day 1: KNN Recovery Exercise

"""
DAY 1 SPECIAL ASSIGNMENT — 2026-03-06

This is the EXACT type of problem you failed at FareHarbor.
Solve it cold. No looking at solutions. Time yourself.

Problem: K-Nearest Neighbors
Given a list of 2D points and a query point, return the K closest points.

Example:
    points = [(1, 2), (3, 4), (0, 0), (5, 1), (2, 3)]
    query = (2, 2)
    k = 3
    → returns 3 closest points to (2, 2)

Constraints:
    - Use Euclidean distance
    - If tied, any order is fine
    - k <= len(points)

START TIMER NOW. Target: < 15 minutes.
"""

import math


def knn(points: list[tuple], query: tuple, k: int) -> list[tuple]:
    """
    Find k nearest neighbors to query point.

    Args:
        points: list of (x, y) tuples
        query: (x, y) tuple
        k: number of neighbors
    Returns:
        list of k closest (x, y) tuples
    """
    # YOUR CODE HERE
    pass


# --- Test Cases ---
if __name__ == "__main__":
    # Test 1: Basic
    points = [(1, 2), (3, 4), (0, 0), (5, 1), (2, 3)]
    result = knn(points, (2, 2), 3)
    print(f"Test 1: {result}")
    # Expected: 3 closest to (2,2) → (1,2), (2,3), (3,4) in some order

    # Test 2: k=1
    result = knn(points, (0, 0), 1)
    print(f"Test 2: {result}")
    # Expected: [(0, 0)]

    # Test 3: k = len(points)
    result = knn(points, (0, 0), len(points))
    print(f"Test 3: {result}")
    # Expected: all points

    # Test 4: Negative coordinates
    points2 = [(-1, -1), (1, 1), (2, 2), (-3, -3)]
    result = knn(points2, (0, 0), 2)
    print(f"Test 4: {result}")
    # Expected: (-1,-1) and (1,1)

    print("\nDone! Record your time in practice/log.md")
