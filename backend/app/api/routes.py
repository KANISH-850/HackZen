from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import crud
from ..db.database import get_db

router = APIRouter(prefix="/api")


@router.get("/cameras")
async def list_cameras(db: AsyncSession = Depends(get_db)):
    cameras = await crud.get_cameras(db)
    return [{"id": c.id, "name": c.name, "rtsp_url": c.rtsp_url, "location": c.location} for c in cameras]


@router.get("/workers")
async def list_workers(db: AsyncSession = Depends(get_db)):
    workers = await crud.get_workers(db)
    return [{"id": w.id, "name": w.name, "role": w.role} for w in workers]


@router.get("/zones/{camera_id}")
async def get_zones(camera_id: int, db: AsyncSession = Depends(get_db)):
    zones = await crud.get_zones_for_camera(db, camera_id)
    return [{"id": z.id, "name": z.name, "polygon": z.polygon, "risk_level": z.risk_level} for z in zones]


@router.post("/zones/{camera_id}")
async def set_zones(camera_id: int, zones: list[dict], db: AsyncSession = Depends(get_db)):
    """
    Replaces all zones for a camera. Body: [{"name": str, "polygon": [{"x":.., "y":..}, ...], "risk_level": str}]
    Persists to DB and immediately updates the live in-memory ZoneManager used by the inference loop.
    """
    await crud.get_or_create_camera(db, camera_id)
    saved = await crud.replace_zones_for_camera(db, camera_id, zones)

    from ..main import zone_manager
    zone_manager.set_zones(camera_id, zones)

    return [{"id": z.id, "name": z.name, "polygon": z.polygon, "risk_level": z.risk_level} for z in saved]


@router.get("/incidents")
async def list_incidents(camera_id: int = None, limit: int = 100, db: AsyncSession = Depends(get_db)):
    incidents = await crud.get_incidents(db, camera_id=camera_id, limit=limit)
    return [
        {
            "id": i.id,
            "camera_id": i.camera_id,
            "worker_id": i.worker_id,
            "timestamp": i.timestamp.isoformat(),
            "incident_type": i.incident_type,
            "severity": i.severity,
            "details": i.details,
        }
        for i in incidents
    ]


@router.get("/risk_logs")
async def list_risk_logs(worker_id: int = None, limit: int = 200, db: AsyncSession = Depends(get_db)):
    logs = await crud.get_risk_logs(db, worker_id=worker_id, limit=limit)
    return [
        {"id": r.id, "worker_id": r.worker_id, "timestamp": r.timestamp.isoformat(), "risk_score": r.risk_score}
        for r in logs
    ]
