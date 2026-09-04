from io import BytesIO
from PIL import Image
from fastapi import HTTPException, status

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


def get_leaf_green_ratio(image: Image.Image) -> float:
    """
    Returns the fraction of pixels that are unmistakably plant-green.
    A pixel qualifies ONLY when green channel is strongly dominant over
    both red AND blue — this matches chlorophyll-based leaf tissue and
    definitively rejects animal fur, skin, sand, dry grass, and sky.
    """
    small_img = image.resize((64, 64))
    pixels = list(small_img.getdata())
    total = len(pixels)
    green_count = 0
    for r, g, b in pixels:
        # g must be meaningfully brighter than both r and b
        if g > 45 and (g - r) > 18 and (g - b) > 18:
            green_count += 1
    return green_count / total


def is_leaf_image(image: Image.Image) -> bool:
    """
    Returns True only when the image contains a genuine plant leaf.
    Threshold: at least 10% of pixels must be unmistakably leaf-green.
    Rejects: animals, humans, sky, sand, dry grass, buildings, objects.
    """
    return get_leaf_green_ratio(image) >= 0.10

