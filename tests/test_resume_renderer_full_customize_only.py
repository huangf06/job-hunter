"""Regression tests for resume_renderer after 2026-04-17 tier revert.

Every job with analysis must render through the FULL_CUSTOMIZE path
(base_template.html + experiences loop). USE_TEMPLATE (static PDF copy)
and ADAPT_TEMPLATE (zone DE/ML/DS) are retired.
"""
import json
from unittest.mock import patch

from src.resume_renderer import ResumeRenderer


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


def test_format_coursework_filters_by_selected_ids():
    master = {
        'courses': [
            {'id': 'deep_learning', 'name': 'Deep Learning', 'grade': '9.5'},
            {'id': 'multi_agent_systems', 'name': 'Multi-Agent Systems', 'grade': '9.5'},
            {'id': 'nlp', 'name': 'NLP', 'grade': '9.0'},
        ]
    }
    selected = ['deep_learning', 'nlp']

    result = ResumeRenderer._format_coursework(master, selected_courses=selected)

    assert 'Deep Learning (9.5)' in result
    assert 'NLP (9.0)' in result
    assert 'Multi-Agent' not in result


def test_format_coursework_all_when_no_selection():
    master = {
        'courses': [
            {'id': 'deep_learning', 'name': 'Deep Learning', 'grade': '9.5'},
            {'id': 'nlp', 'name': 'NLP', 'grade': '9.0'},
        ]
    }

    result = ResumeRenderer._format_coursework(master, selected_courses=None)

    assert 'Deep Learning (9.5)' in result
    assert 'NLP (9.0)' in result


def test_build_context_applies_selected_courses():
    """Integration: _build_context respects selected_courses from tailored JSON."""
    renderer = ResumeRenderer.__new__(ResumeRenderer)
    renderer.bullet_library = {
        'education': {
            'master': {
                'courses': [
                    {'id': 'deep_learning', 'name': 'Deep Learning', 'grade': '9.5'},
                    {'id': 'nlp', 'name': 'NLP', 'grade': '9.0'},
                    {'id': 'data_mining', 'name': 'Data Mining', 'grade': '9.0'},
                ],
            },
        },
    }
    renderer.base_context = {
        'edu_master_coursework': 'Deep Learning (9.5), NLP (9.0), Data Mining (9.0)',
        'edu_bachelor_thesis': 'Some thesis',
        'career_note': 'Career Note: 2019-2023 gap explanation.',
    }
    renderer.validator = type('V', (), {'validate': lambda self, t, j, tier=None: type('R', (), {'passed': True, 'errors': [], 'warnings': [], 'fixes': {}})()})()

    tailored = {
        'bio': 'Test bio',
        'experiences': [
            {'company': 'A', 'bullets': ['b1'], 'title': 'T', 'date': 'D'},
            {'company': 'B', 'bullets': ['b2'], 'title': 'T', 'date': 'D'},
        ],
        'projects': [{'name': 'P', 'bullets': ['p1']}],
        'skills': [
            {'category': 'Languages & Core', 'skills_list': 'Python'},
            {'category': 'Data Engineering', 'skills_list': 'Spark'},
            {'category': 'Cloud & DevOps', 'skills_list': 'Docker'},
        ],
        'selected_courses': ['deep_learning', 'nlp'],
        'show_bachelor_thesis': False,
        'show_career_note': False,
    }

    context = renderer._build_context(tailored, {'company': 'TestCorp'})

    assert 'Deep Learning (9.5)' in context['edu_master_coursework']
    assert 'Data Mining' not in context['edu_master_coursework']
    assert context['edu_bachelor_thesis'] == ''
    assert context['career_note'] == ''


def test_build_context_preserves_defaults_without_ai_control():
    """Integration: without AI control fields, defaults are preserved."""
    renderer = ResumeRenderer.__new__(ResumeRenderer)
    renderer.bullet_library = {}
    renderer.base_context = {
        'edu_master_coursework': 'All courses here',
        'edu_bachelor_thesis': 'Some thesis',
        'career_note': 'Career Note text',
    }
    renderer.validator = type('V', (), {'validate': lambda self, t, j, tier=None: type('R', (), {'passed': True, 'errors': [], 'warnings': [], 'fixes': {}})()})()

    tailored = {
        'bio': 'Test bio',
        'experiences': [
            {'company': 'A', 'bullets': ['b1'], 'title': 'T', 'date': 'D'},
            {'company': 'B', 'bullets': ['b2'], 'title': 'T', 'date': 'D'},
        ],
        'projects': [{'name': 'P', 'bullets': ['p1']}],
        'skills': [
            {'category': 'Languages & Core', 'skills_list': 'Python'},
            {'category': 'Data Engineering', 'skills_list': 'Spark'},
            {'category': 'Cloud & DevOps', 'skills_list': 'Docker'},
        ],
    }

    context = renderer._build_context(tailored, {'company': 'TestCorp'})

    assert context['edu_master_coursework'] == 'All courses here'
    assert context['edu_bachelor_thesis'] == 'Some thesis'
    assert context['career_note'] == 'Career Note text'
