def _iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_area = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


class Tracker:
    """
    Real IOU-based multi-object tracker with greedy best-match assignment.
    Persists a track across frames while it keeps matching within
    iou_threshold, tolerates brief occlusion for max_age frames before
    dropping the ID, and hands out a fresh ID per genuinely new object
    (no ID reuse while a track is still alive).
    """

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 10):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.next_id = 1
        # track_id -> {"bbox": [...], "age": int, "class": str}
        self.tracks = {}

    def update(self, detections: list):
        unmatched_dets = list(range(len(detections)))
        unmatched_tracks = list(self.tracks.keys())

        # Build all (iou, track_id, det_idx) candidate pairs above threshold,
        # then greedily assign highest-IOU pairs first (stable under crowding).
        candidates = []
        for track_id in unmatched_tracks:
            track_bbox = self.tracks[track_id]["bbox"]
            for det_idx in unmatched_dets:
                iou = _iou(track_bbox, detections[det_idx]["bbox"])
                if iou >= self.iou_threshold:
                    candidates.append((iou, track_id, det_idx))
        candidates.sort(key=lambda c: c[0], reverse=True)

        matched_tracks, matched_dets = set(), set()
        for iou, track_id, det_idx in candidates:
            if track_id in matched_tracks or det_idx in matched_dets:
                continue
            matched_tracks.add(track_id)
            matched_dets.add(det_idx)
            detections[det_idx]["track_id"] = track_id
            self.tracks[track_id] = {
                "bbox": detections[det_idx]["bbox"],
                "age": 0,
                "class": detections[det_idx].get("class"),
            }

        # Age out tracks that weren't matched this frame; drop if stale too long.
        for track_id in unmatched_tracks:
            if track_id in matched_tracks:
                continue
            self.tracks[track_id]["age"] += 1
            if self.tracks[track_id]["age"] > self.max_age:
                del self.tracks[track_id]

        # Any detection left unmatched is a new object: assign a fresh ID.
        for det_idx in range(len(detections)):
            if det_idx in matched_dets:
                continue
            track_id = self.next_id
            self.next_id += 1
            detections[det_idx]["track_id"] = track_id
            self.tracks[track_id] = {
                "bbox": detections[det_idx]["bbox"],
                "age": 0,
                "class": detections[det_idx].get("class"),
            }

        return detections
