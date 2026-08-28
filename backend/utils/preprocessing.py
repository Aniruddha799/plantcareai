from io import BytesIO
from PIL import Image
from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_image_extension(filename: str):
    """Checks if the uploaded file has a valid image extension."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format .{ext}. Only JPG, JPEG, and PNG are allowed."
        )

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Validates, loads, and processes the raw image bytes:
    1. Converts image to RGB mode.
    2. Resizes it to 224x224 pixels.
    Returns the processed PIL Image object.
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        image = image.convert("RGB")
        image = image.resize((224, 224))
        return image
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format or corrupt image. Error: {str(e)}"
        )

def is_leaf_image(image: Image.Image) -> bool:
    """
    Analyzes the image color distribution to verify if it represents a plant leaf.
    Downsamples the image to a 32x32 grid and checks if at least 8% of the pixels
    have a green-dominant profile (characteristic of healthy foliage and crop leaves).
    Filters out pets, sky, buildings, faces, and other non-plant objects.
    """
    small_img = image.resize((32, 32))
    pixels = list(small_img.getdata())
    
    green_pixel_count = 0
    total_pixels = len(pixels)
    
    for r, g, b in pixels:
        # Check for green foliage color ranges:
        # 1. Green component must be reasonably bright (g > 35)
        # 2. Green must be significantly dominant over red (g > r + 12)
        # 3. Green must be significantly dominant over blue (g > b + 12)
        is_green_leaf = (g > 35) and (g > r + 12) and (g > b + 12)
        
        if is_green_leaf:
            green_pixel_count += 1
            
    percentage = (green_pixel_count / total_pixels) * 100
    return percentage >= 8.0
