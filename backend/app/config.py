from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./unsafe_db.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Camera / Stream settings
    RTSP_URLS: str = "0" # Comma separated for multiple cameras, '0' for local webcam
    FPS: int = 15

    # YOLO .pt weights are auto-discovered from MODELS_DIR by filename (see model_manager.py).
    # Each setting below is the filename stem (no extension) of the weight file that plays
    # that role. Roles with no matching file simply stay unloaded (explicit "unavailable"
    # state) instead of being faked.
    MODELS_DIR: str = "models"
    PERSON_MODEL_KEY: str = "person"
    PPE_MODEL_KEY: str = "best"
    POSE_MODEL_KEY: str = "pose"

    # Anomaly / risk-trend models (pickle / onnx). Optional — if the file doesn't exist,
    # those subsystems report explicitly unavailable rather than inventing a value.
    ANOMALY_MODEL_PATH: str = "weights/anomaly_model.pkl"
    RISK_PREDICTOR_MODEL_PATH: str = "weights/risk_predictor.onnx"

    # YOLO Settings
    YOLO_CONFIDENCE: float = 0.5
    
    # Alerts thresholds
    RISK_THRESHOLD_CAUTION: float = 0.5
    RISK_THRESHOLD_CRITICAL: float = 0.8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
