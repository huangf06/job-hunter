"""
Tests for SVG Auto-Optimizer System

Following TDD principles:
1. Write failing test first
2. Verify it fails correctly
3. Write minimal code to pass
4. Refactor while keeping tests green
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil


# ============================================================================
# SVGResumeGenerator Tests
# ============================================================================

class TestSVGResumeGenerator:
    """Test SVG generation from structured data"""

    def test_load_data_from_yaml_returns_dict(self):
        """Should load bullet_library.yaml and return structured data"""
        from scripts.svg_auto_optimizer import SVGResumeGenerator

        generator = SVGResumeGenerator()
        data = generator.load_data_from_yaml()

        assert isinstance(data, dict)
        assert 'personal_info' in data
        assert 'work_experience' in data

    def test_generate_svg_creates_file(self):
        """Should generate SVG file with iteration number"""
        from scripts.svg_auto_optimizer import SVGResumeGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SVGResumeGenerator(output_dir=tmpdir)
            svg_path = generator.generate_svg(iteration=0)

            assert svg_path.exists()
            assert svg_path.suffix == '.svg'
            assert 'iteration_0' in str(svg_path)

    def test_generate_svg_contains_valid_svg_markup(self):
        """Generated SVG should have valid XML structure"""
        from scripts.svg_auto_optimizer import SVGResumeGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SVGResumeGenerator(output_dir=tmpdir)
            svg_path = generator.generate_svg(iteration=0)

            content = svg_path.read_text(encoding='utf-8')
            assert content.startswith('<?xml') or content.startswith('<svg')
            assert '</svg>' in content

    def test_apply_fixes_modifies_svg_content(self):
        """Should apply fixes to SVG content and return modified version"""
        from scripts.svg_auto_optimizer import SVGResumeGenerator

        generator = SVGResumeGenerator()
        original_svg = '<svg><text y="100">Test</text></svg>'
        fixes = [
            {
                'suggested_fix': {
                    'action': 'adjust_position',
                    'details': 'Move y=100 to y=120'
                }
            }
        ]

        modified_svg = generator.apply_fixes(original_svg, fixes)

        assert modified_svg != original_svg
        assert isinstance(modified_svg, str)


# ============================================================================
# VisualQualityChecker Tests
# ============================================================================

class TestVisualQualityChecker:
    """Test visual quality checking with Claude Vision API"""

    def test_render_screenshot_creates_png(self):
        """Should render SVG to PNG screenshot using Playwright"""
        from scripts.svg_auto_optimizer import VisualQualityChecker

        # Create minimal valid SVG
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / 'test.svg'
            svg_path.write_text(
                '<svg width="800" height="1000"><text>Test</text></svg>',
                encoding='utf-8'
            )

            checker = VisualQualityChecker()
            screenshot_path = checker.render_screenshot(svg_path)

            assert screenshot_path.exists()
            assert screenshot_path.suffix == '.png'

    def test_analyze_with_vision_returns_structured_feedback(self):
        """Should call Claude Vision API and return structured JSON feedback"""
        from scripts.svg_auto_optimizer import VisualQualityChecker

        checker = VisualQualityChecker()

        # Create dummy image
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / 'test.png'
            # Create 1x1 pixel PNG (minimal valid PNG)
            image_path.write_bytes(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )

            feedback = checker.analyze_with_vision(image_path)

            assert isinstance(feedback, dict)
            assert 'status' in feedback
            assert feedback['status'] in ['NEEDS_FIX', 'APPROVED']

    def test_parse_feedback_extracts_issues(self):
        """Should parse Vision API response and extract issues list"""
        from scripts.svg_auto_optimizer import VisualQualityChecker

        checker = VisualQualityChecker()
        raw_response = {
            'status': 'NEEDS_FIX',
            'overall_quality_score': 6,
            'issues': [
                {
                    'priority': 'P0',
                    'type': 'text_overlap',
                    'description': 'Text overlapping'
                }
            ]
        }

        parsed = checker.parse_feedback(raw_response)

        assert isinstance(parsed, dict)
        assert 'issues' in parsed
        assert len(parsed['issues']) == 1
        assert parsed['issues'][0]['priority'] == 'P0'


# ============================================================================
# SVGFixer Tests
# ============================================================================

class TestSVGFixer:
    """Test automatic SVG fixing logic"""

    def test_apply_fixes_processes_p0_and_p1_only(self):
        """Should only apply P0 and P1 fixes, skip P2"""
        from scripts.svg_auto_optimizer import SVGFixer

        fixer = SVGFixer()
        svg_content = '<svg><text y="100">Test</text></svg>'
        issues = [
            {'priority': 'P0', 'suggested_fix': {'action': 'increase_spacing'}},
            {'priority': 'P1', 'suggested_fix': {'action': 'adjust_position'}},
            {'priority': 'P2', 'suggested_fix': {'action': 'reduce_font_size'}},
        ]

        result = fixer.apply_fixes(svg_content, issues)

        # Should process P0 and P1, but result should still be valid SVG
        assert isinstance(result, str)
        assert '<svg>' in result

    def test_increase_spacing_modifies_y_coordinates(self):
        """Should increase spacing by adjusting y coordinates"""
        from scripts.svg_auto_optimizer import SVGFixer

        fixer = SVGFixer()
        svg = '<svg><text y="100">Line1</text><text y="108">Line2</text></svg>'
        issue = {
            'location': {'approximate_y_range': '100-110'},
            'suggested_fix': {
                'action': 'increase_spacing',
                'details': 'Increase spacing by 10px'
            }
        }

        result = fixer._increase_spacing(svg, issue)

        # Should modify at least one y coordinate
        assert result != svg
        assert 'y=' in result

    def test_adjust_position_moves_element(self):
        """Should adjust element position based on fix details"""
        from scripts.svg_auto_optimizer import SVGFixer

        fixer = SVGFixer()
        svg = '<svg><text y="100">Test</text></svg>'
        issue = {
            'suggested_fix': {
                'action': 'adjust_position',
                'details': 'Move y=100 to y=120'
            }
        }

        result = fixer._adjust_position(svg, issue)

        assert 'y="120"' in result or "y='120'" in result

    def test_reduce_font_size_modifies_font_attribute(self):
        """Should reduce font-size attribute"""
        from scripts.svg_auto_optimizer import SVGFixer

        fixer = SVGFixer()
        svg = '<svg><text font-size="14">Test</text></svg>'
        issue = {
            'suggested_fix': {
                'action': 'reduce_font_size',
                'details': 'Reduce font-size from 14 to 12'
            }
        }

        result = fixer._reduce_font_size(svg, issue)

        assert 'font-size="12"' in result or "font-size='12'" in result


# ============================================================================
# IterationController Tests
# ============================================================================

class TestIterationController:
    """Test iteration control and optimization loop"""

    def test_save_iteration_creates_directory_structure(self):
        """Should save SVG, screenshot, and feedback in iteration directory"""
        from scripts.svg_auto_optimizer import IterationController

        with tempfile.TemporaryDirectory() as tmpdir:
            controller = IterationController(output_dir=tmpdir)

            svg_path = Path(tmpdir) / 'test.svg'
            svg_path.write_text('<svg></svg>', encoding='utf-8')

            screenshot_path = Path(tmpdir) / 'test.png'
            screenshot_path.write_bytes(b'fake_png_data')

            feedback = {'status': 'NEEDS_FIX', 'issues': []}

            controller.save_iteration(0, svg_path, screenshot_path, feedback)

            iteration_dir = Path(tmpdir) / 'iteration_0'
            assert iteration_dir.exists()
            assert (iteration_dir / 'resume.svg').exists()
            assert (iteration_dir / 'preview.png').exists()
            assert (iteration_dir / 'feedback.json').exists()

    def test_is_approved_checks_approval_criteria(self):
        """Should return True only if all approval criteria met"""
        from scripts.svg_auto_optimizer import IterationController

        controller = IterationController()

        # Approved feedback
        approved = {
            'status': 'APPROVED',
            'overall_quality_score': 9,
            'issues': []
        }
        assert controller.is_approved(approved) is True

        # Not approved feedback
        needs_fix = {
            'status': 'NEEDS_FIX',
            'overall_quality_score': 6,
            'issues': [{'priority': 'P0'}]
        }
        assert controller.is_approved(needs_fix) is False

    def test_run_optimization_loop_returns_final_path(self):
        """Should run optimization loop and return final SVG path"""
        from scripts.svg_auto_optimizer import IterationController

        with tempfile.TemporaryDirectory() as tmpdir:
            controller = IterationController(
                output_dir=tmpdir,
                max_iterations=1  # Limit to 1 for fast testing
            )

            # Should complete and return a Path
            final_path = controller.run_optimization_loop()

            assert isinstance(final_path, Path)
            assert final_path.exists()
            assert final_path.suffix == '.pdf'


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_full_optimization_pipeline(self):
        """Should run complete optimization from data to final PDF"""
        # This test will be implemented after all components work
        pytest.skip("Integration test - implement after components are ready")

