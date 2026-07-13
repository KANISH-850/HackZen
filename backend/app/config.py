from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./unsafe_db.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Camera / Stream settings
    RTSP_URLS: str = "mock" # Comma separated for multiple cameras, '0' for local webcam
    FPS: int = 15
    
    # ML Models Paths
    DETECTOR_MODEL_PATH: str = "weights/detector.onnx"
    POSE_ESTIMATOR_MODEL_PATH: str = "weights/pose_estimator.onnx"
    TRACKER_MODEL_PATH: str = "weights/tracker.onnx"
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
