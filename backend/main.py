import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.routers import auth, plants, prediction, reports

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
os.makedirs("backend/uploads", exist_ok=True)

app = FastAPI(
    title="PlantCare AI API",
    description="API for Plant Disease Detection & Recovery Tracking System",
    version="1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allowing all origins for development and demo ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static files directory
app.mount("/backend/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

# Mount frontend statically
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Register routers
app.include_router(auth.router)
app.include_router(plants.router)
app.include_router(prediction.router)
app.include_router(reports.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PlantCare AI API! Visit /docs for interactive Swagger API documentation."
    }
