import numpy as np
from .model_manager import model_manager
from ..config import settings

PPE_CLASS_TO_FLAG = {
    "helmet": "helmet",
    "vest": "vest",
    "gloves": "gloves",
    "goggles": "goggles",
    "mask": "mask",
    "safety_shoe": "safety_shoe",
}


def _extract_boxes(results, model_key: str):
    boxes = []
    if not results:
        return boxes
    class_names = model_manager.get_class_names(model_key)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = class_names.get(cls_id, str(cls_id))
            boxes.append({"bbox": [x1, y1, x2, y2], "confidence": conf, "class": class_name})
    return boxes


class Detector:
    """
    Runs real YOLO inference for whichever roles have a loaded model
    (see settings.PERSON_MODEL_KEY / PPE_MODEL_KEY). No mock/random fallback:
    a role with no model loaded simply contributes nothing.
    """

    def __init__(self, model_path: str = None):
        pass

    def predict(self, frame: np.ndarray):
        person_loaded = model_manager.is_loaded(settings.PERSON_MODEL_KEY)
        ppe_results = model_manager.predict(settings.PPE_MODEL_KEY, frame, conf=settings.YOLO_CONFIDENCE)
        ppe_boxes = _extract_boxes(ppe_results, settings.PPE_MODEL_KEY)

        if not person_loaded:
            # No person model available yet: report the raw PPE-item detections
            # directly (real, not mocked) instead of a fabricated person box.
            results = []
            for item in ppe_boxes:
                results.append({
                    "bbox": item["bbox"],
                    "confidence": item["confidence"],
                    "class": item["class"],
                    "ppe": {},
                    "person_detection": "unavailable",
                })
            return results

        person_results = model_manager.predict(settings.PERSON_MODEL_KEY, frame, conf=settings.YOLO_CONFIDENCE)
        results = []
        for r in (person_results or []):
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])

                ppe_flags = {flag: False for flag in PPE_CLASS_TO_FLAG.values()}
                for item in ppe_boxes:
                    px1, py1, px2, py2 = item["bbox"]
                    # PPE item center falls within the person bbox
                    pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                    if x1 <= pcx <= x2 and y1 <= pcy <= y2:
                        flag = PPE_CLASS_TO_FLAG.get(item["class"].lower())
                        if flag:
                            ppe_flags[flag] = True

                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "class": "person",
                    "ppe": ppe_flags,
                })
        return results
