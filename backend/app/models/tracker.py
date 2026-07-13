class Tracker:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.next_id = 1
        
    def update(self, detections: list):
        """
        Mock tracker. Assigns a persistent ID for demo purposes.
        """
        tracked = []
        for det in detections:
            # Simple mock: assigning ID 1 always
            det["track_id"] = 1
            tracked.append(det)
        return tracked
