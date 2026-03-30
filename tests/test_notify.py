"""Tests for notify.py (Block E+F audit)."""

from scripts.notify import format_message


def test_generate_count_in_success_message():
    """EF-5: Today's resume generation count should appear in notification."""
    db_stats = {
        "ready": [{"id": "j1", "score": 7.0, "title": "DE", "company": "Acme"}],
        "today_analyzed": 3,
        "today_high_score": 2,
        "today_tokens": 500,
        "today_new_ready": [],
        "today_generated": 4,
        "applied": 10,
        "interview": 2,
        "rejected": 5,
        "total_ready": 1,
    }
    scrape = {"new_jobs": 5}

    msg = format_message("success", scrape=scrape, db_stats=db_stats)
    assert "4 resumes" in msg or "4 generated" in msg, f"Expected generate count in message, got:\n{msg}"


def test_generate_count_zero_omitted():
    """EF-5: When no resumes generated, don't show generate line."""
    db_stats = {
        "ready": [],
        "today_analyzed": 1,
        "today_high_score": 0,
        "today_tokens": 100,
        "today_new_ready": [],
        "today_generated": 0,
        "applied": 0,
        "interview": 0,
        "rejected": 0,
        "total_ready": 0,
    }
    scrape = {"new_jobs": 2}

    msg = format_message("success", scrape=scrape, db_stats=db_stats)
    assert "generated" not in msg.lower() and "resumes" not in msg.lower(), (
        f"Generate count should be omitted when 0, got:\n{msg}"
    )
