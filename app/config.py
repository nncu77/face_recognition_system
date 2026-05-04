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
    LIVENESS_BLINK_THRESHOLD: float = 0.25
    LIVENESS_REQUIRED_BLINKS: int = 2

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000


settings = Settings()

settings.DATA_DIR.mkdir(exist_ok=True)
settings.FACES_DIR.mkdir(exist_ok=True)
settings.MODELS_DIR.mkdir(exist_ok=True)
