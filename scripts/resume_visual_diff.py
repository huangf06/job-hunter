#!/usr/bin/env python3
"""
Render an HTML resume to PDF, compare it against a canonical PDF, and emit diff artifacts.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.resume_visual_diff import run_visual_diff_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume visual diff pipeline")
    parser.add_argument("--reference-pdf", required=True, help="Canonical PDF used as comparison truth")
    parser.add_argument("--candidate-html", required=True, help="Editable HTML file to render and compare")
    parser.add_argument("--output-dir", required=True, help="Directory for candidate PDF, PNGs, diff, and summary")
    parser.add_argument("--dpi", type=int, default=144, help="Rasterization DPI for both PDFs")
    args = parser.parse_args()

    summary = run_visual_diff_pipeline(
        reference_pdf=Path(args.reference_pdf),
        candidate_html=Path(args.candidate_html),
        output_dir=Path(args.output_dir),
        dpi=args.dpi,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
