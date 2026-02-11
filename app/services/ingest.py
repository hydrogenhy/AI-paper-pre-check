import os
from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE


def save_upload(file):
    filename = file.filename
    filename = filename.replace(" ", "_")
    dest_path = os.path.join(UPLOAD_DIR, filename)
    size = 0
    with open(dest_path, "wb") as f:
        while True:
            chunk = file.stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                f.close()
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
                raise ValueError("File too large")
            f.write(chunk)
    return dest_path, filename
