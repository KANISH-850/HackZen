def extract_features(detections: list, poses: list, frame_shape: tuple = None) -> list:
    """
    Converts a single detection + its pose into a fixed-size feature vector for
    the anomaly/risk-trend models:
        [bbox_aspect_ratio, bbox_area_ratio, avg_keypoint_confidence]
    - bbox_aspect_ratio (width/height): elevated for a fallen/prone person.
    - bbox_area_ratio: bbox area as a fraction of the frame, a proxy for
      camera proximity / crowding.
    - avg_keypoint_confidence: mean pose-keypoint confidence, low when the
      pose estimator is unsure (occlusion, motion blur, or unavailable).

    This vector's ordering/length is the contract with whatever anomaly/risk
    model is loaded (see training/anomaly_model/train_isolation_forest.py) —
    keep them in sync if the feature set changes.
    """
    if not detections or not detections[0]:
        return [0.0, 0.0, 0.0]

    det = detections[0]
    x1, y1, x2, y2 = det["bbox"]
    width, height = max(1e-6, x2 - x1), max(1e-6, y2 - y1)
    aspect_ratio = width / height

    if frame_shape:
        frame_h, frame_w = frame_shape[0], frame_shape[1]
        area_ratio = (width * height) / max(1e-6, frame_w * frame_h)
    else:
        area_ratio = 0.0

    pose = poses[0] if poses else []
    confidences = [kp[2] for kp in pose if len(kp) > 2]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return [aspect_ratio, area_ratio, avg_confidence]
