#!/usr/bin/env python3
"""
Resume visual diff utilities.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import fitz
from PIL import Image, ImageChops, ImageStat


@dataclass(frozen=True)
class ArtifactPaths:
    output_dir: Path
    candidate_pdf: Path
    reference_png: Path
    candidate_png: Path
    diff_png: Path
    summary_json: Path


def build_artifact_paths(reference_pdf: Path, candidate_html: Path, output_dir: Path) -> ArtifactPaths:
    """Build stable artifact paths for one comparison run."""
    del reference_pdf, candidate_html
    output_dir.mkdir(parents=True, exist_ok=True)
    return ArtifactPaths(
        output_dir=output_dir,
        candidate_pdf=output_dir / "candidate.pdf",
        reference_png=output_dir / "reference.png",
        candidate_png=output_dir / "candidate.png",
        diff_png=output_dir / "diff.png",
        summary_json=output_dir / "summary.json",
    )


def render_html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Render a local HTML file to a single-page A4 PDF via Playwright."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle", timeout=15000)
            page.pdf(
                path=str(pdf_path),
                format="A4",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=True,
                page_ranges="1",
            )
        finally:
            browser.close()


def rasterize_pdf_to_png(pdf_path: Path, png_path: Path, dpi: int) -> None:
    """Rasterize the first page of a PDF to PNG using PyMuPDF."""
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf_path) as document:
        if document.page_count < 1:
            raise ValueError(f"PDF has no pages: {pdf_path}")
        pixmap = document[0].get_pixmap(matrix=matrix, alpha=False)
        pixmap.save(str(png_path))


def compute_image_metrics(reference_png: Path, candidate_png: Path, diff_png: Path) -> Dict[str, object]:
    """Compute pixel-diff metrics between two equal-sized PNGs."""
    with Image.open(reference_png) as ref_img, Image.open(candidate_png) as cand_img:
        ref_rgb = ref_img.convert("RGB")
        cand_rgb = cand_img.convert("RGB")

        if ref_rgb.size != cand_rgb.size:
            raise ValueError("Reference and candidate images must have the same dimensions")

        diff = ImageChops.difference(ref_rgb, cand_rgb)
        diff.save(diff_png)
        stat = ImageStat.Stat(diff)
        channel_means = stat.mean
        channel_rms = stat.rms
        mean_abs_diff = sum(channel_means) / len(channel_means)
        rmse = math.sqrt(sum(value * value for value in channel_rms) / len(channel_rms))
        bbox = diff.getbbox()

        return {
            "width": ref_rgb.width,
            "height": ref_rgb.height,
            "mean_abs_diff": round(mean_abs_diff, 6),
            "rmse": round(rmse, 6),
            "normalized_mean_abs_diff": round(mean_abs_diff / 255.0, 6),
            "diff_bbox": list(bbox) if bbox else None,
        }


def normalize_candidate_png(reference_png: Path, candidate_png: Path) -> Dict[str, object]:
    """Resize the candidate raster to the reference dimensions when needed."""
    with Image.open(reference_png) as ref_img, Image.open(candidate_png) as cand_img:
        reference_size = ref_img.size
        candidate_size = cand_img.size
        if candidate_size == reference_size:
            return {
                "reference_size": list(reference_size),
                "candidate_original_size": list(candidate_size),
                "candidate_normalized_size": list(candidate_size),
                "normalized": False,
            }

        normalized = cand_img.resize(reference_size, Image.Resampling.LANCZOS)
        normalized.save(candidate_png)
        return {
            "reference_size": list(reference_size),
            "candidate_original_size": list(candidate_size),
            "candidate_normalized_size": list(reference_size),
            "normalized": True,
        }


def run_visual_diff_pipeline(
    reference_pdf: Path,
    candidate_html: Path,
    output_dir: Path,
    dpi: int = 144,
) -> Dict[str, object]:
    """Run the full HTML -> PDF -> PNG -> diff pipeline and persist a JSON summary."""
    reference_pdf = Path(reference_pdf)
    candidate_html = Path(candidate_html)
    output_dir = Path(output_dir)
    paths = build_artifact_paths(reference_pdf, candidate_html, output_dir)

    render_html_to_pdf(candidate_html, paths.candidate_pdf)
    rasterize_pdf_to_png(reference_pdf, paths.reference_png, dpi)
    rasterize_pdf_to_png(paths.candidate_pdf, paths.candidate_png, dpi)
    normalization = normalize_candidate_png(paths.reference_png, paths.candidate_png)
    metrics = compute_image_metrics(paths.reference_png, paths.candidate_png, paths.diff_png)

    summary = {
        "reference_pdf": str(reference_pdf),
        "candidate_html": str(candidate_html),
        "candidate_pdf": str(paths.candidate_pdf),
        "reference_png": str(paths.reference_png),
        "candidate_png": str(paths.candidate_png),
        "diff_png": str(paths.diff_png),
        "summary_json": str(paths.summary_json),
        "dpi": dpi,
        "normalization": normalization,
        "metrics": metrics,
    }
    paths.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
