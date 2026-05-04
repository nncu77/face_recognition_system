"""Smoke tests — 不需要 InsightFace model 也能跑 (DB + utils + EAR 純算式)"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.database import Database
from app.liveness import LEFT_EYE, _eye_aspect_ratio
from app.utils import bytes_to_embedding, cosine_similarity, embedding_to_bytes


def test_cosine_similarity_identical_is_one() -> None:
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert cosine_similarity(a, a) == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal_is_zero() -> None:
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)


def test_embedding_round_trip() -> None:
    emb = np.random.rand(512).astype(np.float32)
    restored = bytes_to_embedding(embedding_to_bytes(emb))
    np.testing.assert_array_almost_equal(emb, restored)


def test_database_user_crud() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(db_path=Path(tmp) / "test.db")
        emb = np.random.rand(512).astype(np.float32)
        db.add_user("uid1", "Alice", emb)

        users = db.get_all_users()
        assert len(users) == 1
        assert users[0]["name"] == "Alice"
        np.testing.assert_array_almost_equal(users[0]["embedding"], emb)

        db.delete_user("uid1")
        assert db.get_all_users() == []


def test_database_log_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(db_path=Path(tmp) / "test.db")
        db.log_recognition("uid1", 0.87, is_live=True)
        logs = db.get_recent_logs(10)
        assert len(logs) == 1
        assert logs[0]["similarity"] == 0.87
        assert logs[0]["is_live"] is True


def test_ear_open_eye() -> None:
    """睜開的眼睛 EAR 應該 ~0.3, 閉眼 ~0.05"""
    # 模擬睜眼 6 點 (典型比例)
    landmarks = np.zeros((468, 2), dtype=np.float32)
    pts = np.array(
        [
            [0, 0],   # p1 (左角)
            [10, -3], # p2 (上左)
            [20, -3], # p3 (上右)
            [30, 0],  # p4 (右角)
            [20, 3],  # p5 (下右)
            [10, 3],  # p6 (下左)
        ],
        dtype=np.float32,
    )
    for i, idx in enumerate(LEFT_EYE):
        landmarks[idx] = pts[i]

    ear = _eye_aspect_ratio(landmarks, LEFT_EYE)
    assert 0.15 < ear < 0.30
