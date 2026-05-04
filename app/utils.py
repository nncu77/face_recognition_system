"""工具函數：圖像 IO、embedding 序列化、相似度"""
from __future__ import annotations

import io
import numpy as np
from PIL import Image


def read_image_bytes(data: bytes) -> np.ndarray:
    """位元組 → BGR np.ndarray (給 InsightFace / OpenCV 用)"""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    rgb = np.array(img)
    return rgb[:, :, ::-1].copy()  # RGB → BGR


def embedding_to_bytes(emb: np.ndarray) -> bytes:
    """float32 embedding → bytes (存 SQLite BLOB)"""
    return emb.astype(np.float32).tobytes()


def bytes_to_embedding(data: bytes) -> np.ndarray:
    """bytes → float32 embedding"""
    return np.frombuffer(data, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """餘弦相似度，回傳 [-1, 1]"""
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
