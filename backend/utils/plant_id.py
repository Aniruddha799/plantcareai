from fastapi import HTTPException, status


def parse_plant_id(plant_id_str: str) -> int:
    """
    Converts user-facing plant ID string (e.g. 'P001' or '1') to the internal
    database integer primary key.

    Accepts:
        - "P001" format (with leading P prefix)
        - Plain integer strings like "1"

    Returns:
        int: The internal database ID.

    Raises:
        HTTPException 400: If the format is invalid.
    """
    if plant_id_str.upper().startswith("P"):
        try:
            return int(plant_id_str[1:])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plant ID format. Expected format like P001."
            )
    try:
        return int(plant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plant ID format. Expected format like P001 or integer."
        )
