#!/usr/bin/env python3
"""
FareHarbor Live Coding Interview - Practice Script
Run this to test your Python fundamentals before the interview.

Usage:
    python 07_practice_drills.py

Each section has a problem. Try to solve it WITHOUT looking at the solution.
Uncomment the solution to check your answer.
"""

import time
from functools import wraps


def section(title):
    """Decorator to mark practice sections"""
    def decorator(func):
        @wraps(func)
        def wrapper():
            print(f"\n{'='*60}")
            print(f"  {title}")
            print(f"{'='*60}\n")
            func()
        return wrapper
    return decorator


# ============================================================================
# SECTION 1: DECORATORS
# ============================================================================

@section("1. DECORATORS")
def drill_decorators():
    print("PROBLEM: Write a decorator that times function execution")
    print("Expected output: 'function_name took X.XX seconds'")
    print()

    # YOUR CODE HERE
    # def timer(func):
    #     ...

    # SOLUTION (uncomment to check)
    # def timer(func):
    #     @wraps(func)
    #     def wrapper(*args, **kwargs):
    #         start = time.time()
    #         result = func(*args, **kwargs)
    #         elapsed = time.time() - start
    #         print(f"{func.__name__} took {elapsed:.2f} seconds")
    #         return result
    #     return wrapper
    #
    # @timer
    # def slow_function():
    #     time.sleep(0.1)
    #     return "done"
    #
    # slow_function()


# ============================================================================
# SECTION 2: GENERATORS
# ============================================================================

@section("2. GENERATORS")
def drill_generators():
    print("PROBLEM: Write a generator that yields Fibonacci numbers")
    print("fibonacci(5) should yield: 0, 1, 1, 2, 3")
    print()

    # YOUR CODE HERE
    # def fibonacci(n):
    #     ...

    # SOLUTION (uncomment to check)
    # def fibonacci(n):
    #     a, b = 0, 1
    #     for _ in range(n):
    #         yield a
    #         a, b = b, a + b
    #
    # print(list(fibonacci(5)))  # [0, 1, 1, 2, 3]


# ============================================================================
# SECTION 3: CONTEXT MANAGERS
# ============================================================================

@section("3. CONTEXT MANAGERS")
def drill_context_managers():
    print("PROBLEM: Write a context manager that prints 'START' and 'END'")
    print("Usage: with timer_context(): ...")
    print()

    # YOUR CODE HERE
    # from contextlib import contextmanager
    # @contextmanager
    # def timer_context():
    #     ...

    # SOLUTION (uncomment to check)
    # from contextlib import contextmanager
    # @contextmanager
    # def timer_context():
    #     print("START")
    #     start = time.time()
    #     yield
    #     elapsed = time.time() - start
    #     print(f"END (took {elapsed:.2f}s)")
    #
    # with timer_context():
    #     time.sleep(0.1)


# ============================================================================
# SECTION 4: LIST COMPREHENSIONS
# ============================================================================

@section("4. LIST COMPREHENSIONS")
def drill_comprehensions():
    print("PROBLEM 1: Flatten a 2D list")
    matrix = [[1, 2], [3, 4], [5, 6]]
    print(f"Input: {matrix}")
    print("Expected: [1, 2, 3, 4, 5, 6]")
    print()

    # YOUR CODE HERE
    # flat = ...

    # SOLUTION (uncomment to check)
    # flat = [item for row in matrix for item in row]
    # print(f"Output: {flat}")

    print("\nPROBLEM 2: Create dict of word lengths")
    words = ["hello", "world", "python"]
    print(f"Input: {words}")
    print("Expected: {'hello': 5, 'world': 5, 'python': 6}")
    print()

    # YOUR CODE HERE
    # word_lengths = ...

    # SOLUTION (uncomment to check)
    # word_lengths = {word: len(word) for word in words}
    # print(f"Output: {word_lengths}")


# ============================================================================
# SECTION 5: CLASSES & OOP
# ============================================================================

@section("5. CLASSES & OOP")
def drill_classes():
    print("PROBLEM: Create a Temperature class with Celsius/Fahrenheit conversion")
    print("Usage: t = Temperature(0); print(t.fahrenheit)  # 32.0")
    print()

    # YOUR CODE HERE
    # class Temperature:
    #     ...

    # SOLUTION (uncomment to check)
    # class Temperature:
    #     def __init__(self, celsius):
    #         self._celsius = celsius
    #
    #     @property
    #     def fahrenheit(self):
    #         return self._celsius * 9/5 + 32
    #
    #     @fahrenheit.setter
    #     def fahrenheit(self, value):
    #         self._celsius = (value - 32) * 5/9
    #
    # t = Temperature(0)
    # print(f"0°C = {t.fahrenheit}°F")  # 32.0
    # t.fahrenheit = 212
    # print(f"212°F = {t._celsius}°C")  # 100.0


# ============================================================================
# SECTION 6: MULTI-ARMED BANDIT
# ============================================================================

@section("6. MULTI-ARMED BANDIT (ML)")
def drill_bandit():
    print("PROBLEM: Implement epsilon-greedy bandit")
    print("- n_arms: number of options")
    print("- epsilon: exploration rate")
    print("- select_arm(): choose arm (explore or exploit)")
    print("- update(arm, reward): update statistics")
    print()

    # YOUR CODE HERE
    # import numpy as np
    # class EpsilonGreedyBandit:
    #     ...

    # SOLUTION (uncomment to check)
    # import numpy as np
    # class EpsilonGreedyBandit:
    #     def __init__(self, n_arms, epsilon=0.1):
    #         self.n_arms = n_arms
    #         self.epsilon = epsilon
    #         self.counts = np.zeros(n_arms)
    #         self.values = np.zeros(n_arms)
    #
    #     def select_arm(self):
    #         if np.random.random() < self.epsilon:
    #             return np.random.randint(self.n_arms)
    #         else:
    #             return np.argmax(self.values)
    #
    #     def update(self, arm, reward):
    #         self.counts[arm] += 1
    #         n = self.counts[arm]
    #         self.values[arm] = ((n - 1) / n) * self.values[arm] + (1 / n) * reward
    #
    # # Test
    # bandit = EpsilonGreedyBandit(n_arms=3, epsilon=0.1)
    # for _ in range(10):
    #     arm = bandit.select_arm()
    #     reward = [1, 5, 3][arm]  # Arm 1 is best
    #     bandit.update(arm, reward)
    # print(f"Arm values: {bandit.values}")
    # print(f"Best arm: {np.argmax(bandit.values)}")  # Should be 1


# ============================================================================
# SECTION 7: A/B TESTING
# ============================================================================

@section("7. A/B TESTING")
def drill_ab_testing():
    print("PROBLEM: Implement deterministic A/B test assignment")
    print("- Use hash of user_id to assign variant")
    print("- 50/50 split between control and treatment")
    print()

    # YOUR CODE HERE
    # import hashlib
    # def assign_variant(user_id, experiment_name):
    #     ...

    # SOLUTION (uncomment to check)
    # import hashlib
    # def assign_variant(user_id, experiment_name):
    #     hash_input = f"{experiment_name}:{user_id}"
    #     hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    #     bucket = (hash_value % 100) / 100.0
    #     return "treatment" if bucket < 0.5 else "control"
    #
    # # Test: same user always gets same variant
    # print(assign_variant("user_123", "exp_1"))  # Should be consistent
    # print(assign_variant("user_123", "exp_1"))  # Same as above
    # print(assign_variant("user_456", "exp_1"))  # Different user


# ============================================================================
# SECTION 8: RAPID FIRE QUESTIONS
# ============================================================================

@section("8. RAPID FIRE QUESTIONS")
def drill_rapid_fire():
    questions = [
        ("What's the difference between == and is?",
         "== compares values, is compares object identity (memory address)"),

        ("What's the GIL?",
         "Global Interpreter Lock - mutex that prevents multiple threads from executing Python bytecode simultaneously"),

        ("What are *args and **kwargs?",
         "*args = variable positional arguments (tuple), **kwargs = variable keyword arguments (dict)"),

        ("Mutable vs immutable types?",
         "Immutable: int, float, str, tuple. Mutable: list, dict, set"),

        ("What's a closure?",
         "Function that captures variables from enclosing scope"),

        ("Bias-variance tradeoff?",
         "Bias = error from wrong assumptions (underfitting), Variance = error from sensitivity to data (overfitting)"),

        ("Precision vs Recall?",
         "Precision = TP/(TP+FP), Recall = TP/(TP+FN)"),

        ("How to handle imbalanced data?",
         "Resampling, class weights, use precision-recall curve instead of accuracy"),

        ("What's regularization?",
         "Penalty term in loss function to prevent overfitting. L1 = sparse, L2 = small weights"),

        ("Explain gradient boosting",
         "Ensemble method: train models sequentially, each corrects errors of previous models"),
    ]

    print("Answer each question in <30 seconds:\n")
    for i, (question, answer) in enumerate(questions, 1):
        print(f"{i}. {question}")
        input("   [Press Enter to see answer]")
        print(f"   → {answer}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   FareHarbor Live Coding Interview - Practice Drills        ║
║                                                              ║
║   Instructions:                                              ║
║   1. Try to solve each problem WITHOUT looking at solution  ║
║   2. Uncomment solution to check your answer                ║
║   3. If you can't solve it, study the solution and retry    ║
║                                                              ║
║   Goal: Muscle memory for Python fundamentals                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    drills = [
        drill_decorators,
        drill_generators,
        drill_context_managers,
        drill_comprehensions,
        drill_classes,
        drill_bandit,
        drill_ab_testing,
        drill_rapid_fire,
    ]

    for drill in drills:
        drill()
        input("\n[Press Enter to continue to next section]")

    print("\n" + "="*60)
    print("  PRACTICE COMPLETE!")
    print("="*60)
    print("\nRemember:")
    print("- Clarify requirements before coding")
    print("- Think out loud during the interview")
    print("- Test your code with examples")
    print("- Ask for hints if stuck")
    print("\nYou've got this! 💪")


if __name__ == "__main__":
    main()
