"""Seed the DB with N demo users extracted from a single group photo.

Use case: portfolio demo without a webcam — bundles 6 distinct people
from insightface's bundled t1.jpg as Person 1..6, then any one of those
faces sent to /api/recognize will match.

Usage (from repo root):
  venv\Scripts\python.exe scripts\seed_demo.py             # default t1.jpg
  venv\Scripts\python.exe scripts\seed_demo.py --reset     # clear DB first
  venv\Scripts\python.exe scripts\seed_demo.py path\to\group.jpg

Optional --gpu uses USE_GPU=true for this run.
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# Allow running as `python scripts/seed_demo.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import insightface

# Cross-platform path to insightface's bundled t1.jpg (works in venv on
# Windows, system Python in Linux Docker, etc).
DEFAULT_IMAGE = (
    Path(insightface.__file__).parent / "data" / "images" / "t1.jpg"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "image",
        nargs="?",
        default=str(DEFAULT_IMAGE),
        help=f"Group photo path (default: {DEFAULT_IMAGE})",
    )
    parser.add_argument("--reset", action="store_true", help="Delete existing users first")
    parser.add_argument("--gpu", action="store_true", help="Force USE_GPU=true for this run")
    parser.add_argument(
        "--name-prefix", default="Person", help="Prefix for generated names (default: Person)"
    )
    args = parser.parse_args()

    if args.gpu:
        os.environ["USE_GPU"] = "true"

    # Imports after env override so settings reads USE_GPU correctly
    from app.database import get_db
    from app.face_engine import get_engine

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"ERROR: image not found: {img_path}", file=sys.stderr)
        return 1

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"ERROR: cv2 cannot read image: {img_path}", file=sys.stderr)
        return 1
    print(f"Loaded image: {img_path} {img.shape}")

    engine = get_engine()
    db = get_db()

    if args.reset:
        existing = db.get_all_users()
        for u in existing:
            db.delete_user(u["user_id"])
        print(f"Reset: deleted {len(existing)} existing user(s)")

    faces = engine.detect(img)
    if not faces:
        print("ERROR: no faces detected", file=sys.stderr)
        return 1

    # Sort left-to-right (so Person 1 is leftmost) — stable for repeat runs
    faces.sort(key=lambda f: f.bbox[0])
    print(f"Detected {len(faces)} face(s); seeding as {args.name_prefix} 1..{len(faces)}")

    crops_dir = Path(__file__).resolve().parents[1] / "data" / "demo_crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    h_img, w_img = img.shape[:2]
    margin = 60   # need enough surrounding context for det_10g to re-detect

    for i, face in enumerate(faces, start=1):
        name = f"{args.name_prefix} {i}"
        emb = face.normed_embedding.astype("float32")
        bbox = [int(v) for v in face.bbox]
        det_score = float(face.det_score)
        uid = uuid.uuid4().hex[:12]
        db.add_user(uid, name, emb)

        # Save a single-face crop for one-shot recognition demos
        x1, y1, x2, y2 = bbox
        crop = img[
            max(0, y1 - margin) : min(h_img, y2 + margin),
            max(0, x1 - margin) : min(w_img, x2 + margin),
        ]
        crop_path = crops_dir / f"person{i}.jpg"
        cv2.imwrite(str(crop_path), crop)
        print(
            f"  -> {name:12s} uid={uid} bbox={bbox} det_score={det_score:.3f}"
            f"  crop={crop_path.relative_to(crops_dir.parents[1])}"
        )

    print(f"\nDone. {len(faces)} user(s) registered + {len(faces)} crops in {crops_dir.relative_to(crops_dir.parents[1])}/")
    print("\nTry recognizing a single face crop:")
    print(f"  curl -X POST http://127.0.0.1:8000/api/recognize \\")
    print(f"    -F 'image=@data/demo_crops/person1.jpg'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
