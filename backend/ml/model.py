import os
import random
from PIL import Image

# Supported classes in PRD
CLASSES = ["Healthy", "Early Blight", "Late Blight", "Bacterial Spot"]

TENSORFLOW_AVAILABLE = False
model = None

try:
    import tensorflow as tf
    import numpy as np
    TENSORFLOW_AVAILABLE = True
except ImportError:
    pass

MODEL_PATH = os.path.join(os.path.dirname(__file__), "plant_disease_model.h5")

if TENSORFLOW_AVAILABLE and os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("TensorFlow CNN model loaded successfully from:", MODEL_PATH)
    except Exception as e:
        print("Failed to load Keras model. Falling back to Mock Predictor. Error:", e)
        model = None
else:
    print("plant_disease_model.h5 not found or TensorFlow not installed. Using Mock Predictor.")

def predict_disease(image: Image.Image) -> tuple:
    """
    Performs inference on the processed leaf image.
    Uses real model prediction if loaded; otherwise returns mocked results.
    
    Returns:
        (disease: str, confidence: float, severity: str)
    """
    if model is not None:
        try:
            import numpy as np
            # Convert image to float numpy array, normalize, and add batch dimension (1, 224, 224, 3)
            img_arr = np.array(image) / 255.0
            img_arr = np.expand_dims(img_arr, axis=0)
            
            predictions = model.predict(img_arr)
            class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][class_idx])
            predicted_class = CLASSES[class_idx]
            
            if predicted_class == "Healthy":
                severity = "Mild"
            else:
                severity = random.choice(["Mild", "Moderate", "Severe"])
                
            return predicted_class, confidence, severity
        except Exception as e:
            print("Error during CNN model inference. Falling back to mock. Error:", e)

    # Fallback/Mock prediction logic
    predicted_class = random.choice(CLASSES)
    confidence = round(random.uniform(0.50, 0.99), 2)
    
    if predicted_class == "Healthy":
        severity = "Mild"
    else:
        severity = random.choice(["Mild", "Moderate", "Severe"])
        
    return predicted_class, confidence, severity
