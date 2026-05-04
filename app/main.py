"""FastAPI 主程式"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.face_engine import get_engine
from app.liveness import LivenessDetector
from app.utils import read_image_bytes


app = FastAPI(title="Face Recognition System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- response schemas ----

class RegisterResponse(BaseModel):
    user_id: str
    name: str
    message: str


class RecognizeResponse(BaseModel):
    matched: bool
    user_id: Optional[str]
    name: Optional[str]
    similarity: float
    is_live: bool


class UserInfo(BaseModel):
    user_id: str
    name: str
    created_at: Optional[str]


class LogEntry(BaseModel):
    user_id: Optional[str]
    name: Optional[str]
    similarity: float
    timestamp: str
    is_live: bool


class LivenessResponse(BaseModel):
    is_live: bool
    blink_count: int
    required_blinks: int
    frames_processed: int
    frames_with_face: int
    ear_history: list[float]


# ---- endpoints ----

@app.get("/")
def root() -> dict:
    return {
        "name": "Face Recognition System",
        "model": settings.FACE_MODEL_NAME,
        "recognition_threshold": settings.RECOGNITION_THRESHOLD,
    }


@app.post("/api/register", response_model=RegisterResponse)
async def register(
    name: str = Form(...), image: UploadFile = File(...)
) -> RegisterResponse:
    data = await image.read()
    img = read_image_bytes(data)

    engine = get_engine()
    emb = engine.get_embedding(img)
    if emb is None:
        raise HTTPException(status_code=400, detail="未偵測到人臉")

    user_id = uuid.uuid4().hex[:12]
    get_db().add_user(user_id, name, emb)
    logger.info(f"Registered user {user_id} ({name})")
    return RegisterResponse(user_id=user_id, name=name, message="註冊成功")


@app.post("/api/recognize", response_model=RecognizeResponse)
async def recognize(
    image: UploadFile = File(...), is_live: bool = Form(False)
) -> RecognizeResponse:
    data = await image.read()
    img = read_image_bytes(data)

    engine = get_engine()
    db = get_db()
    user_id, score = engine.recognize(img, db)

    name: Optional[str] = None
    if user_id:
        u = db.get_user(user_id)
        name = u["name"] if u else None

    db.log_recognition(user_id, score, is_live)
    return RecognizeResponse(
        matched=user_id is not None,
        user_id=user_id,
        name=name,
        similarity=float(score),
        is_live=is_live,
    )


@app.get("/api/users", response_model=list[UserInfo])
def list_users() -> list[UserInfo]:
    return [
        UserInfo(
            user_id=u["user_id"], name=u["name"], created_at=u.get("created_at")
        )
        for u in get_db().get_all_users()
    ]


@app.delete("/api/users/{user_id}")
def delete_user(user_id: str) -> dict:
    get_db().delete_user(user_id)
    return {"message": "deleted", "user_id": user_id}


@app.get("/api/logs", response_model=list[LogEntry])
def list_logs(limit: int = 50) -> list[LogEntry]:
    return [LogEntry(**log) for log in get_db().get_recent_logs(limit)]


@app.post("/api/liveness", response_model=LivenessResponse)
async def liveness(frames: list[UploadFile] = File(...)) -> LivenessResponse:
    """多 frame 上傳 → 連續餵 LivenessDetector → 回傳 final state。
    Client 收 ~30 frames 過 ~3 秒 (10 FPS)，要求自然眨眼 ≥2 次"""
    if not frames:
        raise HTTPException(status_code=400, detail="至少要 1 個 frame")

    detector = LivenessDetector()
    frames_with_face = 0

    for f in frames:
        data = await f.read()
        img = read_image_bytes(data)
        result = detector.update(img)
        if result is not None:
            frames_with_face += 1

    return LivenessResponse(
        is_live=detector.blink_count >= settings.LIVENESS_REQUIRED_BLINKS,
        blink_count=detector.blink_count,
        required_blinks=settings.LIVENESS_REQUIRED_BLINKS,
        frames_processed=len(frames),
        frames_with_face=frames_with_face,
        ear_history=list(detector.ear_history),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
