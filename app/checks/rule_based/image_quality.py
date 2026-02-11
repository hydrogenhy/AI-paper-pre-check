from PIL import Image
import os


def get_image_dpi(image_path):
    """Extract DPI information from an image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (dpi_x, dpi_y) or (None, None) if not available
    """
    try:
        with Image.open(image_path) as im:
            dpi = im.info.get('dpi', None)
            if dpi:
                return dpi[0], dpi[1]
            return None, None
    except Exception:
        return None, None
    
def estimate_image_confidence(width: int, height: int) -> str:
    min_side = min(width, height)

    if min_side < 500:
        return "high"
    elif min_side < 800:
        return "medium"
    else:
        return "low"


def image_quality_check(path):
    """Scan directory for image files and assess resolution risk.

    Args:
        path: Directory path to scan

    Returns:
        Dict with:
        - check_type: "images"
        - results: list of image entries with filename, size, risk, confidence
    """
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp")
    results = []
    
    if not path:
        return {
            "check_type": "images",
            "results": [
                {
                    "note": "Path is None or empty"
                }
            ]
        }
    
    # Check if path exists and is a directory
    path_exists = os.path.exists(path)
    is_dir = os.path.isdir(path)
    
    if not is_dir:
        return {
            "check_type": "images",
            "results": [
                {
                    "note": f"Invalid directory path: {path} (exists: {path_exists}, isdir: {is_dir})"
                }
            ]
        }
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(root, file)
                
                try:
                    with Image.open(file_path) as im:
                        width, height = im.size
                    
                    results.append({
                        "filename": file,
                        "width × height": f"{width} × {height}",
                        "risk": "Image may be too low resolution for clear visibility in the paper." if estimate_image_confidence(width, height) == "high" else "Image resolution seems acceptable." if estimate_image_confidence(width, height) == "medium" else "Image resolution is likely sufficient.",
                        "confidence": estimate_image_confidence(width, height)
                    })
                except Exception as e:
                    results.append({
                        "filename": file,
                        "error": str(e)
                    })
    
    order = {"high": 0, "medium": 1, "low": 2, "unknown": 3,}
    results = sorted(results, key=lambda x: order.get(x["confidence"], 99))

    return {
        "check_type": "images",
        "results": results
        }
