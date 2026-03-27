import importlib.util
import json
from pathlib import Path


def load_scrape_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "scrape.py"
    spec = importlib.util.spec_from_file_location("scripts.scrape", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_phase_one_metrics_json_contract():
    scrape = load_scrape_module()
    metrics_path = Path(__file__).resolve().parent / "_metrics_contract.json"

    try:
        metrics = scrape.emit_metrics(
            {
                "greenhouse": {
                    "found": 4,
                    "new": 2,
                    "would_insert": 2,
                    "targets_failed": 1,
                    "severity": "warning",
                },
                "iamexpat": {
                    "found": 3,
                    "new": 1,
                    "would_insert": 1,
                    "targets_failed": 0,
                    "severity": "info",
                },
            },
            output_path=metrics_path,
        )

        assert metrics["new_jobs"] == 3
        assert metrics["total"]["new"] == 3
        assert metrics["platforms"]["greenhouse"]["targets_failed"] == 1
        assert metrics["platforms"]["greenhouse"]["severity"] == "warning"
        assert metrics["total"]["severity"] == "warning"

        on_disk = json.loads(metrics_path.read_text(encoding="utf-8"))
        assert on_disk["new_jobs"] == 3
    finally:
        metrics_path.unlink(missing_ok=True)
