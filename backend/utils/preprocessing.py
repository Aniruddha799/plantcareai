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


def is_leaf_image(image: Image.Image) -> bool:
    """
    Validates if the image contains plant leaf / agricultural foliage.
    
    Filters out non-plant objects like human faces, indoor pets, clear blue sky,
    vehicles, and non-agricultural items, while accommodating real-world conditions
    (e.g., leaves held in hands, leaves on tables, shadows, or diseased yellow/brown foliage).
    """
    small_img = image.resize((64, 64))
    pixels = list(small_img.getdata())
    total_pixels = len(pixels)

    vegetation_count = 0
    human_face_skin_count = 0
    clear_sky_count = 0

    for r, g, b in pixels:
        # 1. Vegetation checks (healthy green, yellowing/chlorosis, brown blight necrosis)
        # Green foliage:
        is_green = (g > 35) and (g >= r - 5) and (g > b + 5)
        # Yellow foliage / chlorosis:
        is_yellow = (r > 70 and g > 70 and b < 90) and (abs(r - g) < 55) and (r > b + 15)
        # Brown blight / necrotic leaf tissue:
        is_brown_leaf = (r > 45 and g > 25 and b < 80) and (r > b) and (r < 210) and (g > b - 10)

        if is_green or is_yellow or is_brown_leaf:
            vegetation_count += 1
            continue

        # 2. Specific non-plant detectors:
        # High-confidence human face / flesh skin tone (peachy pink, high brightness)
        is_flesh = (
            r > 160 and g > 110 and b > 90 and
            r > g + 15 and g > b and
            (r - g) < 70 and (r - b) > 30
        )
        if is_flesh:
            human_face_skin_count += 1
            continue

        # Bright clear blue sky (not plant)
        is_sky = (b > 160 and b > r + 35 and b > g + 20)
        if is_sky:
            clear_sky_count += 1

    veg_ratio = vegetation_count / total_pixels
    face_ratio = human_face_skin_count / total_pixels
    sky_ratio = clear_sky_count / total_pixels

    # Rejection rules:
    # A. If dominant human face / skin (> 40% image is pink/peach flesh)
    if face_ratio > 0.40 and veg_ratio < 0.15:
        return False

    # B. If dominant clear blue sky (> 50% image is sky with minimal plant)
    if sky_ratio > 0.50 and veg_ratio < 0.10:
        return False

    # C. Minimum plant foliage presence: at least 7% of pixels must match plant leaf spectrum
    if veg_ratio < 0.07:
        return False

    return True
