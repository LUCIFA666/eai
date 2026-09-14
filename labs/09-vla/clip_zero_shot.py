"""9.2 — CLIP zero-shot classification on synthetic geometric shapes.

We *generate* a tiny image set with Pillow (no internet needed for data),
then ask ``openai/clip-vit-base-patch32`` to rank a fixed set of text
prompts.  The point is not accuracy on toy data — it's to show the
``text_features @ image_features`` similarity recipe that almost every
VLA inherits from.

Run:
    python labs/09-vla/clip_zero_shot.py

Outputs:
- prints top-3 predictions per image
- writes ``runs/09-vla/clip_predictions.json``
- writes ``runs/09-vla/synthetic_shapes/{red_circle,blue_square,green_triangle}.png``
"""
from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image, ImageDraw
from transformers import CLIPModel, CLIPProcessor

# Reproducibility — CLIP forward is deterministic but generated images
# depend on PIL only, so no rng is needed.
MODEL_ID = "openai/clip-vit-base-patch32"
IMG_SIZE = 224
OUT_DIR = Path("runs/09-vla")
IMG_DIR = OUT_DIR / "synthetic_shapes"
JSON_OUT = OUT_DIR / "clip_predictions.json"

# Prompt set: 9 candidate labels for a 3-class problem.  The 6 distractors
# probe whether CLIP picks color + shape together rather than ignoring one.
LABELS = [
    "a red circle",
    "a blue square",
    "a green triangle",
    "a red square",
    "a blue circle",
    "a green circle",
    "a yellow star",
    "a black rectangle",
    "an empty white image",
]


def make_red_circle() -> Image.Image:
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), "white")
    d = ImageDraw.Draw(img)
    d.ellipse([56, 56, 168, 168], fill=(220, 30, 30))
    return img


def make_blue_square() -> Image.Image:
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, 164, 164], fill=(30, 60, 220))
    return img


def make_green_triangle() -> Image.Image:
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), "white")
    d = ImageDraw.Draw(img)
    d.polygon([(112, 50), (50, 175), (174, 175)], fill=(30, 170, 60))
    return img


SHAPES = {
    "red_circle": (make_red_circle, "a red circle"),
    "blue_square": (make_blue_square, "a blue square"),
    "green_triangle": (make_green_triangle, "a green triangle"),
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[clip] device = {device}; model = {MODEL_ID}")

    print("[clip] loading processor + model (first time downloads ~600MB)...")
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    model = CLIPModel.from_pretrained(MODEL_ID).to(device).eval()

    records: list[dict] = []
    for name, (maker, gt) in SHAPES.items():
        img = maker()
        img_path = IMG_DIR / f"{name}.png"
        img.save(img_path)

        inputs = processor(text=LABELS, images=img, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=-1).cpu().tolist()
        ranked = sorted(zip(LABELS, probs), key=lambda kv: -kv[1])
        top3 = ranked[:3]
        rec = {
            "image": str(img_path),
            "ground_truth": gt,
            "top1": top3[0][0],
            "top1_prob": round(top3[0][1], 4),
            "top3": [(lbl, round(p, 4)) for lbl, p in top3],
            "correct_top1": top3[0][0] == gt,
        }
        records.append(rec)
        print(
            f"[clip] {name:>16}  gt='{gt}'  top1='{top3[0][0]}' "
            f"({top3[0][1]:.3f})  ok={rec['correct_top1']}"
        )

    correct = sum(r["correct_top1"] for r in records)
    summary = {
        "model": MODEL_ID,
        "device": device,
        "num_images": len(records),
        "num_correct_top1": correct,
        "top1_accuracy": round(correct / len(records), 4),
        "labels": LABELS,
        "records": records,
    }
    with JSON_OUT.open("w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(
        f"[clip] top-1 accuracy = {correct}/{len(records)} "
        f"= {summary['top1_accuracy']:.2%}"
    )
    print(f"[clip] wrote {JSON_OUT}")


if __name__ == "__main__":
    main()
