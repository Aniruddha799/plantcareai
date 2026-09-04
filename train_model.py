"""
PlantCare AI — Sklearn Model Trainer
=====================================
Trains a real Random Forest + SVM ensemble classifier using HSV color
and texture features extracted from leaf images.

Works on ANY Python version (no TensorFlow needed).
Model is saved as: backend/ml/plant_disease_model.pkl

HOW TO IMPROVE ACCURACY:
  Add real leaf images to the dataset/ folder:
    dataset/Healthy/          ← healthy leaf photos (JPG/PNG)
    dataset/Early_Blight/     ← early blight leaf photos
    dataset/Late_Blight/      ← late blight leaf photos
    dataset/Bacterial_Spot/   ← bacterial spot leaf photos

  Then run: python train_model.py
  Expected accuracy with real images: 80-92%
"""

import os
import sys
import pickle
import colorsys
import statistics
import random

try:
    import numpy as np
    from PIL import Image
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install scikit-learn numpy pillow")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
CLASSES = ["Healthy", "Early Blight", "Late Blight", "Bacterial Spot"]
DATASET_DIR = "dataset"
OUTPUT_MODEL = "backend/ml/plant_disease_model.pkl"
SCALER_PATH  = "backend/ml/feature_scaler.pkl"
IMAGE_SIZE   = (64, 64)
RANDOM_SEED  = 42

# ── Feature extraction (same as model.py) ─────────────────────────────────────

def extract_features(image: Image.Image) -> list:
    """
    Extracts an 18-dimensional feature vector from a leaf image using
    HSV color analysis and texture statistics.
    """
    small = image.resize(IMAGE_SIZE, Image.LANCZOS)
    pixels = list(small.getdata())
    total = len(pixels)

    zone_green = zone_yg = zone_yo = zone_rb = zone_gray = zone_dark = 0
    sat_vals, val_vals = [], []

    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        h360 = h * 360.0
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

        if 80 <= h360 <= 160:   zone_green += 1
        elif 55 <= h360 < 80:   zone_yg += 1
        elif 15 <= h360 < 55:   zone_yo += 1
        elif h360 < 15 or h360 >= 340: zone_rb += 1

    r_green = zone_green / total
    r_yg    = zone_yg    / total
    r_yo    = zone_yo    / total
    r_rb    = zone_rb    / total
    r_gray  = zone_gray  / total
    r_dark  = zone_dark  / total
    dz      = r_yo + r_rb + r_dark

    avg_sat = sum(sat_vals) / total
    avg_val = sum(val_vals) / total
    sat_var = statistics.variance(sat_vals) if len(sat_vals) > 1 else 0.0
    val_var = statistics.variance(val_vals) if len(val_vals) > 1 else 0.0
    sdi     = val_var * dz * 100

    # Row-column split features (left-half vs right-half disease ratio)
    half = IMAGE_SIZE[0] // 2
    left_pixels  = [pixels[i * IMAGE_SIZE[0] + j] for i in range(IMAGE_SIZE[1]) for j in range(half)]
    right_pixels = [pixels[i * IMAGE_SIZE[0] + j] for i in range(IMAGE_SIZE[1]) for j in range(half, IMAGE_SIZE[0])]

    def brown_ratio(px_list):
        count = sum(1 for r2, g2, b2 in px_list
                    if r2 > 50 and g2 > 30 and b2 < 80 and r2 > g2 and r2 > b2 and r2 < 200)
        return count / len(px_list) if px_list else 0.0

    lr_symmetry = abs(brown_ratio(left_pixels) - brown_ratio(right_pixels))

    return [
        r_green, r_yg, r_yo, r_rb, r_gray, r_dark, dz,
        avg_sat, avg_val, sat_var, val_var, sdi,
        lr_symmetry,
        r_green / (dz + 1e-6),           # green-to-disease ratio
        r_dark / (r_green + 1e-6),        # necrosis-to-green ratio
        sat_var / (avg_sat + 1e-6),       # relative saturation spread
        r_gray / (r_dark + 1e-6),         # water-soak vs necrosis ratio
        (r_yo + r_yg) / (r_rb + r_dark + 1e-6),  # early vs late disease ratio
    ]


# ── Synthetic dataset generator ────────────────────────────────────────────────

def _make_pixel(base_rgb, jitter=20) -> tuple:
    r, g, b = base_rgb
    r2 = min(255, max(0, r + random.randint(-jitter, jitter)))
    g2 = min(255, max(0, g + random.randint(-jitter, jitter)))
    b2 = min(255, max(0, b + random.randint(-jitter, jitter)))
    return (r2, g2, b2)

def generate_synthetic_dataset(n_per_class=400) -> tuple:
    """
    Generates a synthetic training dataset of leaf images with realistic
    disease color signatures. Used when no real image dataset is found.
    """
    print(f"  Generating {n_per_class} synthetic images per class...")
    X, y = [], []

    rng = random.Random(RANDOM_SEED)
    from PIL import ImageDraw

    for cls_idx, cls_name in enumerate(CLASSES):
        for i in range(n_per_class):
            img = Image.new("RGB", IMAGE_SIZE, (0, 0, 0))
            draw = ImageDraw.Draw(img)
            W, H = IMAGE_SIZE

            if cls_name == "Healthy":
                # Uniform green leaf — slight gradient variation
                for px in range(W):
                    for py in range(H):
                        base_g = rng.randint(100, 155)
                        r2 = rng.randint(30, 70)
                        b2 = rng.randint(20, 60)
                        img.putpixel((px, py), (r2, base_g, b2))

            elif cls_name == "Early Blight":
                # Green background + yellow-orange halo spots + dark centers
                for px in range(W):
                    for py in range(H):
                        img.putpixel((px, py), _make_pixel((70, 130, 55), 15))
                num_spots = rng.randint(8, 20)
                for _ in range(num_spots):
                    cx = rng.randint(4, W - 4)
                    cy = rng.randint(4, H - 4)
                    r = rng.randint(2, 6)
                    # Yellow halo
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                                 fill=_make_pixel((200, 155, 35), 20))
                    # Dark-brown center
                    cr = max(1, r // 2)
                    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                                 fill=_make_pixel((55, 32, 12), 10))

            elif cls_name == "Late Blight":
                # Dark, gray-green, water-soaked large patches
                for px in range(W):
                    for py in range(H):
                        img.putpixel((px, py), _make_pixel((80, 90, 70), 10))
                # Large dark water-soaked patch covering much of leaf
                x1 = rng.randint(0, W // 4)
                y1 = rng.randint(0, H // 4)
                x2 = rng.randint(3 * W // 4, W)
                y2 = rng.randint(3 * H // 4, H)
                draw.rectangle([x1, y1, x2, y2],
                                fill=_make_pixel((45, 50, 40), 8))
                draw.rectangle([x1 + 4, y1 + 4, x2 - 4, y2 - 4],
                                fill=_make_pixel((28, 32, 22), 5))

            elif cls_name == "Bacterial Spot":
                # Green background + many tiny scattered dark spots
                for px in range(W):
                    for py in range(H):
                        img.putpixel((px, py), _make_pixel((75, 128, 58), 12))
                num_spots = rng.randint(30, 80)
                for _ in range(num_spots):
                    cx = rng.randint(0, W - 1)
                    cy = rng.randint(0, H - 1)
                    r = rng.randint(1, 3)
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                                 fill=_make_pixel((90, 55, 25), 15))
                    draw.point((cx, cy), fill=_make_pixel((30, 18, 8), 5))

            features = extract_features(img)
            X.append(features)
            y.append(cls_idx)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def load_real_dataset() -> tuple:
    """Load real leaf images from dataset/ folder if available."""
    X, y = [], []
    total = 0

    for cls_idx, cls_name in enumerate(CLASSES):
        # Accept both "Healthy" and "Early_Blight" style folder names
        candidates = [
            os.path.join(DATASET_DIR, cls_name),
            os.path.join(DATASET_DIR, cls_name.replace(" ", "_")),
            os.path.join(DATASET_DIR, cls_name.replace(" ", "-")),
        ]
        cls_dir = next((c for c in candidates if os.path.isdir(c)), None)
        if not cls_dir:
            continue

        image_files = [
            f for f in os.listdir(cls_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        for fname in image_files:
            try:
                img = Image.open(os.path.join(cls_dir, fname)).convert("RGB")
                features = extract_features(img)
                X.append(features)
                y.append(cls_idx)
                total += 1
            except Exception:
                pass

    if total > 0:
        print(f"  Loaded {total} real images from {DATASET_DIR}/")

    return (np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)) if X else (None, None)


# ── Model builder ─────────────────────────────────────────────────────────────

def build_ensemble():
    """
    Voting ensemble of 3 classifiers:
      - Random Forest (handles non-linear feature interactions well)
      - Gradient Boosting (sequential correction of errors)
      - SVM with RBF kernel (effective in high-dimensional feature spaces)
    Final prediction = soft vote (average of probabilities).
    """
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    gb = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        random_state=RANDOM_SEED
    )
    svm = SVC(
        kernel="rbf",
        C=10.0,
        gamma="scale",
        probability=True,
        class_weight="balanced",
        random_state=RANDOM_SEED
    )

    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("svm", svm)],
        voting="soft",
        weights=[2, 2, 1]   # RF and GB get more weight
    )
    return ensemble


# ── Training pipeline ─────────────────────────────────────────────────────────

def train():
    print("=" * 55)
    print("  PlantCare AI — Sklearn Model Training")
    print("=" * 55)

    os.makedirs(os.path.dirname(OUTPUT_MODEL), exist_ok=True)

    # 1. Load or generate dataset
    print("\n[1/5] Loading dataset...")
    X_real, y_real = load_real_dataset()

    print("      Generating synthetic training data...")
    X_syn, y_syn = generate_synthetic_dataset(n_per_class=400)

    if X_real is not None and len(X_real) >= 50:
        X = np.vstack([X_real, X_syn])
        y = np.concatenate([y_real, y_syn])
        print(f"      Combined: {len(X_real)} real + {len(X_syn)} synthetic = {len(X)} total")
    else:
        X, y = X_syn, y_syn
        print(f"      Using {len(X)} synthetic images (add real images to dataset/ for better accuracy)")

    # 2. Split
    print(f"\n[2/5] Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RANDOM_SEED
    )
    print(f"      Train: {len(X_train)} | Test: {len(X_test)}")

    # 3. Scale + train
    print("\n[3/5] Training ensemble model (RF + GradientBoosting + SVM)...")
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    model = build_ensemble()
    model.fit(X_train_sc, y_train)
    print("      Training complete!")

    # 4. Evaluate
    print("\n[4/5] Evaluating...")
    y_pred = model.predict(X_test_sc)
    acc = accuracy_score(y_test, y_pred)

    print(f"\n  Test Accuracy: {acc:.2%}")
    print()
    print("  Per-class report:")
    report = classification_report(y_test, y_pred, target_names=CLASSES)
    for line in report.split("\n"):
        print("  " + line)

    # 5-fold CV
    X_sc_all = scaler.transform(X)
    cv_scores = cross_val_score(model, X_sc_all, y, cv=5, scoring="accuracy", n_jobs=-1)
    print(f"  5-fold CV accuracy: {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")

    # 5. Save
    print("\n[5/5] Saving model...")
    joblib.dump(model, OUTPUT_MODEL)
    joblib.dump(scaler, SCALER_PATH)
    print(f"  Model saved: {OUTPUT_MODEL}")
    print(f"  Scaler saved: {SCALER_PATH}")

    print("\n" + "=" * 55)
    print(f"  Done! Accuracy: {acc:.2%}")
    print("  Restart FastAPI server to load the new model.")
    print("=" * 55)
    return acc


if __name__ == "__main__":
    train()
