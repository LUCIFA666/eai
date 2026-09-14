"""4.5 — CLIP zero-shot classification on a procedural test image."""
from __future__ import annotations

import os
import sys
from typing import List

import numpy as np
import torch
from PIL import Image, ImageDraw

import open_clip as clip

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception"))
os.makedirs(RUN_DIR, exist_ok=True)


def make_color_image(color: str = "red", size: int = 224) -> Image.Image:
    img = Image.new("RGB", (size, size), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)
    palette = {
        "red": (220, 40, 40),
        "green": (40, 180, 70),
        "blue": (40, 70, 220),
        "yellow": (220, 200, 40),
    }
    rgb = palette[color]
    draw.rectangle([28, 28, 196, 196], fill=rgb)
    rng = np.random.default_rng(42)
    arr = np.array(img)
    noise = rng.integers(-10, 10, size=arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


PROMPTS: List[str] = [
    "a photo of a red square",
    "a photo of a green square",
    "a photo of a blue square",
    "a photo of a yellow square",
    "a photo of a cat",
    "a photo of a robot arm",
]


def main() -> None:
    print(f"device = {DEVICE}")

    # ===================== 【核心修改】 =====================
    model, preprocess_train, preprocess_val = clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai", device=DEVICE
    )
    tokenizer = clip.get_tokenizer("ViT-B-32")
    model.eval()
    # ========================================================

    test_set = [(c, make_color_image(c)) for c in ("red", "green", "blue", "yellow")]

    print("\n--- Zero-shot classification ---")
    print(f"{'truth':8s} {'top-1 prompt':38s} {'p_top':>7s} {'p_correct':>10s}")
    correct = 0

    with torch.no_grad():
        text = tokenizer(PROMPTS).to(DEVICE)
        text_features = model.encode_text(text)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        for truth, img in test_set:
            x = preprocess_val(img).unsqueeze(0).to(DEVICE)
            image_features = model.encode_image(x)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            logits = (100.0 * image_features @ text_features.T).softmax(dim=-1).cpu().numpy().flatten()
            top1 = np.argmax(logits)
            correct_idx = next(i for i, p in enumerate(PROMPTS) if truth in p)

            if top1 == correct_idx:
                correct += 1

            print(f"{truth:8s} {PROMPTS[top1]:38s} {logits[top1]:7.3f} {logits[correct_idx]:10.3f}")

    print(f"accuracy = {correct}/{len(test_set)}")
    print("✅ 运行成功！")


if __name__ == "__main__":
    main()