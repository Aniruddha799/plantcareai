from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend import models, schemas, auth
from backend.utils.plant_id import parse_plant_id  # Shared utility — no more duplication

router = APIRouter(
    prefix="/plants",
    tags=["Plants"]
)


@router.post("", response_model=schemas.PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(
    plant_in: schemas.PlantCreate,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    db_plant = models.Plant(
        farmer_id=current_farmer.id,
        crop_name=plant_in.crop_name,
        plant_name=plant_in.plant_name
    )
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant


@router.get("", response_model=List[schemas.PlantResponse])
def list_plants(
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    # Only return active (non-deleted) plants belonging to current farmer
    return db.query(models.Plant).filter(
        models.Plant.farmer_id == current_farmer.id,
        models.Plant.is_active == True
    ).all()


@router.get("/{plant_id}", response_model=schemas.PlantResponse)
def get_plant(
    plant_id: str,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    db_id = parse_plant_id(plant_id)
    plant = db.query(models.Plant).filter(
        models.Plant.id == db_id,
        models.Plant.farmer_id == current_farmer.id,
        models.Plant.is_active == True
    ).first()

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )
    return plant


@router.delete("/{plant_id}", status_code=status.HTTP_200_OK)
def delete_plant(
    plant_id: str,
    db: Session = Depends(get_db),
    current_farmer: models.Farmer = Depends(auth.get_current_farmer)
):
    db_id = parse_plant_id(plant_id)
    plant = db.query(models.Plant).filter(
        models.Plant.id == db_id,
        models.Plant.farmer_id == current_farmer.id,
        models.Plant.is_active == True
    ).first()

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )

    # Soft delete to preserve historical scan reports
    plant.is_active = False
    db.commit()
    return {"message": f"Plant {plant_id} soft-deleted successfully"}
