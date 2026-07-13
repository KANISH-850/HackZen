# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy.future import select
from sqlalchemy import delete
from . import models

async def get_worker(db: AsyncSession, worker_id: int):
    result = await db.execute(select(models.Worker).where(models.Worker.id == worker_id))
    return result.scalars().first()

async def get_workers(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Worker).offset(skip).limit(limit))
    return result.scalars().all()

async def get_or_create_worker(db: AsyncSession, worker_id: int):
    """
    Auto-provisions a Worker row for a tracker track_id the first time it's
    seen. Tracker IDs have no name/role association yet, so this is a
    placeholder identity record, not fabricated data — it exists so
    worker_id foreign keys (incidents, risk logs) stay valid on Postgres,
    which enforces them (unlike SQLite by default).
    """
    result = await db.execute(select(models.Worker).where(models.Worker.id == worker_id))
    worker = result.scalars().first()
    if worker:
        return worker
    worker = models.Worker(id=worker_id, name=f"Worker {worker_id}", role="unknown")
    db.add(worker)
    await db.commit()
    await db.refresh(worker)
    return worker

async def get_cameras(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Camera).offset(skip).limit(limit))
    return result.scalars().all()

async def get_or_create_camera(db: AsyncSession, camera_id: int, name: str = None):
    result = await db.execute(select(models.Camera).where(models.Camera.id == camera_id))
    camera = result.scalars().first()
    if camera:
        return camera
    camera = models.Camera(id=camera_id, name=name or f"Camera {camera_id}")
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return camera

async def get_zones_for_camera(db: AsyncSession, camera_id: int):
    result = await db.execute(select(models.Zone).where(models.Zone.camera_id == camera_id))
    return result.scalars().all()

async def replace_zones_for_camera(db: AsyncSession, camera_id: int, zones_data: list):
    """
    zones_data: [{"name": str, "polygon": [{"x": int, "y": int}, ...], "risk_level": str}]
    """
    await db.execute(delete(models.Zone).where(models.Zone.camera_id == camera_id))
    created = []
    for z in zones_data:
        db_zone = models.Zone(
            camera_id=camera_id,
            name=z["name"],
            polygon=z["polygon"],
            risk_level=z.get("risk_level", "CAUTION"),
        )
        db.add(db_zone)
        created.append(db_zone)
    await db.commit()
    for z in created:
        await db.refresh(z)
    return created

async def create_incident(db: AsyncSession, incident_data: dict):
    db_incident = models.Incident(**incident_data)
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    return db_incident

async def get_incidents(db: AsyncSession, camera_id: int = None, skip: int = 0, limit: int = 100):
    query = select(models.Incident).order_by(models.Incident.timestamp.desc())
    if camera_id is not None:
        query = query.where(models.Incident.camera_id == camera_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def log_risk_score(db: AsyncSession, worker_id: int, score: float):
    db_log = models.RiskLog(worker_id=worker_id, risk_score=score)
    db.add(db_log)
    await db.commit()
    return db_log

async def get_risk_logs(db: AsyncSession, worker_id: int = None, skip: int = 0, limit: int = 200):
    query = select(models.RiskLog).order_by(models.RiskLog.timestamp.desc())
    if worker_id is not None:
        query = query.where(models.RiskLog.worker_id == worker_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()
