"""人臉辨識核心 — InsightFace 包裝"""
from __future__ import annotations

from typing import Optional

import numpy as np
from insightface.app import FaceAnalysis
from loguru import logger

from app.config import settings
from app.database import Database
from app.utils import cosine_similarity


class FaceEngine:
    def __init__(self) -> None:
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if settings.USE_GPU
            else ["CPUExecutionProvider"]
        )
        logger.info(
            f"Loading InsightFace model: {settings.FACE_MODEL_NAME} "
            f"(providers={providers})"
        )
        self.app = FaceAnalysis(
            name=settings.FACE_MODEL_NAME,
            root=str(settings.MODELS_DIR),
            providers=providers,
        )
        # ctx_id: 0 = first CUDA device (if available), -1 = CPU
        # When CUDA fails, ORT auto-falls back to CPU regardless of ctx_id.
        self.app.prepare(ctx_id=0, det_thresh=settings.DETECTION_THRESHOLD)
        actual = self.app.models["detection"].session.get_providers()
        logger.info(f"InsightFace ready (active providers: {actual})")

    def detect(self, image_bgr: np.ndarray) -> list:
        """回傳所有偵測到的 Face 物件 (含 bbox + embedding)"""
        return self.app.get(image_bgr)

    def get_embedding(self, image_bgr: np.ndarray) -> Optional[np.ndarray]:
        """取最大那張臉的 embedding (註冊用)"""
        faces = self.detect(image_bgr)
        if not faces:
            return None
        # 選最大那張臉 (按 bbox 面積)
        face = max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
        )
        return face.normed_embedding.astype(np.float32)

    def recognize(
        self, image_bgr: np.ndarray, db: Database
    ) -> tuple[Optional[str], float]:
        """1:N 比對，回傳 (user_id, similarity) 或 (None, best_score)"""
        emb = self.get_embedding(image_bgr)
        if emb is None:
            return None, 0.0

        best_match: Optional[str] = None
        best_score = -1.0

        for user in db.get_all_users():
            score = cosine_similarity(emb, user["embedding"])
            if score > best_score:
                best_score = score
                best_match = user["user_id"]

        if best_score >= settings.RECOGNITION_THRESHOLD:
            return best_match, best_score
        return None, best_score


_engine: Optional[FaceEngine] = None


def get_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine
