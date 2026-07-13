# pyrefly: ignore [missing-import]
import socketio
# pyrefly: ignore [missing-import]
import uvicorn
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
import threading
import time
import urllib.request

sio = socketio.AsyncServer(async_mode='asgi')
sio_app = socketio.ASGIApp(sio, socketio_path='ws/socket.io')

app = FastAPI()
app.mount("/ws", sio_app)

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

thread = threading.Thread(target=run_server, daemon=True)
thread.start()
time.sleep(1)

try:
    req = urllib.request.urlopen("http://127.0.0.1:8001/ws/socket.io/?EIO=4&transport=polling")
    print("Mounted status:", req.getcode())
    print("Mounted body:", req.read())
except Exception as e:
    print("Mounted error:", e)
