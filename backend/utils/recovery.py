from sqlalchemy.orm import Session
from backend import models

SEVERITY_MAP = {
    "MILD": 1,
    "MODERATE": 2,
    "SEVERE": 3
}

def calculate_recovery_trend(
    db: Session,
    plant_id: int,
    current_disease: str,
    current_severity: str
) -> tuple:
    """
    Calculates the recovery trend by comparing with the plant's previous chronological report.
    This must be called BEFORE saving the current scan report to the database.
    
    Returns:
        (severity_score: int, trend: str)
    """
    current_score = SEVERITY_MAP.get(current_severity.upper(), 1)
    
    # Fetch the last saved report for this plant
    previous_report = db.query(models.DiseaseReport).filter(
        models.DiseaseReport.plant_id == plant_id
    ).order_by(
        models.DiseaseReport.created_at.desc(),
        models.DiseaseReport.id.desc()
    ).first()
    
    # If no scan exists, this is the Baseline scan
    if not previous_report:
        return current_score, "Baseline"
        
    # If the disease changed (e.g. from Bacterial Spot to Early Blight), reset trend to Baseline
    if previous_report.disease != current_disease:
        return current_score, "Baseline"
        
    # Retrieve score of previous report
    previous_score = SEVERITY_MAP.get(previous_report.severity.upper(), 1)
    
    # Compare scores
    if current_score < previous_score:
        trend = "Improving"
    elif current_score > previous_score:
        trend = "Worsening"
    else:
        trend = "Stable"
        
    return current_score, trend
