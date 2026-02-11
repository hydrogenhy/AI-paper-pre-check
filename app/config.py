import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))

os.makedirs(UPLOAD_DIR, exist_ok=True)
