DISEASE_TIPS = {
    "Healthy": [
        "Regularly monitor soil moisture and water when the top inch is dry.",
        "Ensure the plant gets adequate sunlight based on its specific crop type.",
        "Inspect leaves weekly for signs of pests or nutritional deficiencies."
    ],
    "Early Blight": [
        "Prune and destroy infected lower leaves immediately to prevent upward spread.",
        "Water at the base of the plant to keep the leaves dry.",
        "Apply mulch around the base to prevent soil splashing onto foliage."
    ],
    "Late Blight": [
        "Promptly harvest healthy portions and discard heavily infected plants.",
        "Improve air circulation by spacing plants appropriately.",
        "Avoid overhead watering and apply copper-based fungicides if wet weather persists."
    ],
    "Bacterial Spot": [
        "Avoid overhead irrigation; water using drip lines or soil-level hoses.",
        "Remove crop debris at the end of the season and practice crop rotation.",
        "Treat with copper-containing bactericides early in the disease cycle."
    ]
}

def get_care_tips(disease: str, severity: str) -> list:
    """
    Returns a list of care tips for the diagnosed disease.
    If severity is 'Severe', appends a critical warning recommendation.
    """
    tips = DISEASE_TIPS.get(disease, [
        "Monitor the plant condition regularly.",
        "Ensure adequate water and nutrients."
    ]).copy()
    
    if severity.upper() == "SEVERE":
        tips.append("CRITICAL: Severity level is Severe. Please consult a local agriculture expert immediately.")
        
    return tips
