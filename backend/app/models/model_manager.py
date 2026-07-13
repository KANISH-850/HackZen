import os
import glob
try:
    import torch
    from ultralytics import YOLO
except ImportError:
    torch = None
    YOLO = None

class ModelManager:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.models = {}
        self.class_names = {}
        self.device = "cuda:0" if torch and torch.cuda.is_available() else "cpu"
        
    def load_models(self):
        if not YOLO:
            print("⚠ Warning: ultralytics not installed. Cannot load YOLO models.")
            return

        search_path = os.path.join(self.models_dir, "*.pt")
        model_files = glob.glob(search_path)
        
        if not model_files:
            print(f"⚠ Warning: No .pt models found in {self.models_dir}")
            # Do not crash, just log warning
            
        for model_path in model_files:
            filename = os.path.basename(model_path)
            model_name = os.path.splitext(filename)[0]
            try:
                # Load the YOLO model
                model = YOLO(model_path)
                
                self.models[model_name] = model
                self.class_names[model_name] = model.names
                
                print(f"✓ Loaded {filename} on {self.device}")
            except Exception as e:
                print(f"⚠ Warning: Failed to load {filename}: {e}")
                
    def predict(self, model_name: str, frame, conf: float = 0.5):
        model = self.models.get(model_name)
        if not model:
            return None
            
        # Run inference using the selected device and threshold
        results = model.predict(source=frame, conf=conf, device=self.device, verbose=False)
        return results

model_manager = ModelManager(models_dir="models")
