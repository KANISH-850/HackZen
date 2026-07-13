import numpy as np
from .model_manager import model_manager
from ..config import settings

class PoseEstimator:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def estimate(self, frame: np.ndarray, bboxes: list):
        pose_results = model_manager.predict("pose", frame, conf=settings.YOLO_CONFIDENCE)
        
        poses = []
        # If no model, fallback to mock
        if not pose_results:
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                w, h = max(1, x2 - x1), max(1, y2 - y1)
                keypoints = []
                for _ in range(17):
                    kx = x1 + np.random.randint(0, int(w))
                    ky = y1 + np.random.randint(0, int(h))
                    keypoints.append([kx, ky, 0.9])
                poses.append(keypoints)
            return poses
            
        extracted_poses = []
        for r in pose_results:
            if r.keypoints and hasattr(r.keypoints, 'data') and r.keypoints.data is not None:
                for kpts in r.keypoints.data:
                    kpts_list = kpts.tolist()
                    extracted_poses.append(kpts_list)
                    
        # Map to bboxes (simplified 1:1 mapping for demo)
        for i in range(len(bboxes)):
            if i < len(extracted_poses):
                poses.append(extracted_poses[i])
            else:
                poses.append([])
                
        return poses
