from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from backend.database import get_db
from backend import models, schemas, auth
from backend.utils.plant_id import parse_plant_id  # Shared utility — no more duplication

router = APIRouter(
    tags=["Reports & Recovery"]
)


@router.get("/reports", response_model=List[schemas.ReportResponse])
def list_reports(
    plant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    """Lists all disease reports for the authenticated farmer, optionally filtered by plant_id."""
    # joinedload eagerly fetches recovery_record in the same SQL query,
    # so the trend field in ReportResponse is correctly populated (fixes lazy loading bug).
    query = (
        db.query(models.DiseaseReport)
        .join(models.Plant)
        .options(joinedload(models.DiseaseReport.recovery_record))
        .filter(
            models.Plant.farmer_id == current_farmer.id,
            models.Plant.is_active == True
        )
    )

    if plant_id:
        db_plant_id = parse_plant_id(plant_id)
        query = query.filter(models.DiseaseReport.plant_id == db_plant_id)

    return query.order_by(models.DiseaseReport.created_at.desc()).all()


@router.get("/reports/{report_id}", response_model=schemas.ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    """Retrieves detailed information for a single report."""
    # joinedload ensures recovery_record (and its trend) is fetched in one query
    report = (
        db.query(models.DiseaseReport)
        .join(models.Plant)
        .options(joinedload(models.DiseaseReport.recovery_record))
        .filter(
            models.DiseaseReport.id == report_id,
            models.Plant.farmer_id == current_farmer.id
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    return report


@router.get("/plants/{plant_id}/recovery", response_model=schemas.PlantRecoveryResponse)
def get_plant_recovery(
    plant_id: str,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    """
    Returns time-series recovery records for a specific plant,
    including severity scores and overall condition trends (Improving/Stable/Worsening/Baseline).
    """
    db_plant_id = parse_plant_id(plant_id)

    # 1. Verify plant exists, is active and belongs to farmer
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

    # 2. Get all recovery records for this plant chronologically.
    #    joinedload on report ensures rec.report.severity access doesn't trigger N+1 queries.
    records = (
        db.query(models.RecoveryRecord)
        .filter(models.RecoveryRecord.plant_id == db_plant_id)
        .options(joinedload(models.RecoveryRecord.report))
        .order_by(models.RecoveryRecord.created_at.asc())
        .all()
    )

    # 3. Form overall trend from the latest record
    overall_trend = "Baseline"
    if records:
        overall_trend = records[-1].trend

    # 4. Map DB records to Pydantic items
    history_items = []
    for rec in records:
        history_items.append(
            schemas.RecoveryHistoryItem(
                date=rec.created_at.strftime("%Y-%m-%d"),
                severity=rec.report.severity if rec.report else "Unknown",
                score=rec.severity_score
            )
        )

    return schemas.PlantRecoveryResponse(
        plant_id=f"P{db_plant_id:03d}",
        history=history_items,
        overall_trend=overall_trend
    )
