"""
PlantCare AI — Disease Prediction Engine
=========================================
Three prediction pathways (best available is used automatically):

1. SKLEARN ENSEMBLE (.pkl) — works on Python 3.14, no TensorFlow needed.
   Run 'python train_model.py' to generate plant_disease_model.pkl.

2. TENSORFLOW CNN (.h5) — requires Python <=3.12 + TensorFlow installed.
   See train_model.py comments for setup instructions.

3. ADVANCED MOCK PREDICTOR — HSV + texture rule-based fallback.
   Always available, no training needed.
"""

import os
import colorsys
import statistics
from PIL import Image

# Supported disease classes
CLASSES = ["Healthy", "Early Blight", "Late Blight", "Bacterial Spot"]

# ── Model state ───────────────────────────────────────────────────────────────
TENSORFLOW_AVAILABLE    = False
SKLEARN_MODEL_AVAILABLE = False
model          = None   # TensorFlow CNN model
sklearn_model  = None   # Sklearn ensemble model
sklearn_scaler = None

_ML_DIR       = os.path.dirname(__file__)
MODEL_PATH_H5  = os.path.join(_ML_DIR, "plant_disease_model.h5")
MODEL_PATH_PKL = os.path.join(_ML_DIR, "plant_disease_model.pkl")
SCALER_PATH    = os.path.join(_ML_DIR, "feature_scaler.pkl")

# ── Try loading sklearn model (Python 3.14 compatible) ───────────────────────
try:
    import joblib
    if os.path.exists(MODEL_PATH_PKL) and os.path.exists(SCALER_PATH):
        sklearn_model  = joblib.load(MODEL_PATH_PKL)
        sklearn_scaler = joblib.load(SCALER_PATH)
        SKLEARN_MODEL_AVAILABLE = True
        print("[PlantCare AI] Sklearn ensemble model loaded:", MODEL_PATH_PKL)
except Exception as _e:
    print(f"[PlantCare AI] Sklearn model load failed: {_e}")

# ── Try loading TensorFlow model (Python <=3.12 only) ────────────────────────
if not SKLEARN_MODEL_AVAILABLE:
    try:
        import tensorflow as tf
        import numpy as np
        TENSORFLOW_AVAILABLE = True
    except ImportError:
        pass

    if TENSORFLOW_AVAILABLE and os.path.exists(MODEL_PATH_H5):
        try:
            model = tf.keras.models.load_model(MODEL_PATH_H5)
            print("[PlantCare AI] TensorFlow CNN model loaded:", MODEL_PATH_H5)
        except Exception as _e:
            print(f"[PlantCare AI] TF model failed: {_e}. Using Mock Predictor.")
            model = None
    else:
        print("[PlantCare AI] No trained model found. Using Advanced Mock Predictor.")
        print("[PlantCare AI] Run 'python train_model.py' to train a real model.")


# ─────────────────────────────────────────────────────────────────────────────
# Helper: RGB → HSV
# ─────────────────────────────────────────────────────────────────────────────

def _rgb_to_hsv(r: int, g: int, b: int) -> tuple:
    """Convert 0-255 RGB to (H: 0-360°, S: 0-1, V: 0-1)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


# ─────────────────────────────────────────────────────────────────────────────
# Core feature extraction (shared by mock predictor and sklearn model)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_leaf_features(image: Image.Image) -> dict:
    """
    Extracts HSV color + texture features from a leaf image.

    Disease visual signatures:
      Healthy       → High green ratio (hue 80-160°), uniform, bright
      Early Blight  → Yellow-orange halos (hue 15-55°), high saturation variance
      Late Blight   → Gray/water-soaked tissue (low saturation), large dark patches
      Bacterial Spot → Many tiny dark spots, high spot-density index, high value variance
    """
    small = image.resize((64, 64), Image.LANCZOS)
    pixels = list(small.getdata())
    total = len(pixels)

    zone_green = zone_yg = zone_yo = zone_rb = zone_gray = zone_dark = 0
    sat_vals, val_vals = [], []

    for r, g, b in pixels:
        h, s, v = _rgb_to_hsv(r, g, b)
        sat_vals.append(s)
        val_vals.append(v)

        if v < 0.25:
            zone_dark += 1
            if s < 0.35:
                zone_gray += 1
            continue

        if s < 0.22:
            zone_gray += 1
            continue

        if 80 <= h <= 160:          zone_green += 1
        elif 55 <= h < 80:          zone_yg    += 1
        elif 15 <= h < 55:          zone_yo    += 1
        elif h < 15 or h >= 340:    zone_rb    += 1

    r_green = zone_green / total
    r_yg    = zone_yg    / total
    r_yo    = zone_yo    / total
    r_rb    = zone_rb    / total
    r_gray  = zone_gray  / total
    r_dark  = zone_dark  / total
    dz      = r_yo + r_rb + r_dark

    avg_sat = sum(sat_vals) / total
    avg_val = sum(val_vals) / total
    sat_var = statistics.variance(sat_vals) if total > 1 else 0.0
    val_var = statistics.variance(val_vals) if total > 1 else 0.0
    sdi     = val_var * dz * 100

    return {
        "r_green": r_green, "r_yellow_green": r_yg,
        "r_yellow_orange": r_yo, "r_red_brown": r_rb,
        "r_gray": r_gray, "r_dark": r_dark,
        "avg_sat": avg_sat, "avg_val": avg_val,
        "sat_variance": sat_var, "val_variance": val_var,
        "sdi": sdi, "disease_zone_ratio": dz,
    }


def _features_to_vector(f: dict) -> list:
    """Convert feature dict to the 18-element list used by the sklearn model."""
    return [
        f["r_green"], f["r_yellow_green"], f["r_yellow_orange"], f["r_red_brown"],
        f["r_gray"], f["r_dark"], f["disease_zone_ratio"],
        f["avg_sat"], f["avg_val"], f["sat_variance"], f["val_variance"], f["sdi"],
        0.0,  # lr_symmetry (placeholder for compatibility with training script)
        f["r_green"]         / (f["disease_zone_ratio"] + 1e-6),
        f["r_dark"]          / (f["r_green"]            + 1e-6),
        f["sat_variance"]    / (f["avg_sat"]             + 1e-6),
        f["r_gray"]          / (f["r_dark"]              + 1e-6),
        (f["r_yellow_orange"] + f["r_yellow_green"]) / (f["r_red_brown"] + f["r_dark"] + 1e-6),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Advanced mock classifier (rule-based, no training needed)
# ─────────────────────────────────────────────────────────────────────────────

def _classify_from_features(f: dict) -> tuple:
    """
    Weighted multi-class scoring classifier using HSV + texture features.
    Used only when no trained model is available.
    """
    r_green = f["r_green"]
    r_yg    = f["r_yellow_green"]
    r_yo    = f["r_yellow_orange"]
    r_rb    = f["r_red_brown"]
    r_gray  = f["r_gray"]
    r_dark  = f["r_dark"]
    avg_sat = f["avg_sat"]
    avg_val = f["avg_val"]
    sat_var = f["sat_variance"]
    val_var = f["val_variance"]
    sdi     = f["sdi"]
    dz      = f["disease_zone_ratio"]

    scores = {"Healthy": 0.0, "Early Blight": 0.0, "Late Blight": 0.0, "Bacterial Spot": 0.0}

    # Healthy signals
    scores["Healthy"] += r_green * 3.0
    scores["Healthy"] += r_yg * 0.3
    scores["Healthy"] -= dz * 6.0
    scores["Healthy"] -= r_dark * 4.0
    scores["Healthy"] -= sat_var * 4.0
    if avg_sat > 0.30 and avg_val > 0.35 and dz < 0.10:
        scores["Healthy"] += 0.5

    # Early Blight — yellow-orange halos + dark centres + high sat variance
    scores["Early Blight"] += r_yo * 4.0
    scores["Early Blight"] += r_rb * 2.0
    scores["Early Blight"] += sat_var * 9.0
    scores["Early Blight"] += r_dark * 1.5
    scores["Early Blight"] -= r_gray * 2.0
    if 0.04 < r_dark < 0.30 and r_yo > 0.06:
        scores["Early Blight"] += 0.8
    if dz > 0.15 and sat_var > 0.015:
        scores["Early Blight"] += 0.5

    # Late Blight — large gray/desaturated water-soaked patches
    scores["Late Blight"] += r_gray * 4.5
    scores["Late Blight"] += r_dark * 3.0
    scores["Late Blight"] -= sat_var * 3.0
    scores["Late Blight"] += r_rb * 1.2
    if avg_val < 0.45 and r_gray > 0.10:
        scores["Late Blight"] += 1.0
    if r_dark > 0.12:
        scores["Late Blight"] += 0.8

    # Bacterial Spot — many tiny scattered spots, high SDI + val variance
    scores["Bacterial Spot"] += sdi * 3.0
    scores["Bacterial Spot"] += val_var * 6.0
    scores["Bacterial Spot"] += r_rb * 2.5
    scores["Bacterial Spot"] += r_dark * 2.0
    if sdi > 0.2 and r_green > 0.15:
        scores["Bacterial Spot"] += 1.0
    if r_dark < 0.20 and val_var > 0.02 and dz > 0.08:
        scores["Bacterial Spot"] += 0.6

    best_class = max(scores, key=scores.get)
    best_score = scores[best_class]
    total_score = sum(max(s, 0) for s in scores.values()) or 1.0
    raw_conf    = best_score / total_score
    confidence  = round(min(0.96, max(0.55, 0.55 + raw_conf * 0.41)), 2)

    if best_class == "Healthy":
        severity = "None"
    elif f["r_dark"] > 0.20 or dz > 0.45:
        severity = "Severe"
    elif f["r_dark"] > 0.08 or dz > 0.22:
        severity = "Moderate"
    else:
        severity = "Mild"

    return best_class, confidence, severity


def _map_confidence_to_severity(confidence: float) -> str:
    if confidence >= 0.80:  return "Severe"
    elif confidence >= 0.60: return "Moderate"
    else:                   return "Mild"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def predict_disease(image: Image.Image) -> tuple:
    """
    Runs disease prediction using the best available model:
      1. Sklearn ensemble   (.pkl) — Python 3.14 compatible
      2. TensorFlow CNN     (.h5)  — Python <=3.12 only
      3. Advanced Mock              — always available fallback

    Returns: (disease: str, confidence: float, severity: str)
    """
    import numpy as np

    # ── Pathway 1: Sklearn ensemble ───────────────────────────────────────────
    if SKLEARN_MODEL_AVAILABLE and sklearn_model is not None:
        try:
            features = _extract_leaf_features(image)
            vec = np.array([_features_to_vector(features)], dtype=np.float32)
            scaled = sklearn_scaler.transform(vec)
            proba = sklearn_model.predict_proba(scaled)[0]
            class_idx  = int(np.argmax(proba))
            confidence = float(proba[class_idx])
            predicted  = CLASSES[class_idx]
            severity   = "None" if predicted == "Healthy" else _map_confidence_to_severity(confidence)
            return predicted, round(confidence, 2), severity
        except Exception as _e:
            print(f"[PlantCare AI] Sklearn error: {_e}. Falling back.")

    # ── Pathway 2: TensorFlow CNN ─────────────────────────────────────────────
    if model is not None:
        try:
            img_arr = np.array(image) / 255.0
            img_arr = np.expand_dims(img_arr, axis=0)
            predictions = model.predict(img_arr, verbose=0)
            class_idx  = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][class_idx])
            predicted  = CLASSES[class_idx]
            severity   = "None" if predicted == "Healthy" else _map_confidence_to_severity(confidence)
            return predicted, round(confidence, 2), severity
        except Exception as _e:
            print(f"[PlantCare AI] TF error: {_e}. Falling back.")

    # ── Pathway 3: Advanced Mock Predictor ────────────────────────────────────
    features = _extract_leaf_features(image)
    return _classify_from_features(features)
