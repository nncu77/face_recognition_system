"""人臉辨識核心 — InsightFace 包裝"""
from __future__ import annotations

import glob
import os
import sys
from typing import Optional

from app.config import settings


def _ensure_cuda_on_path() -> Optional[str]:
    """Windows: 把 CUDA bin 加進 PATH 才能讓 onnxruntime-gpu 找到
    cudart64_*.dll / cudnn*.dll。優先用 CUDA_PATH，fallback 找
    `C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.*`
    最新版。回傳實際加入的 bin path（或 None 表示沒找到）。"""
    if sys.platform != "win32":
        return None
    cuda_root = os.environ.get("CUDA_PATH")
    if not cuda_root or not os.path.isdir(cuda_root):
        candidates = sorted(
            glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.*")
        )
        cuda_root = candidates[-1] if candidates else None
    if not cuda_root:
        return None
    cuda_bin = os.path.join(cuda_root, "bin")
    if not os.path.isdir(cuda_bin):
        return None
    if cuda_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = cuda_bin + os.pathsep + os.environ.get("PATH", "")
    return cuda_bin


# Must run BEFORE the onnxruntime/insightface imports below — otherwise
# onnxruntime_providers_cuda.dll fails to load its dependencies.
_cuda_bin_added = _ensure_cuda_on_path() if settings.USE_GPU else None

import numpy as np  # noqa: E402
from insightface.app import FaceAnalysis  # noqa: E402
from loguru import logger  # noqa: E402

from app.database import Database  # noqa: E402
from app.utils import cosine_similarity  # noqa: E402

if _cuda_bin_added:
    logger.info(f"Added CUDA bin to PATH: {_cuda_bin_added}")


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

    def _largest_face(self, image_bgr: np.ndarray):
        """從所有偵測到的臉選 bbox 面積最大的"""
        faces = self.detect(image_bgr)
        if not faces:
            return None
        return max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
        )

    def get_embedding(self, image_bgr: np.ndarray) -> Optional[np.ndarray]:
        """取最大那張臉的 embedding (註冊用)"""
        face = self._largest_face(image_bgr)
        return None if face is None else face.normed_embedding.astype(np.float32)

    def recognize(self, image_bgr: np.ndarray, db: Database) -> dict:
        """1:N 比對。回傳 dict:
        {user_id, similarity, bbox=[x1,y1,x2,y2]|None, det_score}
        user_id 為 None 表示沒臉或低於 RECOGNITION_THRESHOLD。
        """
        face = self._largest_face(image_bgr)
        if face is None:
            return {"user_id": None, "similarity": 0.0, "bbox": None, "det_score": 0.0}

        emb = face.normed_embedding.astype(np.float32)
        bbox = [int(v) for v in face.bbox]
        det_score = float(face.det_score)

        best_match: Optional[str] = None
        best_score = -1.0
        for user in db.get_all_users():
            score = cosine_similarity(emb, user["embedding"])
            if score > best_score:
                best_score = score
                best_match = user["user_id"]

        matched = best_match if best_score >= settings.RECOGNITION_THRESHOLD else None
        return {
            "user_id": matched,
            "similarity": float(best_score),
            "bbox": bbox,
            "det_score": det_score,
        }


_engine: Optional[FaceEngine] = None


def get_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine
