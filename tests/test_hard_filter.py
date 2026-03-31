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
    """Whitelist-only: title must contain at least one target keyword to pass."""

    # --- Rejected: no whitelist keyword in title ---

    def test_marketing_manager_rejected(self, hf):
        job = _make_job(title="Marketing Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_account_manager_rejected(self, hf):
        job = _make_job(title="Account Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_recruiter_rejected(self, hf):
        job = _make_job(title="Technical Recruiter")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_hr_manager_rejected(self, hf):
        job = _make_job(title="HR Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    # --- Passed: title contains whitelist keyword ---

    def test_data_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Data Engineer"))
        assert result.passed is True

    def test_marketing_data_analyst_passes(self, hf):
        """Has 'data' in title → passes whitelist (AI decides on marketing fit)."""
        result = hf.apply(_make_job(title="Marketing Data Analyst"))
        assert result.passed is True

    def test_marketing_data_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Marketing Data Engineer"))
        assert result.passed is True

    def test_embedded_ml_engineer_passes(self, hf):
        """Has 'ml' in title → passes whitelist."""
        result = hf.apply(_make_job(title="Embedded ML Engineer"))
        assert result.passed is True

    def test_legal_ai_engineer_passes(self, hf):
        """Has 'ai' in title → passes whitelist."""
        result = hf.apply(_make_job(title="AI Engineer (Libra - Legal AI Assistant)"))
        assert result.passed is True

    def test_data_analyst_sales_passes(self, hf):
        result = hf.apply(_make_job(title="Data Analyst, Sales & Delivery"))
        assert result.passed is True

    def test_security_data_engineer_passes(self, hf):
        """Has 'data' → passes whitelist (formerly hard-rejected by pattern)."""
        result = hf.apply(_make_job(title="Data Security Engineer"))
        assert result.passed is True

    def test_policy_data_analyst_passes(self, hf):
        """Has 'data' → passes whitelist (formerly hard-rejected by pattern)."""
        result = hf.apply(_make_job(title="Policy Data Analyst"))
        assert result.passed is True

    def test_bi_analyst_passes(self, hf):
        result = hf.apply(_make_job(title="BI Analyst"))
        assert result.passed is True

    def test_senior_data_scientist_marketing_passes(self, hf):
        result = hf.apply(_make_job(title="Senior Data Scientist - Marketing"))
        assert result.passed is True


class TestM6CompoundWhitelist:
    """M6: Compound patterns should pass target roles, reject loose matches."""

    def test_data_platform_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Data Platform Engineer"))
        assert result.passed is True

    def test_ml_infrastructure_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="ML Infrastructure Engineer"))
        assert result.passed is True

    def test_software_engineer_passes(self, hf):
        result = hf.apply(_make_job(title="Software Engineer"))
        assert result.passed is True

    def test_platform_product_manager_rejected(self, hf):
        """Standalone 'platform' no longer in whitelist — Product Manager rejected."""
        job = _make_job(title="Platform Product Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_infrastructure_manager_rejected(self, hf):
        """Standalone 'infrastructure' no longer in whitelist."""
        job = _make_job(title="Infrastructure Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"

    def test_software_sales_rejected(self, hf):
        """Standalone 'software' no longer in whitelist."""
        job = _make_job(title="Software Sales Manager")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "non_target_role"


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
        """'Android Developer' with whitelist keyword passes non_target_role but rejected by tech_stack."""
        job = _make_job(title="Android Developer - Python Backend")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_dotnet_in_title_body_rejected(self, hf):
        """Dotnet keyword in title triggers tech_stack; 'platform engineer' passes non_target_role."""
        job = _make_job(title="Platform Engineer Dotnet")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_csharp_platform_engineer_rejected(self, hf):
        """C# followed by space in title triggers tech_stack."""
        job = _make_job(title="C# Platform Engineer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_csharp_slash_dotnet_rejected(self, hf):
        """C#/.NET Engineer — C# followed by slash (non-word char) should match via (?!\\w)."""
        job = _make_job(title="C#/.NET Software Engineer")
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "wrong_tech_stack"

    def test_csharp_comma_rejected(self, hf):
        """C#, WPF Developer — C# followed by comma should match."""
        job = _make_job(title="C#, WPF Software Developer")
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

    def test_software_engineer_with_frontend_body_passes(self, hf):
        """Body keywords no longer checked — only title patterns matter."""
        job = _make_job(
            title="Software Engineer",
            description=(
                "Full stack engineer needed. Tech stack: react, angular, vue, "
                "typescript, node.js, spring boot, microservice architecture, "
                ".net backend, graphql API layer. Some Python scripting."
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


class TestPhDRequired:
    """M3: PhD hard requirement detection."""

    def test_phd_required_rejected(self, hf):
        job = _make_job(description=(
            "We are looking for a Research Scientist. "
            "PhD required in Computer Science or related field. "
            "Experience with deep learning frameworks."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "phd_required"

    def test_requires_phd_rejected(self, hf):
        job = _make_job(description=(
            "Applied Scientist position. This role requires a PhD "
            "in Machine Learning. Strong publication record expected."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "phd_required"

    def test_must_have_phd_rejected(self, hf):
        job = _make_job(description=(
            "Senior Research Engineer. Candidates must have a PhD "
            "in a relevant technical field. 5+ years experience."
        ))
        result = hf.apply(job)
        assert result.passed is False
        assert result.reject_reason == "phd_required"

    def test_phd_or_equivalent_passes(self, hf):
        """PhD with 'or equivalent' escape should NOT be rejected."""
        job = _make_job(description=(
            "ML Engineer. PhD required or equivalent industry experience. "
            "Python, PyTorch, distributed systems. Amsterdam office."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_phd_or_masters_passes(self, hf):
        """PhD with 'or Master' escape should NOT be rejected."""
        job = _make_job(description=(
            "Data Scientist. PhD or Master's degree in a quantitative field. "
            "Experience with Python, SQL, and statistical modeling."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_phd_preferred_passes(self, hf):
        """'PhD preferred' is not a hard requirement — should pass."""
        job = _make_job(description=(
            "ML Engineer. PhD preferred but not required. "
            "Strong Python skills. Experience with ML pipelines."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_phd_is_a_plus_passes(self, hf):
        """'PhD is a plus' is not a requirement — should pass."""
        job = _make_job(description=(
            "Data Engineer. MSc in CS or related. PhD is a plus. "
            "Experience with Spark, Airflow, and cloud platforms."
        ))
        result = hf.apply(job)
        assert result.passed is True

    def test_phd_or_msc_passes(self, hf):
        """'PhD or MSc' escape should NOT be rejected."""
        job = _make_job(description=(
            "Research Engineer. Requires a PhD or MSc in Computer Science. "
            "Experience with NLP and transformer architectures."
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
