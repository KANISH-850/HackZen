# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy.future import select
from . import models

async def get_worker(db: AsyncSession, worker_id: int):
    result = await db.execute(select(models.Worker).where(models.Worker.id == worker_id))
    return result.scalars().first()

async def get_cameras(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Camera).offset(skip).limit(limit))
    return result.scalars().all()

async def get_zones_for_camera(db: AsyncSession, camera_id: int):
    result = await db.execute(select(models.Zone).where(models.Zone.camera_id == camera_id))
    return result.scalars().all()

async def create_incident(db: AsyncSession, incident_data: dict):
    db_incident = models.Incident(**incident_data)
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    return db_incident

async def log_risk_score(db: AsyncSession, worker_id: int, score: float):
    db_log = models.RiskLog(worker_id=worker_id, risk_score=score)
    db.add(db_log)
    await db.commit()
    return db_log
