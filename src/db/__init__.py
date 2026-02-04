"""
Job Hunter 数据库模块
"""

from .job_db import (
    JobDatabase,
    Job,
    FilterResult,
    ScoreResult,
    Resume,
    Application,
)

__all__ = [
    "JobDatabase",
    "Job",
    "FilterResult",
    "ScoreResult",
    "Resume",
    "Application",
]
