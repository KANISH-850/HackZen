import os

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class RiskPredictor:
    """
    Loads a real ONNX LSTM risk-trajectory model at model_path, trained via
    training/action_recognition or a dedicated risk-trend pipeline. If no model
    file is present (or onnxruntime isn't installed), trend prediction is
    explicitly unavailable (returns None) rather than fabricating a value.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session = None
        if ort is None:
            print("⚠ Warning: onnxruntime not installed. Risk trend prediction unavailable.")
        elif model_path and os.path.exists(model_path):
            try:
                self.session = ort.InferenceSession(model_path)
            except Exception as e:
                print(f"⚠ Warning: failed to load risk predictor at {model_path}: {e}")

    def is_loaded(self) -> bool:
        return self.session is not None

    def predict_trajectory(self, historical_features: list):
        """
        Returns a predicted risk trend in [0, 1], or None if unavailable.
        """
        if self.session is None:
            return None
        input_name = self.session.get_inputs()[0].name
        result = self.session.run(None, {input_name: [historical_features]})
        return float(min(1.0, max(0.0, result[0].flatten()[0])))
