"""Regression tests for resume_renderer after 2026-04-17 tier revert.

Every job with analysis must render through the FULL_CUSTOMIZE path
(base_template.html + experiences loop). USE_TEMPLATE (static PDF copy)
and ADAPT_TEMPLATE (zone DE/ML/DS) are retired.
"""
import json
from unittest.mock import patch

from src.resume_renderer import ResumeRenderer


def test_render_resume_upgrades_legacy_use_template_tier():
    """A tier='USE_TEMPLATE' analysis should NOT copy a static PDF anymore."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer.db, 'get_job') as mock_job, \
         patch.object(renderer, '_render_template_copy') as mock_copy:
        mock_get.return_value = {
            'resume_tier': 'USE_TEMPLATE',
            'template_id_final': 'DE',
            'tailored_resume': '{}',
        }
        mock_job.return_value = {'id': 'fake-job-id', 'company': 'Test', 'title': 'DE'}
        renderer.render_resume('fake-job-id')
        mock_copy.assert_not_called()


def test_render_resume_upgrades_legacy_adapt_template_tier():
    """A tier='ADAPT_TEMPLATE' analysis should NOT use zone rendering anymore."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer.db, 'get_job') as mock_job, \
         patch.object(renderer, '_render_adapt_template') as mock_adapt:
        mock_get.return_value = {
            'resume_tier': 'ADAPT_TEMPLATE',
            'template_id_final': 'DE',
            'tailored_resume': '{}',
        }
        mock_job.return_value = {'id': 'fake-job-id', 'company': 'Test', 'title': 'DE'}
        renderer.render_resume('fake-job-id')
        mock_adapt.assert_not_called()


def test_render_resume_rejects_zone_schema_tailored_json():
    """Pre-revert tailored_resume with slot_overrides must be skipped (need re-analyze)."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer.db, 'get_job') as mock_job:
        mock_get.return_value = {
            'resume_tier': 'FULL_CUSTOMIZE',
            'template_id_final': 'DE',
            'tailored_resume': json.dumps({
                'slot_overrides': {'bio_1': 'something'},
                'entry_visibility': {'glp': True},
                'change_summary': 'zone edit',
            }),
        }
        mock_job.return_value = {'id': 'fake-job-id', 'company': 'Test', 'title': 'DE'}
        result = renderer.render_resume('fake-job-id')
        assert result is None, "Legacy zone schema must not render"
