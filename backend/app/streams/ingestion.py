import cv2
import asyncio
import time
from .frame_buffer import get_buffer
from ..config import settings
import numpy as np

async def start_ingestion(camera_id: str, rtsp_url: str):
    """
    Background task to capture frames from RTSP/webcam and push to buffer.
    If source fails, generates a mock dummy frame.
    """
    buffer = get_buffer(camera_id)
    
    # Try parsing to int for webcam
    try:
        source = int(rtsp_url)
    except ValueError:
        source = rtsp_url
        
    cap = await asyncio.to_thread(cv2.VideoCapture, source)
    is_mock = False
    if not cap.isOpened():
        print(f"Failed to open video source: {rtsp_url}. Using mock dummy generator.")
        is_mock = True

    fps = settings.FPS
    frame_time = 1.0 / fps

    color = (0, 0, 0)
    while True:
        start_time = time.time()

        if not is_mock:
            # cap.read() blocks on I/O; run it off the event loop so it can't
            # stall websocket traffic or other cameras' ingestion tasks.
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                print(f"Lost video source: {rtsp_url}. Reconnecting in 1s...")
                await asyncio.sleep(1)
                cap = await asyncio.to_thread(cv2.VideoCapture, source)
                continue
        else:
            # Generate a 640x480 dummy frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = color
            # Change color slightly over time
            color = ((color[0] + 1) % 255, (color[1] + 2) % 255, (color[2] + 3) % 255)
            cv2.putText(frame, "MOCK CAMERA FEED", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        buffer.push(frame)
        
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_time - elapsed)
        await asyncio.sleep(sleep_time)
