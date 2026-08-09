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
    Downsamples the image to a 32x32 grid and checks if at least 15% of the pixels
    are green, yellow, or brown.
    """
    small_img = image.resize((32, 32))
    pixels = list(small_img.getdata())
    
    leaf_pixel_count = 0
    total_pixels = len(pixels)
    
    for r, g, b in pixels:
        # Green healthy leaf colors
        is_green = (g > r) and (g > b) and (g > 30)
        
        # Yellow/Chlorosis diseased colors
        is_yellow = (r > 60 and g > 60 and b < r and b < g) and (abs(r - g) < 40)
        
        # Brown necrotic/spots colors
        is_brown = (r > 40 and g > 30 and b < g) and (r > b) and (r < 160)
        
        if is_green or is_yellow or is_brown:
            leaf_pixel_count += 1
            
    percentage = (leaf_pixel_count / total_pixels) * 100
    return percentage >= 15.0
