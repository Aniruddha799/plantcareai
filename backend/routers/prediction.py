import os
import json
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas, auth
from backend.utils.plant_id import parse_plant_id  # Shared utility — no more duplication
from backend.utils.preprocessing import validate_image_extension, preprocess_image, is_leaf_image, get_leaf_green_ratio
from backend.utils.recovery import calculate_recovery_trend
from backend.utils.disease_info import get_care_tips
from backend.ml.model import predict_disease

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def predict(
    plant_id: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    # 1. Verify plant exists and belongs to current farmer
    db_plant_id = parse_plant_id(plant_id)
    plant = db.query(models.Plant).filter(
        models.Plant.id == db_plant_id,
        models.Plant.farmer_id == current_farmer.id,
        models.Plant.is_active == True
    ).first()

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )

    # 2. Validate image extension
    validate_image_extension(image.filename)

    # 3. Read image bytes
    image_bytes = await image.read()

    # Enforce size constraints (max 5MB)
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds the 5MB limit."
        )

    # 4. Save image to upload directory
    timestamp = int(time.time())
    safe_filename = f"plant_{db_plant_id}_{timestamp}_{image.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename).replace("\\", "/")  # Unix formatting
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    # 5. Preprocess the image
    preprocessed_img = preprocess_image(image_bytes)

    # 6. Verify that the image contains a plant leaf using multi-factor vegetation detector.
    #    This check actively rejects animals, humans, sky, and non-plant objects.
    if not is_leaf_image(preprocessed_img):
        # Remove the saved file since it's not a valid leaf image
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid Image: The uploaded photo does not appear to be a plant leaf. "
                "Please upload a clear, close-up photo of your crop leaf. "
                "Make sure the leaf fills most of the frame."
            )
        )

    # 7. ML Model Prediction
    disease, confidence, severity = predict_disease(preprocessed_img)

    # 7b. Double-check: even if the sklearn model produced a result, verify the image
    #     actually has meaningful plant-green pixels. This catches cases where the
    #     trained model's HSV features accidentally match non-plant images (animals, soil).
    green_ratio = get_leaf_green_ratio(preprocessed_img)
    if green_ratio < 0.10:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid Image: The uploaded photo does not appear to be a plant leaf. "
                "Please upload a clear, close-up photo of your crop leaf. "
                "Make sure the leaf fills most of the frame."
            )
        )

    # 8. Recovery trend calculation (must query prior to saving the report)
    severity_score, trend = calculate_recovery_trend(db, db_plant_id, disease, severity)

    # 9. Fetch Care Tips
    tips = get_care_tips(disease, severity)

    # 10. Save Disease Report
    disease_report = models.DiseaseReport(
        plant_id=db_plant_id,
        image_path=file_path,
        disease=disease,
        severity=severity,
        confidence=confidence,
        tips=json.dumps(tips)
    )
    db.add(disease_report)
    db.commit()
    db.refresh(disease_report)

    # 11. Save Recovery Record
    recovery_record = models.RecoveryRecord(
        plant_id=db_plant_id,
        report_id=disease_report.id,
        severity_score=severity_score,
        trend=trend
    )
    db.add(recovery_record)
    db.commit()

    # 12. Return JSON response
    return {
        "report_id": disease_report.id,
        "disease": disease,
        "severity": severity,
        "confidence": confidence,
        "trend": trend,
        "tips": tips
    }
