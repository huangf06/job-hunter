import shutil
import uuid
from pathlib import Path

import pytest


def _local_tmp_dir(name: str) -> Path:
    path = Path("_tmp_test_artifacts") / f"{name}_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_build_artifact_paths_uses_stable_filenames():
    from src.resume_visual_diff import build_artifact_paths

    reference_pdf = Path("templates/pdf/Fei_Huang_DE.pdf")
    candidate_html = Path("templates/Fei_Huang_DE_Resume.html")
    output_dir = _local_tmp_dir("visual_diff_paths")
    try:
        paths = build_artifact_paths(reference_pdf, candidate_html, output_dir)

        assert paths.output_dir == output_dir
        assert paths.candidate_pdf == output_dir / "candidate.pdf"
        assert paths.reference_png == output_dir / "reference.png"
        assert paths.candidate_png == output_dir / "candidate.png"
        assert paths.diff_png == output_dir / "diff.png"
        assert paths.summary_json == output_dir / "summary.json"
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_compute_image_metrics_detects_visual_difference():
    from PIL import Image

    from src.resume_visual_diff import compute_image_metrics

    tmp_path = _local_tmp_dir("visual_diff_metrics")
    try:
        ref_path = tmp_path / "ref.png"
        cand_path = tmp_path / "cand.png"
        diff_path = tmp_path / "diff.png"

        Image.new("RGB", (4, 4), "white").save(ref_path)
        Image.new("RGB", (4, 4), "black").save(cand_path)

        metrics = compute_image_metrics(ref_path, cand_path, diff_path)

        assert metrics["width"] == 4
        assert metrics["height"] == 4
        assert metrics["mean_abs_diff"] > 0
        assert metrics["rmse"] > 0
        assert metrics["diff_bbox"] == [0, 0, 4, 4]
        assert diff_path.exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_compute_image_metrics_rejects_size_mismatch():
    from PIL import Image

    from src.resume_visual_diff import compute_image_metrics

    tmp_path = _local_tmp_dir("visual_diff_size")
    try:
        ref_path = tmp_path / "ref.png"
        cand_path = tmp_path / "cand.png"

        Image.new("RGB", (4, 4), "white").save(ref_path)
        Image.new("RGB", (5, 4), "white").save(cand_path)

        with pytest.raises(ValueError, match="same dimensions"):
            compute_image_metrics(ref_path, cand_path, tmp_path / "diff.png")
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_run_visual_diff_pipeline_writes_summary_and_artifacts(monkeypatch):
    from src.resume_visual_diff import run_visual_diff_pipeline

    tmp_path = _local_tmp_dir("visual_diff_pipeline")
    try:
        reference_pdf = tmp_path / "reference.pdf"
        candidate_html = tmp_path / "candidate.html"
        reference_pdf.write_bytes(b"%PDF-1.4 reference")
        candidate_html.write_text("<html><body>candidate</body></html>", encoding="utf-8")

        def fake_render_html_to_pdf(html_path, pdf_path):
            assert html_path == candidate_html
            pdf_path.write_bytes(b"%PDF-1.4 candidate")

        def fake_rasterize_pdf_to_png(pdf_path, png_path, dpi):
            from PIL import Image

            color = "white" if pdf_path == reference_pdf else "black"
            Image.new("RGB", (8, 8), color).save(png_path)

        monkeypatch.setattr("src.resume_visual_diff.render_html_to_pdf", fake_render_html_to_pdf)
        monkeypatch.setattr("src.resume_visual_diff.rasterize_pdf_to_png", fake_rasterize_pdf_to_png)

        result = run_visual_diff_pipeline(reference_pdf, candidate_html, tmp_path, dpi=144)

        assert result["reference_pdf"] == str(reference_pdf)
        assert result["candidate_html"] == str(candidate_html)
        assert result["dpi"] == 144
        assert Path(result["candidate_pdf"]).exists()
        assert Path(result["reference_png"]).exists()
        assert Path(result["candidate_png"]).exists()
        assert Path(result["diff_png"]).exists()
        assert Path(result["summary_json"]).exists()
        assert result["metrics"]["mean_abs_diff"] > 0
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_run_visual_diff_pipeline_normalizes_candidate_size_to_reference(monkeypatch):
    from src.resume_visual_diff import run_visual_diff_pipeline

    tmp_path = _local_tmp_dir("visual_diff_resize")
    try:
        reference_pdf = tmp_path / "reference.pdf"
        candidate_html = tmp_path / "candidate.html"
        reference_pdf.write_bytes(b"%PDF-1.4 reference")
        candidate_html.write_text("<html><body>candidate</body></html>", encoding="utf-8")

        def fake_render_html_to_pdf(html_path, pdf_path):
            pdf_path.write_bytes(b"%PDF-1.4 candidate")

        def fake_rasterize_pdf_to_png(pdf_path, png_path, dpi):
            from PIL import Image

            if pdf_path == reference_pdf:
                Image.new("RGB", (10, 10), "white").save(png_path)
            else:
                Image.new("RGB", (20, 20), "black").save(png_path)

        monkeypatch.setattr("src.resume_visual_diff.render_html_to_pdf", fake_render_html_to_pdf)
        monkeypatch.setattr("src.resume_visual_diff.rasterize_pdf_to_png", fake_rasterize_pdf_to_png)

        result = run_visual_diff_pipeline(reference_pdf, candidate_html, tmp_path, dpi=144)

        assert result["metrics"]["width"] == 10
        assert result["metrics"]["height"] == 10
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
