"""專案設定檔"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    FACES_DIR: Path = DATA_DIR / "faces"
    MODELS_DIR: Path = BASE_DIR / "models"
    DB_PATH: Path = DATA_DIR / "embeddings.db"

    # InsightFace model
    FACE_MODEL_NAME: str = "buffalo_l"
    DETECTION_THRESHOLD: float = 0.5
    RECOGNITION_THRESHOLD: float = 0.4   # 餘弦相似度

    # 活體偵測
    # EAR 閾值：< 此值視為閉眼。原始 paper 用 0.25 (Western faces)，
    # 亞洲人睜眼 EAR 常落 0.20-0.28 → 0.25 太高永遠 trigger 不到。
    # 0.22 對 Asian / 一般 webcam 較合理；可依個人臉形 / 相機距離微調。
    LIVENESS_BLINK_THRESHOLD: float = 0.22
    LIVENESS_REQUIRED_BLINKS: int = 2

    # 推論裝置 — True 試 CUDA 失敗自動 fallback CPU；要實際跑 GPU 需先裝
    # CUDA Toolkit 11.7+ 與 cuDNN 8.x（onnxruntime-gpu 不內建這兩個）
    USE_GPU: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000


settings = Settings()

settings.DATA_DIR.mkdir(exist_ok=True)
settings.FACES_DIR.mkdir(exist_ok=True)
settings.MODELS_DIR.mkdir(exist_ok=True)
