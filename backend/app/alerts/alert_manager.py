import time
from .notifier import notify_alert
from ..db import crud, database

class AlertManager:
    def __init__(self):
        # track last alert time per worker/camera to debounce
        self.last_alert_times = {}
        self.debounce_seconds = 10
        
    async def evaluate_risk(self, camera_id: int, worker_id: int, risk_score: float, details: dict):
        """
        Evaluates risk score and triggers alerts if above threshold.
        """
        from ..config import settings
        
        current_time = time.time()
        alert_key = f"{camera_id}_{worker_id}"
        
        severity = None
        if risk_score >= settings.RISK_THRESHOLD_CRITICAL:
            severity = "CRITICAL"
        elif risk_score >= settings.RISK_THRESHOLD_CAUTION:
            severity = "CAUTION"
            
        if severity:
            last_time = self.last_alert_times.get(alert_key, 0)
            if current_time - last_time > self.debounce_seconds:
                self.last_alert_times[alert_key] = current_time
                
                incident_data = {
                    "camera_id": camera_id,
                    "worker_id": worker_id,
                    "incident_type": "HIGH_RISK",
                    "severity": severity,
                    "details": details
                }
                
                # In real scenario, log to DB:
                # async for db in database.get_db():
                #     await crud.create_incident(db, incident_data)
                #     break
                    
                await notify_alert(incident_data)
