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

    def test_genai_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="GenAI Engineer"))
        assert result.passed is True

    def test_computer_vision_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Computer Vision Engineer"))
        assert result.passed is True

    def test_bi_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Senior BI Engineer"))
        assert result.passed is True

    def test_dataflow_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Dataflow Development Engineer"))
        assert result.passed is True


class TestWrongRole:
    """Marketing / non-target titles should be rejected."""

    def test_marketing_manager_rejected(self, hf):
        job = _make_job(title="Marketing Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_sales_director_rejected(self, hf):
        job = _make_job(title="Sales Director")
        result = hf.apply(job)
        assert result.passed is False

    def test_marketing_data_analyst_passes(self, hf):
        """'Marketing Data Analyst' has reject word 'marketing' but also 'data' + 'analyst'
        in reject_exceptions — should NOT be hard-rejected, let AI decide."""
        result = hf.apply(_make_job(title="Marketing Data Analyst"))
        assert result.passed is True

    def test_marketing_data_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Marketing Data Engineer"))
        assert result.passed is True

    def test_senior_data_scientist_marketing_passes(self, hf):
        result = hf.apply(_make_job(title="Senior Data Scientist - Marketing"))
        assert result.passed is True

    def test_embedded_ml_engineer_passes(self, hf):
        """'Embedded ML Engineer' has 'embedded' reject but 'ml' + 'engineer' exceptions."""
        result = hf.apply(_make_job(title="Embedded ML Engineer"))
        assert result.passed is True

    def test_legal_ai_engineer_passes(self, hf):
        """'AI Engineer (Libra - Legal AI Assistant)' has 'legal' reject but 'ai' + 'engineer' exceptions."""
        result = hf.apply(_make_job(title="AI Engineer (Libra - Legal AI Assistant)"))
        assert result.passed is True

    def test_data_analyst_sales_passes(self, hf):
        result = hf.apply(_make_job(title="Data Analyst, Sales & Delivery"))
        assert result.passed is True


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


class TestDutchRequired:
    """Rule 2: JD explicitly requires Dutch language proficiency."""

    def test_dutch_fluency_required_rejected(self, hf):
        job = _make_job(description=(
            "We are looking for a Data Engineer. "
            "Requirements: fluency in Dutch is required for this position. "
            "You will work with Python and SQL in our Amsterdam office."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "dutch_required"

    def test_nederlandstalig_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer needed. Must be nederlandstalig. "
            "Experience with Python, Spark, and cloud platforms required."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "dutch_required"

    def test_english_only_jd_passes(self, hf):
        """JD mentioning Dutch culture but not requiring the language should pass."""
        job = _make_job(description=(
            "Join our team in the Netherlands. We are looking for a Data Engineer. "
            "You will work with Python, SQL, and Spark. English is the working language."
        ))
        result = hf.apply(job)
        assert result.passed is True


class TestWrongTechStack:
    """Rule 4: Non-target tech stack detection."""

    def test_flutter_developer_title_rejected(self, hf):
        """Flutter Software Engineer: 'software' passes non_target_role, but title matches tech_stack pattern."""
        job = _make_job(title="Software Flutter Developer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_dotnet_in_title_body_rejected(self, hf):
        """Dotnet keyword in title triggers tech_stack; 'platform' passes non_target_role."""
        job = _make_job(title="Platform Engineer Dotnet")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_csharp_platform_engineer_rejected(self, hf):
        """C# in title triggers tech_stack; 'platform' passes non_target_role."""
        job = _make_job(title="C# Platform Engineer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_dotnet_platform_engineer_rejected(self, hf):
        """.NET in title triggers tech_stack; 'platform' passes non_target_role."""
        job = _make_job(title=".NET Platform Engineer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_java_software_engineer_rejected(self, hf):
        """Pure Java role: 'software' passes non_target_role, java triggers tech_stack."""
        job = _make_job(title="Java Software Engineer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_java_data_title_passes(self, hf):
        """Java + data qualifier in title triggers tech_stack exception → passes."""
        job = _make_job(title="Java Data Engineer")
        result = hf.apply(job)
        assert result.passed is True

    def test_title_without_target_keyword_rejected_by_role_not_tech(self, hf):
        """Flutter Developer has no target keyword → non_target_role fires first (priority 2 < 3)."""
        job = _make_job(title="Flutter Developer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_body_irrelevant_keywords_below_threshold_passes(self, hf):
        """A few irrelevant body keywords under threshold should not reject."""
        job = _make_job(description=(
            "Data Engineer role. You will work with Python, SQL, Spark, and AWS. "
            "Some exposure to react and angular is nice to have but not required. "
            "Primary focus is building data pipelines and ETL processes."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_body_irrelevant_keywords_above_threshold_rejected(self, hf):
        """Many irrelevant body keywords over threshold (7) should reject.
        Title 'Software Engineer' passes non_target_role but has no tech_stack exception."""
        job = _make_job(
            title="Software Engineer",
            description=(
                "Full stack engineer needed. Tech stack: react, angular, vue, "
                "typescript, node.js, spring boot, microservice architecture, "
                ".net backend, graphql API layer. Some Python scripting."
            ),
        )
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_data_title_exempts_body_keywords(self, hf):
        """'Data Engineer' title triggers tech_stack exception — body keywords ignored."""
        job = _make_job(
            title="Data Engineer",
            description=(
                "Full stack role: react, angular, vue, typescript, node.js, "
                "spring boot, microservice, .net, graphql, ruby on rails."
            ),
        )
        result = hf.apply(job)
        assert result.passed is True


class TestFreelanceZzp:
    """Rule 5: Freelance/ZZP-only positions."""

    def test_zzp_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer (ZZP). We are looking for a freelance data engineer. "
            "KVK registration required. Day rate negotiable."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "freelance_zzp"

    def test_freelance_only_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer position. This is a freelance only contract. "
            "Candidates must have their own business registration."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "freelance_zzp"

    def test_fulltime_with_freelance_mention_passes(self, hf):
        """JD mentioning full-time/permanent/salary alongside freelance keyword should pass via exception."""
        job = _make_job(description=(
            "Data Engineer - full-time permanent position. Competitive salary offered. "
            "We also welcome freelance applicants. Python, SQL, Spark required."
        ))
        result = hf.apply(job)
        assert result.passed is True


class TestLowCompensation:
    """Rule 6: Extremely low compensation."""

    def test_low_usd_monthly_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer position. Compensation: $1200 per month. "
            "Remote work available. Python and SQL required."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "low_compensation"

    def test_low_eur_monthly_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer. We offer €1300 per month plus benefits. "
            "Location: Amsterdam. Python, SQL, cloud experience."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "low_compensation"

    def test_normal_salary_passes(self, hf):
        """Normal salary range should not trigger low compensation filter."""
        job = _make_job(description=(
            "Data Engineer. Salary range: €55,000 - €75,000 per year. "
            "Python, SQL, Spark. Amsterdam office with hybrid work."
        ))
        result = hf.apply(job)
        assert result.passed is True


class TestSpecificTechExperience:
    """Rule 6.5: Specific tech stack years too high for candidate."""

    def test_java_7_years_rejected(self, hf):
        """Title 'Software Engineer' has no exception keyword → specific_tech_experience fires."""
        job = _make_job(
            title="Software Engineer",
            description=(
                "Software Engineer needed. Requirements: 7+ years of Java experience. "
                "Strong background in distributed systems."
            ),
        )
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "specific_tech_experience"

    def test_scala_5_years_rejected(self, hf):
        """Title 'Backend Engineer' has no exception → specific_tech_experience fires for Scala."""
        job = _make_job(
            title="Backend Engineer",
            description=(
                "Looking for engineer with 5+ years scala experience. "
                "Building distributed data solutions."
            ),
        )
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "specific_tech_experience"

    def test_python_7_years_passes(self, hf):
        """'python' is in the exceptions list — title with 'python' bypasses the rule."""
        job = _make_job(
            title="Python Software Engineer",
            description=(
                "Software Engineer. 7+ years of Python experience required. "
                "SQL, Spark, and cloud platforms."
            ),
        )
        result = hf.apply(job)
        assert result.passed is True

    def test_data_title_exempts_tech_years(self, hf):
        """'Data Engineer' title has 'data' in exceptions → rule skipped even with Java years."""
        job = _make_job(description=(
            "Data Engineer. 7+ years of Java experience. "
            "Building data pipelines."
        ))
        result = hf.apply(job)
        assert result.passed is True


class TestLocationRestricted:
    """Rule 9: Visa/residency restrictions (on-site NOT rejected — let AI decide)."""

    def test_onsite_only_passes(self, hf):
        """On-site requirement is not a hard reject — candidate is NL-based."""
        job = _make_job(description=(
            "Data Engineer. This is an onsite only position in Amsterdam. "
            "You will work from our office. Python, SQL required."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_no_visa_sponsorship_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer role. Unfortunately we cannot provide visa sponsorship "
            "for this position. No sponsorship available. Python and SQL."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "location_restricted"

    def test_must_be_located_rejected(self, hf):
        job = _make_job(description=(
            "Data Engineer. Candidates must be located in Germany. "
            "No relocation support. Python, SQL required."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "location_restricted"

    def test_hybrid_with_onsite_mention_passes(self, hf):
        """Hybrid role mentioning office should pass."""
        job = _make_job(description=(
            "Data Engineer - hybrid position. On-site 2 days per week, flexible "
            "remote the rest. Python, SQL, Spark. Amsterdam office."
        ))
        result = hf.apply(job)
        assert result.passed is True


class TestPriorityOrder:
    """Rules should fire in priority order — earlier rules take precedence."""

    def test_dutch_language_beats_wrong_role(self, hf):
        """Dutch language (priority 0) should reject before non_target_role (priority 2)."""
        job = _make_job(
            title="Marketing Manager",
            description=(
                "Wij zijn op zoek naar een marketing manager. "
                "Jij hebt kennis van onze systemen en werken binnen projecten. "
                "Verantwoordelijk voor de ontwikkeling van oplossingen in een omgeving "
                "met kwaliteit en samenwerken. Beschikbaar voor vacature in onze organisatie. "
                "Functie vereisten: ervaring met projecten."
            ),
        )
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "dutch_language"

    def test_non_target_role_beats_tech_stack(self, hf):
        """non_target_role (priority 2) should reject before wrong_tech_stack (priority 3)."""
        job = _make_job(title="Flutter Developer")
        result = hf.apply(job)
        assert result.passed is False
        # Flutter Developer has no target keyword → non_target_role fires first
        assert result.reject_reason == "non_target_role"


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
