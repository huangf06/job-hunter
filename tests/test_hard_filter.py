"""Tests for src.hard_filter module."""

import json

import pytest

from src.db.job_db import FilterResult
from src.hard_filter import HardFilter, keyword_boundary_pattern


# =============================================================================
# keyword_boundary_pattern tests
# =============================================================================

class TestKeywordBoundaryPattern:
    """Tests for the keyword_boundary_pattern helper function."""

    def test_normal_word_uses_word_boundaries(self):
        """Normal alphanumeric keywords get \\b on both sides."""
        import re
        pattern = keyword_boundary_pattern("python")
        assert re.search(pattern, "use python here")
        assert not re.search(pattern, "cpython2")  # embedded — no match at boundary

    def test_dotnet_leading_dot(self):
        """'.net' has a leading dot — skip left boundary so the dot discriminates."""
        import re
        pattern = keyword_boundary_pattern(".net")
        assert re.search(pattern, "experience with .net framework")
        assert not re.search(pattern, "experience with .network")  # \\b on right blocks

    def test_csharp_trailing_hash(self):
        """'c#' has a trailing non-word char — use lookahead instead of \\b."""
        import re
        pattern = keyword_boundary_pattern("c#")
        assert re.search(pattern, "proficient in c# development")
        assert re.search(pattern, "c#")  # standalone

    def test_plain_word_no_partial(self):
        """'data' should not match inside 'database' — \\b prevents partial match."""
        import re
        pattern = keyword_boundary_pattern("data")
        assert re.search(pattern, "data engineer")
        # \bdata\b should NOT match 'database' because 'b' follows 'a' (no word boundary)
        assert not re.search(pattern, "database")


# =============================================================================
# HardFilter.apply tests
# =============================================================================

@pytest.fixture(scope="module")
def hf():
    """Create a HardFilter instance (loads real config files)."""
    return HardFilter()


def _make_job(title="Data Engineer", company="TestCorp", description=None, location="Amsterdam, Netherlands", job_id="test-001"):
    """Helper to build a job dict with sensible defaults."""
    if description is None:
        description = (
            "We are looking for a Data Engineer to join our team. "
            "You will work with Python, SQL, Spark, and cloud platforms. "
            "Experience with data pipelines, ETL processes, and data warehousing is required. "
            "We offer a competitive salary and a great work environment in the Netherlands."
        )
    return {
        "id": job_id,
        "title": title,
        "company": company,
        "description": description,
        "location": location,
    }


class TestDutchLanguageDetection:
    """Dutch JD should be rejected by word_count rule."""

    def test_dutch_jd_rejected(self, hf):
        job = _make_job(
            title="Data Engineer",
            description=(
                "Wij zijn op zoek naar een ervaren data engineer. "
                "Jij hebt kennis van onze systemen en werken binnen projecten. "
                "Verantwoordelijk voor de ontwikkeling van oplossingen in een omgeving "
                "met kwaliteit en samenwerken. Beschikbaar voor vacature in onze organisatie. "
                "Functie vereisten: ervaring met data pipelines."
            ),
        )
        result = hf.apply(job)
        assert isinstance(result, FilterResult)
        assert result.passed is False
        assert result.reject_reason == "dutch_language"
        assert result.filter_version == "2.0"


class TestValidJobPasses:
    """A well-formed DE job should pass all filters."""

    def test_standard_data_engineer_passes(self, hf):
        result = hf.apply(_make_job())
        assert result.passed is True
        assert result.filter_version == "2.0"

    def test_ml_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Machine Learning Engineer"))
        assert result.passed is True


class TestWrongRole:
    """Marketing / non-target titles should be rejected."""

    def test_marketing_manager_rejected(self, hf):
        job = _make_job(title="Marketing Manager")
        result = hf.apply(job)
        assert result.passed is False
        # Could be rejected by title_reject_patterns or by title_must_contain_one_of
        assert result.reject_reason in ("non_target_role",)

    def test_sales_director_rejected(self, hf):
        job = _make_job(title="Sales Director")
        result = hf.apply(job)
        assert result.passed is False


class TestInsufficientData:
    """Jobs with empty or very short descriptions should be rejected."""

    def test_empty_description(self, hf):
        job = _make_job(description="")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "insufficient_data"

    def test_short_description(self, hf):
        job = _make_job(description="Short JD.")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "insufficient_data"

    def test_empty_title(self, hf):
        job = _make_job(title="", description="Some long enough description that passes the 50 char minimum length check easily.")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "insufficient_data"


class TestSeniorManagement:
    """Senior management titles rejected, but senior data scientist passes."""

    def test_senior_director_rejected(self, hf):
        job = _make_job(title="Senior Director of Data")
        result = hf.apply(job)
        assert result.passed is False

    def test_vp_rejected(self, hf):
        job = _make_job(title="VP of Data Engineering")
        result = hf.apply(job)
        assert result.passed is False

    def test_senior_data_scientist_passes(self, hf):
        result = hf.apply(_make_job(title="Senior Data Scientist"))
        assert result.passed is True

    def test_senior_data_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Senior Data Engineer"))
        assert result.passed is True

    def test_senior_ml_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Senior ML Engineer"))
        assert result.passed is True


class TestCompanyBlacklist:
    """Recruiting agencies should be rejected."""

    def test_hays_rejected(self, hf):
        job = _make_job(company="Hays")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "company_blacklist"

    def test_randstad_rejected(self, hf):
        job = _make_job(company="Randstad")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "company_blacklist"

    def test_normal_company_passes(self, hf):
        result = hf.apply(_make_job(company="Booking.com"))
        assert result.passed is True


class TestTitleBlacklist:
    """Intern/trainee titles should be rejected."""

    def test_intern_rejected(self, hf):
        job = _make_job(title="Data Engineering Intern")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "title_blacklist"

    def test_trainee_rejected(self, hf):
        job = _make_job(title="Data Trainee")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "title_blacklist"


class TestFilterResultType:
    """All results should be FilterResult with filter_version 2.0."""

    def test_passed_result_type(self, hf):
        result = hf.apply(_make_job())
        assert isinstance(result, FilterResult)
        assert result.filter_version == "2.0"

    def test_rejected_result_type(self, hf):
        result = hf.apply(_make_job(title="Marketing Manager"))
        assert isinstance(result, FilterResult)
        assert result.filter_version == "2.0"
        assert result.passed is False
