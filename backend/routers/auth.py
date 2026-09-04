from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas, auth

router = APIRouter(
    tags=["Authentication"]
)

DEFAULT_STARTER_CROPS = [
    ("Tomato", "Roma Tomato - Field 1"),
    ("Potato", "Kufri Jyoti Potato - Bed A"),
    ("Chilli / Pepper", "Bell Pepper - Polyhouse"),
    ("Wheat", "Sharbati Wheat - Sector 2"),
    ("Cotton", "Cotton Crop - Plot 5"),
    ("Rice / Paddy", "Basmati Paddy - Field South"),
]


@router.post("/register", response_model=schemas.FarmerRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(farmer_in: schemas.FarmerRegister, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_farmer = db.query(models.Farmer).filter(models.Farmer.email == farmer_in.email).first()
    if existing_farmer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create farmer
    hashed_password = auth.get_password_hash(farmer_in.password)
    new_farmer = models.Farmer(
        name=farmer_in.name,
        email=farmer_in.email,
        password_hash=hashed_password,
        location=farmer_in.location
    )
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)

    # Automatically add starter crop profiles so the farmer can immediately scan leaves
    for crop_name, plant_name in DEFAULT_STARTER_CROPS:
        starter_plant = models.Plant(
            farmer_id=new_farmer.id,
            crop_name=crop_name,
            plant_name=plant_name
        )
        db.add(starter_plant)
    db.commit()

    return schemas.FarmerRegisterResponse(
        farmer_id=new_farmer.id,
        message="Registration successful"
    )


@router.post("/login", response_model=schemas.Token)
def login(login_in: schemas.FarmerLogin, db: Session = Depends(get_db)):
    farmer = db.query(models.Farmer).filter(models.Farmer.email == login_in.email).first()
    if not farmer or not auth.verify_password(login_in.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": farmer.email})
    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )
