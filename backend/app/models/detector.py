import numpy as np
from .model_manager import model_manager
from ..config import settings

class Detector:
    def __init__(self, model_path: str):
        self.model_path = model_path
    
    def predict(self, frame: np.ndarray):
        results = []
        
        # We try to use 'person' model and 'ppe' model if they exist
        person_results = model_manager.predict("person", frame, conf=settings.YOLO_CONFIDENCE)
        ppe_results = model_manager.predict("ppe", frame, conf=settings.YOLO_CONFIDENCE)
        
        # If no YOLO models are loaded, fallback to mock to prevent crash
        if person_results is None and ppe_results is None:
            height, width = frame.shape[:2]
            x1, y1 = width // 4, height // 4
            x2, y2 = width * 3 // 4, height * 3 // 4
            return [{"bbox": [x1, y1, x2, y2], "confidence": 0.88, "class": "person", "ppe": {"helmet": True, "vest": False}}]
            
        # Process person detections
        if person_results:
            for r in person_results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = model_manager.get_class_names("person").get(cls_id, "person")
                    
                    ppe_flags = {"helmet": False, "vest": False}
                    # Simplified logic: if PPE model detects helmet/vest within this person bbox
                    if ppe_results:
                        for ppe_r in ppe_results:
                            for pbox in ppe_r.boxes:
                                px1, py1, px2, py2 = pbox.xyxy[0].tolist()
                                p_cls_id = int(pbox.cls[0])
                                p_class_name = model_manager.get_class_names("ppe").get(p_cls_id, "ppe")
                                
                                # Check if PPE bbox is inside person bbox
                                if px1 >= x1 and py1 >= y1 and px2 <= x2 and py2 <= y2:
                                    if "helmet" in p_class_name.lower():
                                        ppe_flags["helmet"] = True
                                    elif "vest" in p_class_name.lower():
                                        ppe_flags["vest"] = True
                                        
                    results.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf,
                        "class": class_name,
                        "ppe": ppe_flags
                    })
        return results
