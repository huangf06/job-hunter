import importlib.util
from pathlib import Path

import pytest


def load_scrape_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "scrape.py"
    spec = importlib.util.spec_from_file_location("scripts.scrape", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cli_rejects_deleted_legacy_profiles():
    scrape = load_scrape_module()
    parser = scrape.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--platform", "linkedin", "--profile", "ml_data", "--dry-run"])

    with pytest.raises(SystemExit):
        parser.parse_args(["--platform", "linkedin", "--profile", "backend_data", "--dry-run"])

    with pytest.raises(SystemExit):
        parser.parse_args(["--platform", "linkedin", "--profile", "quick_test", "--dry-run"])


def test_cli_accepts_active_profile_names():
    scrape = load_scrape_module()
    parser = scrape.build_parser()

    args = parser.parse_args(
        ["--platform", "linkedin", "--profile", "data_engineering", "--dry-run"]
    )

    assert args.platform == "linkedin"
    assert args.profile == "data_engineering"
    assert args.dry_run is True


def test_run_platforms_logs_elapsed_time(monkeypatch):
    scrape = load_scrape_module()
    built_platforms = []
    log_messages = []

    class DummyScraper:
        def __init__(self, platform: str):
            self.platform = platform

        def run(self, dry_run: bool = False):
            return {"source": self.platform, "found": 1, "dry_run": dry_run}

    perf_values = iter([10.0, 12.5, 12.5, 20.0])

    monkeypatch.setattr(scrape, "build_scraper", lambda platform, profile=None: built_platforms.append((platform, profile)) or DummyScraper(platform))
    monkeypatch.setattr(scrape, "serialize_report", lambda report: dict(report))
    monkeypatch.setattr(scrape.time, "perf_counter", lambda: next(perf_values))
    monkeypatch.setattr(scrape.logger, "info", lambda message, *args: log_messages.append(message % args))

    reports = scrape.run_platforms(
        platforms=["linkedin", "greenhouse"],
        profile="data_engineering",
        save_to_db=False,
        dry_run=True,
    )

    assert reports == {
        "linkedin": {"source": "linkedin", "found": 1, "dry_run": True, "diagnostics": {"elapsed_seconds": 2.5}},
        "greenhouse": {
            "source": "greenhouse",
            "found": 1,
            "dry_run": True,
            "diagnostics": {"elapsed_seconds": 7.5},
        },
    }
    assert built_platforms == [
        ("linkedin", "data_engineering"),
        ("greenhouse", "data_engineering"),
    ]
    assert log_messages == [
        "Platform linkedin completed in 2.50s severity=n/a found=1 new=0",
        "Platform greenhouse completed in 7.50s severity=n/a found=1 new=0",
    ]


def test_emit_metrics_preserves_platform_diagnostics():
    scrape = load_scrape_module()
    output_path = Path(__file__).resolve().parent / "tmp_scrape_metrics.json"

    try:
        metrics = scrape.emit_metrics(
            {
                "linkedin": {
                    "source": "linkedin",
                    "found": 2,
                    "new": 1,
                    "severity": "warning",
                    "diagnostics": {
                        "session_status": "challenge",
                        "last_stage": "validate_session",
                        "elapsed_seconds": 12.5,
                    },
                }
            },
            output_path=output_path,
        )

        assert metrics["platforms"]["linkedin"]["diagnostics"] == {
            "session_status": "challenge",
            "last_stage": "validate_session",
            "elapsed_seconds": 12.5,
        }
    finally:
        output_path.unlink(missing_ok=True)
