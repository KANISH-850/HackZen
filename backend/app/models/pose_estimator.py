import numpy as np
from .model_manager import model_manager
from ..config import settings


def _bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


class PoseEstimator:
    """
    Runs real Ultralytics pose inference when settings.POSE_MODEL_KEY is loaded.
    If no pose model is available, returns [] for every bbox (explicitly no
    pose data) instead of fabricating random keypoints.
    """

    def __init__(self, model_path: str = None):
        pass

    def estimate(self, frame: np.ndarray, bboxes: list):
        if not model_manager.is_loaded(settings.POSE_MODEL_KEY):
            return [[] for _ in bboxes]

        pose_results = model_manager.predict(settings.POSE_MODEL_KEY, frame, conf=settings.YOLO_CONFIDENCE)
        if not pose_results:
            return [[] for _ in bboxes]

        detected = []  # (center, keypoints)
        for r in pose_results:
            if r.keypoints is None or r.keypoints.data is None:
                continue
            for box, kpts in zip(r.boxes, r.keypoints.data):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected.append((_bbox_center([x1, y1, x2, y2]), kpts.tolist()))

        # Associate each requested bbox with the nearest detected pose (by center
        # distance) instead of a fragile positional 1:1 mapping.
        poses = []
        used = set()
        for bbox in bboxes:
            target = _bbox_center(bbox)
            best_idx, best_dist = None, None
            for i, (center, _) in enumerate(detected):
                if i in used:
                    continue
                dist = (center[0] - target[0]) ** 2 + (center[1] - target[1]) ** 2
                if best_dist is None or dist < best_dist:
                    best_idx, best_dist = i, dist
            if best_idx is not None:
                used.add(best_idx)
                poses.append(detected[best_idx][1])
            else:
                poses.append([])
        return poses
