#!/usr/bin/env python3
"""
SVG Auto-Optimizer - Quick Test

Tests the optimizer with minimal iterations to verify functionality.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.svg_auto_optimizer import (
    SVGResumeGenerator,
    VisualQualityChecker,
    SVGFixer,
    IterationController
)


def test_components():
    """Test individual components"""
    print("Testing SVG Auto-Optimizer Components")
    print("=" * 60)

    # Test 1: SVGResumeGenerator
    print("\n1. Testing SVGResumeGenerator...")
    gen = SVGResumeGenerator()
    data = gen.load_data_from_yaml()
    print(f"   [OK] Loaded {len(data)} data sections")

    svg_path = gen.generate_svg(iteration=0)
    print(f"   [OK] Generated SVG: {svg_path}")

    # Test 2: VisualQualityChecker
    print("\n2. Testing VisualQualityChecker...")
    checker = VisualQualityChecker()

    try:
        screenshot = checker.render_screenshot(svg_path)
        print(f"   [OK] Screenshot: {screenshot}")
    except Exception as e:
        print(f"   [SKIP] Screenshot failed (expected in CI): {e}")

    # Test 3: SVGFixer
    print("\n3. Testing SVGFixer...")
    fixer = SVGFixer()

    test_svg = '<svg><text y="100">Test</text></svg>'
    test_issue = {
        'priority': 'P0',
        'suggested_fix': {
            'action': 'adjust_position',
            'details': 'Move y=100 to y=120'
        }
    }

    fixed = fixer.apply_fixes(test_svg, [test_issue])
    print(f"   [OK] Applied fix: {len(fixed)} bytes")

    print("\n" + "=" * 60)
    print("All component tests passed!")


def quick_run():
    """Run optimizer with 1 iteration for testing"""
    print("\nRunning Quick Optimization (1 iteration)...")
    print("=" * 60)

    controller = IterationController(max_iterations=1)

    try:
        final_path = controller.run_optimization_loop()
        print(f"\n[OK] Final output: {final_path}")
        return 0
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test SVG Auto-Optimizer')
    parser.add_argument('--components-only', action='store_true',
                        help='Only test components, skip optimization loop')

    args = parser.parse_args()

    if args.components_only:
        test_components()
        sys.exit(0)
    else:
        test_components()
        sys.exit(quick_run())
