import numpy as np

class AnomalyModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        # TODO: load pickle model
        
    def score(self, features: list):
        """
        Mock anomaly scoring.
        Returns a score between 0 and 1.
        """
        # Return random score for mock
        return np.random.uniform(0.0, 0.3)
