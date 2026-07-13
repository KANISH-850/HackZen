import os
import pickle


class AnomalyModel:
    """
    Loads a real scikit-learn IsolationForest (or similar) pickled at model_path,
    trained via training/anomaly_model/train_isolation_forest.py. If no trained
    model file is present, scoring is explicitly unavailable (returns None)
    rather than fabricating a score.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        if model_path and os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
            except Exception as e:
                print(f"⚠ Warning: failed to load anomaly model at {model_path}: {e}")

    def is_loaded(self) -> bool:
        return self.model is not None

    def score(self, features: list):
        """
        Returns an anomaly score in [0, 1], or None if no trained model is loaded.
        """
        if self.model is None:
            return None
        # IsolationForest.decision_function: higher = more normal. Invert/clip to [0,1].
        raw = self.model.decision_function([features])[0]
        return float(min(1.0, max(0.0, 0.5 - raw)))
