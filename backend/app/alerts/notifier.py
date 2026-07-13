async def notify_alert(incident_data: dict):
    """
    Sends alerts via WebSocket broadcast (and stub for SMS/email)
    """
    from ..ws.socket_manager import sio
    
    # Broadcast to all connected clients on 'alert' channel
    await sio.emit("alert", incident_data)
    
    # Stub for SMS/Email
    print(f"STUB: Sending SMS/Email for Incident: {incident_data}")
