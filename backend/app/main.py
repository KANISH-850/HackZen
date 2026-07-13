import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import cv2
import base64

from .config import settings
from .ws.socket_manager import sio_app, sio
from .streams.ingestion import start_ingestion
from .streams.frame_buffer import get_buffer
from .models.detector import Detector
from .models.pose_estimator import PoseEstimator
from .models.tracker import Tracker
from .models.anomaly_model import AnomalyModel
from .models.risk_predictor import RiskPredictor
from .engine.feature_extractor import extract_features
from .engine.zone_manager import ZoneManager
from .engine.risk_engine import compute_risk_score
from .alerts.alert_manager import AlertManager
from .db.database import engine
from .db.models import Base
from .models.model_manager import model_manager

# Init ML stubs
detector = Detector(settings.DETECTOR_MODEL_PATH)
pose_estimator = PoseEstimator(settings.POSE_ESTIMATOR_MODEL_PATH)
tracker = Tracker(settings.TRACKER_MODEL_PATH)
anomaly_model = AnomalyModel(settings.ANOMALY_MODEL_PATH)
risk_predictor = RiskPredictor(settings.RISK_PREDICTOR_MODEL_PATH)

zone_manager = ZoneManager()
alert_manager = AlertManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load YOLO models
    model_manager.load_models()

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Startup: Start background video ingestion tasks
    camera_ids = settings.RTSP_URLS.split(",")
    for i, url in enumerate(camera_ids):
        camera_id = str(i) # Use index as camera_id for demo
        asyncio.create_task(start_ingestion(camera_id, url.strip()))
        
    # Start the inference loop
    asyncio.create_task(inference_loop(camera_ids))
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO app
app.mount("/ws", sio_app)

async def inference_loop(camera_ids: list):
    """
    Main loop processing frames, running models, and emitting WS events.
    """
    while True:
        try:
            for i, url in enumerate(camera_ids):
                camera_id = str(i)
                buffer = get_buffer(camera_id)
                frame = buffer.get_latest()
                
                if frame is not None:
                    # 1. Detection
                    detections = detector.predict(frame)
                    
                    # 2. Tracking
                    tracked = tracker.update(detections)
                    
                    # 3. Pose
                    poses = pose_estimator.estimate(frame, [d["bbox"] for d in tracked])
                    
                    # 4. Zone checks
                    zone_violations = zone_manager.check_zone_violations(int(camera_id), tracked)
                    
                    # Process each tracked person for risk
                    for idx, det in enumerate(tracked):
                        # Mock features
                        features = extract_features([det], [poses[idx]])
                        anomaly_score = anomaly_model.score(features)
                        trend = risk_predictor.predict_trajectory(features)
                        
                        # Find zone risk for this person
                        person_zone_risk = "SAFE"
                        for zv in zone_violations:
                            if zv["track_id"] == det.get("track_id"):
                                person_zone_risk = zv["risk_level"]
                                break
                        
                        risk_score = compute_risk_score(det.get("ppe", {}), person_zone_risk, anomaly_score, trend)
                        
                        det["risk_score"] = risk_score
                        
                        # Trigger alert if needed
                        await alert_manager.evaluate_risk(
                            int(camera_id), 
                            det.get("track_id", 0), 
                            risk_score, 
                            details={"ppe": det.get("ppe"), "zone": person_zone_risk}
                        )

                    # Render to base64 for dashboard
                    _, encoded_img = cv2.imencode('.jpg', frame)
                    b64_frame = base64.b64encode(encoded_img).decode('utf-8')
                    
                    frame_data = {
                        "camera_id": camera_id,
                        "frame": b64_frame,
                        "detections": tracked,
                        "poses": poses
                    }
                    
                    # Broadcast frame with annotations
                    print(f"Broadcasting frame for camera {camera_id}")
                    await sio.emit("live_frame", frame_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
                
        await asyncio.sleep(0.1) # Limit loop rate to ~10 FPS processing

@app.get("/")
def read_root():
    return {"status": "ok"}
