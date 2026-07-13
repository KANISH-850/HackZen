import collections
import threading

class FrameBuffer:
    def __init__(self, max_size=30):
        self.buffer = collections.deque(maxlen=max_size)
        self.lock = threading.Lock()
        
    def push(self, frame):
        with self.lock:
            self.buffer.append(frame)
            
    def pop(self):
        with self.lock:
            if len(self.buffer) > 0:
                return self.buffer.popleft()
            return None
            
    def get_latest(self):
        with self.lock:
            if len(self.buffer) > 0:
                return self.buffer[-1]
            return None

# Global dictionary for multiple streams
buffers = {}
def get_buffer(camera_id: str) -> FrameBuffer:
    if camera_id not in buffers:
        buffers[camera_id] = FrameBuffer()
    return buffers[camera_id]
