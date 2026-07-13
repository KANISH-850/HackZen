import asyncio
import time
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
from .db import crud
from .db.database import engine, async_session
from .db.models import Base
from .models.model_manager import model_manager
from .api.routes import router as api_router

detector = Detector()
pose_estimator = PoseEstimator()
tracker = Tracker()
anomaly_model = AnomalyModel(settings.ANOMALY_MODEL_PATH)
risk_predictor = RiskPredictor(settings.RISK_PREDICTOR_MODEL_PATH)

zone_manager = ZoneManager()
alert_manager = AlertManager()

# Risk scores are computed every frame (~10Hz), but persisting every single
# reading would flood the DB with a near-continuous stream of near-identical
# rows. Throttle DB writes per worker instead — the live websocket stream
# still carries every frame's score for the dashboard.
RISK_LOG_INTERVAL_SECONDS = 5
_last_risk_log_time = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load YOLO models
    model_manager.load_models()

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Restore any zones persisted from a previous run
    camera_urls = settings.RTSP_URLS.split(",")
    async with async_session() as db:
        for i in range(len(camera_urls)):
            camera_id = i
            await crud.get_or_create_camera(db, camera_id)
            zones = await crud.get_zones_for_camera(db, camera_id)
            if zones:
                zone_manager.set_zones(camera_id, [
                    {"name": z.name, "polygon": z.polygon, "risk_level": z.risk_level} for z in zones
                ])

    # Startup: Start background video ingestion tasks
    for i, url in enumerate(camera_urls):
        camera_id = str(i) # Use index as camera_id for demo
        asyncio.create_task(start_ingestion(camera_id, url.strip()))

    # Start the inference loop
    asyncio.create_task(inference_loop(camera_urls))
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

app.include_router(api_router)

# Mount Socket.IO app
app.mount("/ws", sio_app)

async def process_camera(camera_id: str):
    buffer = get_buffer(camera_id)
    frame = buffer.get_latest()
    if frame is None:
        return

    # Model inference is CPU/GPU-bound and synchronous; running it inline on the
    # asyncio event loop would stall every other coroutine (websocket I/O, other
    # cameras, incoming HTTP requests) for the duration of each frame. Offload it
    # to a worker thread instead.
    detections = await asyncio.to_thread(detector.predict, frame)
    tracked = tracker.update(detections)
    poses = await asyncio.to_thread(pose_estimator.estimate, frame, [d["bbox"] for d in tracked])

    zone_violations = zone_manager.check_zone_violations(int(camera_id), tracked)

    for idx, det in enumerate(tracked):
        features = extract_features([det], [poses[idx]], frame_shape=frame.shape)
        anomaly_score = anomaly_model.score(features)
        trend = risk_predictor.predict_trajectory(features)

        person_zone_risk = "SAFE"
        for zv in zone_violations:
            if zv["track_id"] == det.get("track_id"):
                person_zone_risk = zv["risk_level"]
                break

        risk_score = compute_risk_score(det.get("ppe", {}), person_zone_risk, anomaly_score, trend)
        det["risk_score"] = risk_score

        worker_id = det.get("track_id", 0)
        now = time.time()
        if now - _last_risk_log_time.get(worker_id, 0) >= RISK_LOG_INTERVAL_SECONDS:
            _last_risk_log_time[worker_id] = now
            async with async_session() as db:
                await crud.get_or_create_worker(db, worker_id)
                await crud.log_risk_score(db, worker_id, risk_score)

        await alert_manager.evaluate_risk(
            int(camera_id),
            worker_id,
            risk_score,
            details={"ppe": det.get("ppe"), "zone": person_zone_risk},
        )

    _, encoded_img = await asyncio.to_thread(cv2.imencode, '.jpg', frame)
    b64_frame = base64.b64encode(encoded_img).decode('utf-8')

    frame_data = {
        "camera_id": camera_id,
        "frame": b64_frame,
        "detections": tracked,
        "poses": poses,
    }
    await sio.emit("live_frame", frame_data)


async def inference_loop(camera_urls: list):
    """
    Main loop processing frames, running models, and emitting WS events.
    Cameras are processed concurrently so a slow/stalled one can't starve the rest.
    """
    while True:
        camera_ids = [str(i) for i in range(len(camera_urls))]
        results = await asyncio.gather(
            *(process_camera(cid) for cid in camera_ids), return_exceptions=True
        )
        # A failure on one camera must not stop the others from being processed
        # on subsequent iterations.
        for cid, result in zip(camera_ids, results):
            if isinstance(result, Exception):
                print(f"⚠ Error processing camera {cid}: {result}")

        await asyncio.sleep(0.1) # Limit loop rate to ~10 FPS processing

@app.get("/")
def read_root():
    return {"status": "ok"}
