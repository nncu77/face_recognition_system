"""活體偵測 — MediaPipe FaceMesh + EAR (eye aspect ratio) 眨眼"""
from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np
import mediapipe as mp

from app.config import settings


# MediaPipe FaceMesh 468 landmark indices, 6 點 / 眼
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def _eye_aspect_ratio(landmarks: np.ndarray, idx: list[int]) -> float:
    """EAR = (|p2-p6| + |p3-p5|) / (2*|p1-p4|)"""
    p = landmarks[idx]
    a = np.linalg.norm(p[1] - p[5])
    b = np.linalg.norm(p[2] - p[4])
    c = np.linalg.norm(p[0] - p[3])
    if c == 0:
        return 0.0
    return float((a + b) / (2.0 * c))


class LivenessDetector:
    def __init__(self) -> None:
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.blink_count = 0
        self.eye_closed = False
        self.ear_history: deque[float] = deque(maxlen=30)

    def update(self, image_bgr: np.ndarray) -> Optional[dict]:
        """單張影像 → 更新 EAR + 偵測眨眼。回傳 dict (or None 如果沒臉)"""
        rgb = image_bgr[:, :, ::-1]
        result = self.mesh.process(rgb)
        if not result.multi_face_landmarks:
            return None

        h, w = image_bgr.shape[:2]
        lms = result.multi_face_landmarks[0].landmark
        coords = np.array([(lm.x * w, lm.y * h) for lm in lms], dtype=np.float32)

        ear_left = _eye_aspect_ratio(coords, LEFT_EYE)
        ear_right = _eye_aspect_ratio(coords, RIGHT_EYE)
        ear = (ear_left + ear_right) / 2.0
        self.ear_history.append(ear)

        # 偵測眨眼
        if ear < settings.LIVENESS_BLINK_THRESHOLD:
            self.eye_closed = True
        else:
            if self.eye_closed:
                self.blink_count += 1
                self.eye_closed = False

        is_live = self.blink_count >= settings.LIVENESS_REQUIRED_BLINKS

        return {
            "is_live": is_live,
            "blink_count": self.blink_count,
            "ear": float(ear),
        }

    def reset(self) -> None:
        """重置狀態"""
        self.blink_count = 0
        self.eye_closed = False
        self.ear_history.clear()
