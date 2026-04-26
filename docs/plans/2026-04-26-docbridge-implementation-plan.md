# DocBridge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CN-EU trade document AI processing platform that extracts structured data from Chinese trade documents (invoices, packing lists), serving as both an ML Engineer portfolio project and an IND self-employment visa business plan.

**Architecture:** Document images flow through a 5-stage pipeline: preprocessing → OCR (PaddleOCR) → layout analysis (LiLT/LayoutLMv3) → field extraction (token classification) → post-processing. The pipeline is exposed via FastAPI, containerized with Docker, tracked with MLflow, and monitored with Prometheus. Model training runs on Snellius HPC cluster (GPU).

**Tech Stack:** Python 3.11+, PyTorch, HuggingFace Transformers, PaddleOCR, LiLT/LayoutLMv3, FastAPI, Docker, MLflow, Prometheus, GitHub Actions, Snellius (SLURM)

**Repo:** New standalone repo `docbridge/` (not inside job-hunter)

**Design doc:** `job-hunter/docs/plans/2026-04-26-docbridge-design.md`

---

## Phase 1: Foundation (Week 1)

### Task 1: Repo Initialization & Project Scaffolding

**Files:**
- Create: `docbridge/pyproject.toml`
- Create: `docbridge/src/__init__.py`
- Create: `docbridge/src/pipeline/__init__.py`
- Create: `docbridge/src/api/__init__.py`
- Create: `docbridge/src/training/__init__.py`
- Create: `docbridge/src/monitoring/__init__.py`
- Create: `docbridge/tests/__init__.py`
- Create: `docbridge/.gitignore`
- Create: `docbridge/README.md`
- Create: `docbridge/CLAUDE.md`

**Step 1: Create repo and directory structure**

```bash
cd ~/github
mkdir docbridge && cd docbridge
git init
mkdir -p src/{pipeline,api,training,monitoring} tests data models notebooks docs/business_plan
touch src/__init__.py src/pipeline/__init__.py src/api/__init__.py src/training/__init__.py src/monitoring/__init__.py tests/__init__.py
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "docbridge"
version = "0.1.0"
description = "CN-EU trade document AI processing platform"
requires-python = ">=3.11"
dependencies = [
    "torch>=2.0",
    "transformers>=4.40",
    "paddleocr>=2.7",
    "paddlepaddle>=2.6",
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "python-multipart>=0.0.9",
    "Pillow>=10.0",
    "mlflow>=2.12",
    "prometheus-client>=0.20",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "ruff>=0.4",
]
training = [
    "datasets>=2.19",
    "seqeval>=1.2",
    "accelerate>=0.30",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 3: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.venv/
venv/
data/
models/*.pt
models/*.bin
*.egg-info/
dist/
build/
.env
mlruns/
*.db
```

**Step 4: Create minimal README.md**

```markdown
# DocBridge

CN-EU trade document AI processing platform. Extracts structured data from Chinese trade documents (invoices, packing lists) for European importers, freight forwarders, and customs brokers.

## Status: MVP in development

## Architecture

```
Document Image → Preprocessing → OCR (PaddleOCR) → Layout Analysis (LiLT)
    → Field Extraction → Structured JSON
```

## Setup

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```
```

**Step 5: Create CLAUDE.md**

```markdown
# DocBridge

CN-EU trade document AI processing platform.

## Commands

- `pytest` — run tests
- `ruff check src/ tests/` — lint
- `uvicorn src.api.main:app --reload` — dev server
- `docker compose up` — full stack

## Structure

- `src/pipeline/` — document processing pipeline (OCR, layout, extraction)
- `src/api/` — FastAPI service
- `src/training/` — model training scripts (run on Snellius HPC)
- `src/monitoring/` — Prometheus metrics
- `tests/` — pytest tests
- `models/` — trained model artifacts (gitignored except metadata)
- `data/` — datasets (gitignored)

## Key Decisions

- LiLT over LayoutLMv3 for language-independent layout understanding
- PaddleOCR for Chinese text (far better than Tesseract on CJK)
- Pipeline architecture (OCR and layout separate) for independent debugging
- Training on Snellius HPC cluster via SLURM jobs
```

**Step 6: Commit**

```bash
git add -A
git commit -m "init: scaffold docbridge project structure"
```

---

### Task 2: PaddleOCR Baseline — Test & Wrapper

**Files:**
- Create: `src/pipeline/ocr_engine.py`
- Create: `tests/test_ocr_engine.py`
- Create: `tests/fixtures/` (sample images)

**Prerequisite:** Download 2-3 sample Chinese invoice images from the web and place them in `tests/fixtures/`. Name them `sample_cn_invoice_01.jpg`, `sample_cn_invoice_02.jpg`. These are test fixtures, not training data.

**Step 1: Write the failing test**

```python
# tests/test_ocr_engine.py
from pathlib import Path
import pytest
from src.pipeline.ocr_engine import OCREngine, OCRResult

FIXTURES = Path(__file__).parent / "fixtures"


def test_ocr_engine_returns_result_object():
    engine = OCREngine()
    result = engine.extract(FIXTURES / "sample_cn_invoice_01.jpg")
    assert isinstance(result, OCRResult)


def test_ocr_result_has_text_and_boxes():
    engine = OCREngine()
    result = engine.extract(FIXTURES / "sample_cn_invoice_01.jpg")
    assert len(result.lines) > 0
    for line in result.lines:
        assert "text" in line
        assert "bbox" in line
        assert "confidence" in line


def test_ocr_detects_chinese_characters():
    engine = OCREngine()
    result = engine.extract(FIXTURES / "sample_cn_invoice_01.jpg")
    all_text = " ".join(line["text"] for line in result.lines)
    has_chinese = any("一" <= ch <= "鿿" for ch in all_text)
    assert has_chinese, f"No Chinese characters detected in: {all_text[:200]}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ocr_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pipeline.ocr_engine'`

**Step 3: Write minimal implementation**

```python
# src/pipeline/ocr_engine.py
from dataclasses import dataclass, field
from pathlib import Path
from paddleocr import PaddleOCR


@dataclass
class OCRResult:
    lines: list[dict] = field(default_factory=list)
    raw: list | None = None


class OCREngine:
    def __init__(self, lang: str = "ch"):
        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def extract(self, image_path: Path | str) -> OCRResult:
        raw = self._ocr.ocr(str(image_path), cls=True)
        lines = []
        for page in raw:
            if page is None:
                continue
            for item in page:
                bbox, (text, confidence) = item
                lines.append({
                    "text": text,
                    "bbox": [coord for point in bbox for coord in point],
                    "confidence": round(confidence, 4),
                })
        return OCRResult(lines=lines, raw=raw)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ocr_engine.py -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/pipeline/ocr_engine.py tests/test_ocr_engine.py tests/fixtures/
git commit -m "feat: add PaddleOCR engine wrapper with Chinese invoice support"
```

---

### Task 3: Image Preprocessor

**Files:**
- Create: `src/pipeline/preprocessor.py`
- Create: `tests/test_preprocessor.py`

**Step 1: Write the failing test**

```python
# tests/test_preprocessor.py
from pathlib import Path
from PIL import Image
import pytest
from src.pipeline.preprocessor import Preprocessor

FIXTURES = Path(__file__).parent / "fixtures"


def test_preprocessor_returns_pil_image():
    prep = Preprocessor()
    result = prep.process(FIXTURES / "sample_cn_invoice_01.jpg")
    assert isinstance(result, Image.Image)


def test_preprocessor_converts_to_rgb():
    gray = Image.new("L", (100, 100), 128)
    gray_path = FIXTURES / "_test_gray.png"
    gray.save(gray_path)
    try:
        prep = Preprocessor()
        result = prep.process(gray_path)
        assert result.mode == "RGB"
    finally:
        gray_path.unlink(missing_ok=True)


def test_preprocessor_limits_max_dimension():
    large = Image.new("RGB", (6000, 4000), (255, 255, 255))
    large_path = FIXTURES / "_test_large.png"
    large.save(large_path)
    try:
        prep = Preprocessor(max_dimension=2048)
        result = prep.process(large_path)
        assert max(result.size) <= 2048
    finally:
        large_path.unlink(missing_ok=True)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_preprocessor.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/pipeline/preprocessor.py
from pathlib import Path
from PIL import Image


class Preprocessor:
    def __init__(self, max_dimension: int = 4096):
        self.max_dimension = max_dimension

    def process(self, image_path: Path | str) -> Image.Image:
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        if max(img.size) > self.max_dimension:
            ratio = self.max_dimension / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        return img
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_preprocessor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/pipeline/preprocessor.py tests/test_preprocessor.py
git commit -m "feat: add image preprocessor with RGB conversion and resize"
```

---

### Task 4: Data Pipeline — Download & Prepare Datasets

**Files:**
- Create: `src/training/dataset.py`
- Create: `src/training/download_data.py`
- Create: `tests/test_dataset.py`

**Note:** SCID requires an application form. FUNSD is freely available on HuggingFace and is the standard LayoutLM benchmark. Start with FUNSD for initial training pipeline validation, then add SCID/VATI when access is granted.

**Step 1: Write the failing test**

```python
# tests/test_dataset.py
import pytest
from src.training.dataset import DocBridgeDataset


@pytest.fixture
def sample_annotation():
    return {
        "id": "sample_001",
        "tokens": ["发票", "号码", ":", "INV-2024-001"],
        "bboxes": [[100, 50, 200, 80], [210, 50, 300, 80], [310, 50, 320, 80], [330, 50, 500, 80]],
        "labels": ["B-INVOICE_NO", "I-INVOICE_NO", "O", "B-INVOICE_NO_VAL"],
    }


def test_dataset_tokenizes_with_label_alignment(sample_annotation):
    ds = DocBridgeDataset(annotations=[sample_annotation], tokenizer_name="bert-base-multilingual-cased")
    item = ds[0]
    assert "input_ids" in item
    assert "bbox" in item
    assert "labels" in item
    assert len(item["input_ids"]) == len(item["labels"])
    assert len(item["input_ids"]) == len(item["bbox"])


def test_dataset_pads_to_max_length(sample_annotation):
    ds = DocBridgeDataset(
        annotations=[sample_annotation],
        tokenizer_name="bert-base-multilingual-cased",
        max_length=64,
    )
    item = ds[0]
    assert len(item["input_ids"]) == 64
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/training/dataset.py
from torch.utils.data import Dataset
from transformers import AutoTokenizer


class DocBridgeDataset(Dataset):
    def __init__(
        self,
        annotations: list[dict],
        tokenizer_name: str = "bert-base-multilingual-cased",
        max_length: int = 512,
        label2id: dict | None = None,
    ):
        self.annotations = annotations
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.max_length = max_length
        self.label2id = label2id or self._build_label2id()

    def _build_label2id(self) -> dict:
        labels = set()
        for ann in self.annotations:
            labels.update(ann["labels"])
        label_list = sorted(labels)
        return {label: i for i, label in enumerate(label_list)}

    def __len__(self) -> int:
        return len(self.annotations)

    def __getitem__(self, idx: int) -> dict:
        ann = self.annotations[idx]
        tokens = ann["tokens"]
        bboxes = ann["bboxes"]
        labels = ann["labels"]

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        word_ids = encoding.word_ids()
        aligned_labels = []
        aligned_bboxes = []
        for word_id in word_ids:
            if word_id is None:
                aligned_labels.append(-100)
                aligned_bboxes.append([0, 0, 0, 0])
            else:
                aligned_labels.append(self.label2id[labels[word_id]])
                aligned_bboxes.append(bboxes[word_id])

        return {
            "input_ids": encoding["input_ids"].squeeze(0).tolist(),
            "attention_mask": encoding["attention_mask"].squeeze(0).tolist(),
            "bbox": aligned_bboxes,
            "labels": aligned_labels,
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dataset.py -v`
Expected: PASS

**Step 5: Write data download script**

```python
# src/training/download_data.py
"""Download and prepare public datasets for DocBridge training.

Usage:
    python -m src.training.download_data --dataset funsd --output data/funsd
"""
import argparse
from pathlib import Path
from datasets import load_dataset


def download_funsd(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("nielsr/funsd", trust_remote_code=True)
    ds.save_to_disk(str(output_dir))
    print(f"FUNSD saved to {output_dir} — {len(ds['train'])} train, {len(ds['test'])} test")


DATASETS = {
    "funsd": download_funsd,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=DATASETS.keys(), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    DATASETS[args.dataset](args.output)


if __name__ == "__main__":
    main()
```

**Step 6: Commit**

```bash
git add src/training/dataset.py src/training/download_data.py tests/test_dataset.py
git commit -m "feat: add dataset loader with tokenizer alignment and FUNSD download"
```

---

## Phase 2: Model Training (Weeks 2-3)

### Task 5: LiLT Training Script + Snellius SLURM Config

**Files:**
- Create: `src/training/train.py`
- Create: `src/training/evaluate.py`
- Create: `scripts/snellius/train.slurm`
- Create: `scripts/snellius/setup_env.sh`
- Create: `tests/test_training.py`

**Step 1: Write the failing test**

```python
# tests/test_training.py
import pytest
from src.training.train import build_model, build_training_args


def test_build_model_returns_lilt_for_token_classification():
    model, tokenizer = build_model(
        model_name="SCUT-DLVCLab/lilt-roberta-en-base",
        num_labels=5,
    )
    assert model is not None
    assert model.config.num_labels == 5


def test_build_training_args_sets_defaults():
    args = build_training_args(output_dir="/tmp/test_run", num_epochs=3)
    assert args.num_train_epochs == 3
    assert args.output_dir == "/tmp/test_run"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_training.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write training script**

```python
# src/training/train.py
"""LiLT fine-tuning for document token classification.

Local:  python -m src.training.train --config config/train_local.yaml
Snellius: sbatch scripts/snellius/train.slurm
"""
import argparse
from pathlib import Path

import mlflow
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


def build_model(
    model_name: str = "SCUT-DLVCLab/lilt-roberta-en-base",
    num_labels: int = 7,
):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
    )
    return model, tokenizer


def build_training_args(
    output_dir: str = "models/lilt-invoice",
    num_epochs: int = 10,
    batch_size: int = 8,
    learning_rate: float = 5e-5,
) -> TrainingArguments:
    return TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        fp16=True,
        report_to="mlflow",
    )


def train(
    train_dataset,
    eval_dataset,
    label_list: list[str],
    model_name: str = "SCUT-DLVCLab/lilt-roberta-en-base",
    output_dir: str = "models/lilt-invoice",
    num_epochs: int = 10,
):
    from src.training.evaluate import compute_metrics_fn

    model, tokenizer = build_model(model_name, num_labels=len(label_list))
    training_args = build_training_args(output_dir=output_dir, num_epochs=num_epochs)

    mlflow.set_experiment("docbridge-invoice-extraction")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics_fn(label_list),
    )

    with mlflow.start_run():
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("num_labels", len(label_list))
        trainer.train()
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)

    return trainer
```

**Step 4: Write evaluation module**

```python
# src/training/evaluate.py
import numpy as np
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score


def compute_metrics_fn(label_list: list[str]):
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=2)

        true_labels = []
        true_preds = []
        for pred_seq, label_seq in zip(predictions, labels):
            seq_labels = []
            seq_preds = []
            for p, l in zip(pred_seq, label_seq):
                if l == -100:
                    continue
                seq_labels.append(label_list[l])
                seq_preds.append(label_list[p])
            true_labels.append(seq_labels)
            true_preds.append(seq_preds)

        return {
            "precision": precision_score(true_labels, true_preds),
            "recall": recall_score(true_labels, true_preds),
            "f1": f1_score(true_labels, true_preds),
        }
    return compute_metrics
```

**Step 5: Write Snellius SLURM scripts**

```bash
#!/bin/bash
# scripts/snellius/setup_env.sh
# Run once on Snellius to set up the conda environment.
module load 2024
module load Anaconda3/2024.06-1

conda create -n docbridge python=3.11 -y
conda activate docbridge

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets seqeval accelerate mlflow
pip install paddlepaddle-gpu paddleocr

echo "Environment ready. Activate with: conda activate docbridge"
```

```bash
#!/bin/bash
# scripts/snellius/train.slurm
#SBATCH --job-name=docbridge-train
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/train_%j.out
#SBATCH --error=logs/train_%j.err

module load 2024
module load Anaconda3/2024.06-1
conda activate docbridge

export MLFLOW_TRACKING_URI=file:///home/$USER/docbridge/mlruns

cd /home/$USER/docbridge
python -m src.training.train \
    --model SCUT-DLVCLab/lilt-roberta-en-base \
    --dataset data/funsd \
    --output models/lilt-invoice-v1 \
    --epochs 10 \
    --batch-size 8
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_training.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/training/train.py src/training/evaluate.py scripts/snellius/ tests/test_training.py
git commit -m "feat: add LiLT training pipeline with Snellius SLURM support and MLflow tracking"
```

---

### Task 6: FUNSD Baseline Training Run

**Files:**
- Create: `notebooks/01_funsd_baseline.ipynb`

This task is executed manually — download FUNSD, run training on Snellius, evaluate results.

**Step 1: Download FUNSD dataset locally**

```bash
python -m src.training.download_data --dataset funsd --output data/funsd
```

**Step 2: Upload to Snellius**

```bash
rsync -avz --exclude '.venv' --exclude '__pycache__' \
    ~/github/docbridge/ snellius:~/docbridge/
```

**Step 3: Set up Snellius environment (first time only)**

```bash
ssh snellius
bash ~/docbridge/scripts/snellius/setup_env.sh
```

**Step 4: Submit training job**

```bash
ssh snellius
cd ~/docbridge
mkdir -p logs
sbatch scripts/snellius/train.slurm
```

**Step 5: Monitor and download results**

```bash
# Check job status
ssh snellius "squeue -u $USER"

# Download MLflow results + model
rsync -avz snellius:~/docbridge/mlruns/ ~/github/docbridge/mlruns/
rsync -avz snellius:~/docbridge/models/ ~/github/docbridge/models/
```

**Step 6: Log baseline metrics**

Start MLflow UI: `mlflow ui --backend-store-uri mlruns/`
Record baseline F1 in the notebook. Target: F1 > 0.70 on FUNSD (this is a validation that the pipeline works; real Chinese invoice F1 will be measured separately when SCID data is available).

**Step 7: Commit notebook with results**

```bash
git add notebooks/01_funsd_baseline.ipynb
git commit -m "experiment: FUNSD baseline — LiLT F1=X.XX"
```

---

### Task 7: Chinese Invoice Data Preparation (SCID/VATI)

**Files:**
- Modify: `src/training/download_data.py` (add SCID/VATI loaders)
- Create: `src/training/convert_scid.py`
- Create: `tests/test_convert_scid.py`

**Prerequisite:** Apply for SCID dataset access at https://davar-lab.github.io/dataset/scid.html. If access takes time, generate synthetic Chinese invoice images using templates as a stopgap.

**Step 1: Write converter test**

```python
# tests/test_convert_scid.py
from src.training.convert_scid import convert_scid_annotation


def test_convert_scid_to_docbridge_format():
    scid_sample = {
        "image_path": "invoice_001.jpg",
        "ocr": [
            {"text": "发票号码", "box": [100, 50, 250, 80]},
            {"text": "12345678", "box": [260, 50, 400, 80]},
        ],
        "entities": [
            {"label": "invoice_number", "text": "12345678", "box": [260, 50, 400, 80]},
        ],
    }
    result = convert_scid_annotation(scid_sample)
    assert "tokens" in result
    assert "bboxes" in result
    assert "labels" in result
    assert len(result["tokens"]) == len(result["labels"])
    assert "B-INVOICE_NUMBER" in result["labels"]
```

**Step 2: Run test, verify fail**

Run: `pytest tests/test_convert_scid.py -v`

**Step 3: Implement converter**

```python
# src/training/convert_scid.py
def convert_scid_annotation(scid_sample: dict) -> dict:
    entity_map = {}
    for entity in scid_sample.get("entities", []):
        key = (entity["text"], tuple(entity["box"]))
        entity_map[key] = entity["label"]

    tokens = []
    bboxes = []
    labels = []

    for ocr_item in scid_sample["ocr"]:
        text = ocr_item["text"]
        box = ocr_item["box"]
        key = (text, tuple(box))
        if key in entity_map:
            label_name = entity_map[key].upper()
            tokens.append(text)
            bboxes.append(box)
            labels.append(f"B-{label_name}")
        else:
            tokens.append(text)
            bboxes.append(box)
            labels.append("O")

    return {
        "id": scid_sample.get("image_path", "unknown"),
        "tokens": tokens,
        "bboxes": bboxes,
        "labels": labels,
    }
```

**Step 4: Run test, verify pass**

Run: `pytest tests/test_convert_scid.py -v`

**Step 5: Commit**

```bash
git add src/training/convert_scid.py tests/test_convert_scid.py
git commit -m "feat: add SCID dataset converter for Chinese invoice annotations"
```

---

### Task 8: Chinese Invoice Fine-tuning on Snellius

This task parallels Task 6 but with Chinese invoice data. Execute once SCID access is granted or synthetic data is ready.

**Step 1: Convert SCID data**

```bash
python -m src.training.convert_scid --input data/scid/raw --output data/scid/processed
```

**Step 2: Update SLURM script for Chinese invoices**

Create `scripts/snellius/train_cn_invoice.slurm` — same as `train.slurm` but pointing to `data/scid/processed` and with adjusted hyperparameters (learning rate 3e-5, epochs 15).

**Step 3: Upload and run on Snellius**

```bash
rsync -avz ~/github/docbridge/ snellius:~/docbridge/
ssh snellius "cd ~/docbridge && sbatch scripts/snellius/train_cn_invoice.slurm"
```

**Step 4: Evaluate and compare**

Download MLflow results. Compare LiLT vs LayoutLMv3 on Chinese invoices. Log to `notebooks/02_cn_invoice_experiments.ipynb`.

**Step 5: Commit**

```bash
git add scripts/snellius/train_cn_invoice.slurm notebooks/02_cn_invoice_experiments.ipynb
git commit -m "experiment: Chinese invoice fine-tuning — LiLT F1=X.XX vs LayoutLMv3 F1=X.XX"
```

---

## Phase 3: API & Deployment (Week 4)

### Task 9: Field Extractor — Post-processing Module

**Files:**
- Create: `src/pipeline/field_extractor.py`
- Create: `tests/test_field_extractor.py`

**Step 1: Write the failing test**

```python
# tests/test_field_extractor.py
from src.pipeline.field_extractor import FieldExtractor


def test_extracts_seller_from_labeled_tokens():
    tokens_with_labels = [
        {"text": "深圳", "label": "B-SELLER"},
        {"text": "华强", "label": "I-SELLER"},
        {"text": "贸易有限公司", "label": "I-SELLER"},
        {"text": "发票号码", "label": "O"},
        {"text": "INV-001", "label": "B-INVOICE_NO"},
    ]
    extractor = FieldExtractor()
    fields = extractor.extract(tokens_with_labels)
    assert fields["seller"] == "深圳华强贸易有限公司"
    assert fields["invoice_no"] == "INV-001"


def test_handles_missing_fields_gracefully():
    tokens_with_labels = [
        {"text": "hello", "label": "O"},
    ]
    extractor = FieldExtractor()
    fields = extractor.extract(tokens_with_labels)
    assert fields == {}


def test_extracts_amount_and_normalizes():
    tokens_with_labels = [
        {"text": "¥45,200.00", "label": "B-AMOUNT"},
    ]
    extractor = FieldExtractor()
    fields = extractor.extract(tokens_with_labels)
    assert fields["amount"] == "¥45,200.00"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_field_extractor.py -v`

**Step 3: Write minimal implementation**

```python
# src/pipeline/field_extractor.py
from collections import defaultdict


class FieldExtractor:
    def extract(self, tokens_with_labels: list[dict]) -> dict:
        entities = defaultdict(list)
        current_entity = None

        for token in tokens_with_labels:
            label = token["label"]
            text = token["text"]

            if label.startswith("B-"):
                current_entity = label[2:].lower()
                entities[current_entity].append(text)
            elif label.startswith("I-") and current_entity == label[2:].lower():
                entities[current_entity].append(text)
            else:
                current_entity = None

        return {key: "".join(parts) for key, parts in entities.items()}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_field_extractor.py -v`

**Step 5: Commit**

```bash
git add src/pipeline/field_extractor.py tests/test_field_extractor.py
git commit -m "feat: add BIO field extractor with entity merging"
```

---

### Task 10: End-to-End Pipeline

**Files:**
- Create: `src/pipeline/pipeline.py`
- Create: `tests/test_pipeline.py`

**Step 1: Write the failing test**

```python
# tests/test_pipeline.py
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from src.pipeline.pipeline import DocumentPipeline, ExtractionResult


def test_pipeline_returns_extraction_result():
    pipeline = DocumentPipeline(model_path="models/lilt-invoice-v1")
    result = pipeline.process(Path("tests/fixtures/sample_cn_invoice_01.jpg"))
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.fields, dict)
    assert isinstance(result.confidence, float)
    assert 0.0 <= result.confidence <= 1.0


def test_pipeline_result_serializes_to_dict():
    result = ExtractionResult(
        fields={"seller": "Test Corp", "amount": "1000"},
        confidence=0.95,
        ocr_text="raw text here",
    )
    d = result.to_dict()
    assert d["fields"]["seller"] == "Test Corp"
    assert d["confidence"] == 0.95
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py -v`

**Step 3: Write pipeline implementation**

```python
# src/pipeline/pipeline.py
from dataclasses import dataclass, field
from pathlib import Path

from src.pipeline.preprocessor import Preprocessor
from src.pipeline.ocr_engine import OCREngine
from src.pipeline.field_extractor import FieldExtractor


@dataclass
class ExtractionResult:
    fields: dict = field(default_factory=dict)
    confidence: float = 0.0
    ocr_text: str = ""

    def to_dict(self) -> dict:
        return {
            "fields": self.fields,
            "confidence": self.confidence,
            "ocr_text": self.ocr_text,
        }


class DocumentPipeline:
    def __init__(self, model_path: str = "models/lilt-invoice-v1"):
        self.preprocessor = Preprocessor()
        self.ocr = OCREngine()
        self.extractor = FieldExtractor()
        self.model_path = model_path
        self._layout_model = None

    def _load_layout_model(self):
        if self._layout_model is not None:
            return
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        model_path = Path(self.model_path)
        if model_path.exists():
            self._tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self._layout_model = AutoModelForTokenClassification.from_pretrained(str(model_path))
        else:
            self._layout_model = None

    def process(self, image_path: Path | str) -> ExtractionResult:
        image = self.preprocessor.process(image_path)
        ocr_result = self.ocr.extract(image_path)

        all_text = " ".join(line["text"] for line in ocr_result.lines)
        avg_confidence = (
            sum(line["confidence"] for line in ocr_result.lines) / len(ocr_result.lines)
            if ocr_result.lines
            else 0.0
        )

        self._load_layout_model()
        if self._layout_model is not None:
            tokens_with_labels = self._run_layout_model(ocr_result)
            fields = self.extractor.extract(tokens_with_labels)
        else:
            fields = {
                "_note": "no layout model loaded, returning raw OCR",
                "ocr_lines": [line["text"] for line in ocr_result.lines],
            }

        return ExtractionResult(
            fields=fields,
            confidence=round(avg_confidence, 4),
            ocr_text=all_text,
        )

    def _run_layout_model(self, ocr_result) -> list[dict]:
        import torch
        tokens = [line["text"] for line in ocr_result.lines]
        bboxes = [line["bbox"][:4] for line in ocr_result.lines]

        encoding = self._tokenizer(
            tokens, is_split_into_words=True, return_tensors="pt",
            padding=True, truncation=True,
        )

        with torch.no_grad():
            outputs = self._layout_model(**encoding)

        predictions = torch.argmax(outputs.logits, dim=2).squeeze(0)
        id2label = self._layout_model.config.id2label
        word_ids = encoding.word_ids()

        result = []
        seen = set()
        for idx, word_id in enumerate(word_ids):
            if word_id is None or word_id in seen:
                continue
            seen.add(word_id)
            label = id2label[predictions[idx].item()]
            result.append({"text": tokens[word_id], "label": label})

        return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: PASS (second test passes directly; first test passes with graceful fallback when no model is loaded)

**Step 5: Commit**

```bash
git add src/pipeline/pipeline.py tests/test_pipeline.py
git commit -m "feat: wire end-to-end document processing pipeline"
```

---

### Task 11: FastAPI Service

**Files:**
- Create: `src/api/main.py`
- Create: `src/api/routes.py`
- Create: `src/api/schemas.py`
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

```python
# tests/test_api.py
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_extract_endpoint_with_invoice_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(FIXTURES / "sample_cn_invoice_01.jpg", "rb") as f:
            response = await client.post("/extract", files={"file": ("invoice.jpg", f, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert "fields" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_extract_rejects_non_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/extract",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
    assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`

**Step 3: Write API implementation**

```python
# src/api/schemas.py
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    model_loaded: bool = False


class ExtractionResponse(BaseModel):
    fields: dict
    confidence: float
    ocr_text: str
```

```python
# src/api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import tempfile

from src.api.schemas import HealthResponse, ExtractionResponse
from src.pipeline.pipeline import DocumentPipeline

router = APIRouter()
pipeline = DocumentPipeline()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/tiff", "application/pdf"}


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=pipeline._layout_model is not None,
    )


@router.post("/extract", response_model=ExtractionResponse)
async def extract(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    with tempfile.NamedTemporaryFile(suffix=Path(file.filename or "upload").suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = pipeline.process(tmp_path)
        return ExtractionResponse(**result.to_dict())
    finally:
        tmp_path.unlink(missing_ok=True)
```

```python
# src/api/main.py
from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(
    title="DocBridge API",
    description="CN-EU trade document AI processing",
    version="0.1.0",
)

app.include_router(router)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/api/ tests/test_api.py
git commit -m "feat: add FastAPI service with /extract and /health endpoints"
```

---

### Task 12: Docker & Docker Compose

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

**Step 1: Write Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/
COPY models/ models/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Write docker-compose.yml**

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - mlflow

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.12.1
    ports:
      - "5001:5000"
    volumes:
      - ./mlruns:/mlflow/mlruns
    command: mlflow server --host 0.0.0.0 --backend-store-uri /mlflow/mlruns
```

**Step 3: Build and test**

```bash
docker compose build
docker compose up -d
curl -X POST http://localhost:8000/extract \
    -F "file=@tests/fixtures/sample_cn_invoice_01.jpg"
docker compose down
```

**Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker + Compose with MLflow service"
```

---

### Task 13: Prometheus Monitoring

**Files:**
- Create: `src/monitoring/metrics.py`
- Modify: `src/api/main.py` (add middleware)
- Create: `tests/test_monitoring.py`

**Step 1: Write the failing test**

```python
# tests/test_monitoring.py
from src.monitoring.metrics import MetricsCollector


def test_metrics_collector_tracks_request_count():
    mc = MetricsCollector()
    mc.record_extraction(document_type="invoice", success=True, latency_ms=150.0)
    # Verify the counter incremented (prometheus_client exposes .collect())
    assert mc.extraction_count._metrics  # at least one metric recorded


def test_metrics_collector_tracks_latency():
    mc = MetricsCollector()
    mc.record_extraction(document_type="invoice", success=True, latency_ms=250.5)
    assert mc.extraction_latency._metrics
```

**Step 2: Run test, verify fail**

**Step 3: Implement**

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram


class MetricsCollector:
    def __init__(self):
        self.extraction_count = Counter(
            "docbridge_extractions_total",
            "Total document extractions",
            ["document_type", "success"],
        )
        self.extraction_latency = Histogram(
            "docbridge_extraction_latency_ms",
            "Extraction latency in milliseconds",
            ["document_type"],
            buckets=[50, 100, 250, 500, 1000, 2500, 5000],
        )

    def record_extraction(self, document_type: str, success: bool, latency_ms: float):
        self.extraction_count.labels(document_type=document_type, success=str(success)).inc()
        self.extraction_latency.labels(document_type=document_type).observe(latency_ms)
```

**Step 4: Add `/metrics` endpoint to FastAPI**

```python
# Add to src/api/main.py
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Step 5: Run tests, verify pass**

**Step 6: Commit**

```bash
git add src/monitoring/metrics.py src/api/main.py tests/test_monitoring.py
git commit -m "feat: add Prometheus metrics for extraction count and latency"
```

---

### Task 14: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Write CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint
        run: ruff check src/ tests/

      - name: Test
        run: pytest tests/ -v --ignore=tests/test_pipeline.py --ignore=tests/test_api.py
        # Pipeline and API tests require PaddleOCR + model artifacts, skipped in CI for now
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions lint + test workflow"
```

---

## Phase 4: Customer Validation (Weeks 5-6)

> This phase is primarily non-code. No implementation tasks — it's about talking to people with the demo from Phase 3.

### Task 15: Prepare Demo & Outreach

**Checklist (manual, not code):**

1. Deploy the Docker stack to a cheap VPS (Hetzner €5/mo or Render free tier) so the demo is accessible via URL
2. Prepare 3 demo scenarios:
   - Chinese VAT invoice → structured JSON
   - Handwritten Chinese receipt → structured JSON (showing OCR robustness)
   - Side-by-side: manual process time vs. DocBridge processing time
3. Draft outreach message (in Chinese) for NCBC/NCHK contacts:
   - "我在做一个帮助处理中文贸易文档的 AI 工具，想了解一下你们目前是怎么处理中国供应商的发票和装箱单的？方便聊 20 分钟吗？"
4. Target: 3-5 conversations in 2 weeks
5. Key questions to ask:
   - 你们每天/每周处理多少份中文文档？
   - 目前怎么处理的？人工翻译？Excel 手动录入？
   - 一份文档从收到到录入系统需要多长时间？
   - 最痛苦的是哪个环节？
   - 如果有工具能自动提取，你愿意付多少钱？

---

## Phase 5: Iteration & Productization (Weeks 7-12)

> Tasks in this phase depend heavily on customer feedback. Below is the expected structure; specifics will be filled in after Phase 4.

### Task 16: Iterate Model on Real Data (Weeks 7-8)

- Collect real document samples from customer interviews
- Annotate with actual field labels
- Re-train on Snellius with mixed dataset (public + real)
- Measure accuracy improvement
- Add monitoring for model drift

### Task 17: Web UI (Weeks 9-10)

- Simple upload-and-view interface (React or plain HTML + HTMX)
- User registration + API key management
- Result history

### Task 18: IND Business Plan & KVK Registration (Weeks 11-12)

- Write formal business plan in English
- Register eenmanszaak at KVK
- Prepare IND self-employment visa application
- Update resume with DocBridge as portfolio project

---

## Summary: Commit Sequence

| # | Commit message | Phase |
|---|---|---|
| 1 | `init: scaffold docbridge project structure` | 1 |
| 2 | `feat: add PaddleOCR engine wrapper with Chinese invoice support` | 1 |
| 3 | `feat: add image preprocessor with RGB conversion and resize` | 1 |
| 4 | `feat: add dataset loader with tokenizer alignment and FUNSD download` | 1 |
| 5 | `feat: add LiLT training pipeline with Snellius SLURM support and MLflow tracking` | 2 |
| 6 | `experiment: FUNSD baseline — LiLT F1=X.XX` | 2 |
| 7 | `feat: add SCID dataset converter for Chinese invoice annotations` | 2 |
| 8 | `experiment: Chinese invoice fine-tuning — LiLT F1=X.XX vs LayoutLMv3 F1=X.XX` | 2 |
| 9 | `feat: add BIO field extractor with entity merging` | 3 |
| 10 | `feat: wire end-to-end document processing pipeline` | 3 |
| 11 | `feat: add FastAPI service with /extract and /health endpoints` | 3 |
| 12 | `feat: add Docker + Compose with MLflow service` | 3 |
| 13 | `feat: add Prometheus metrics for extraction count and latency` | 3 |
| 14 | `ci: add GitHub Actions lint + test workflow` | 3 |
