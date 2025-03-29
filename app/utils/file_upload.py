from fastapi import UploadFile, HTTPException
import os
from typing import Optional

ALLOWED_FILE_TYPES = ["pdf", "jpeg", "png", "jpg"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def save_uploaded_file(file: UploadFile, upload_dir: str = "uploads") -> Optional[str]:
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        # Validate file type
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )

        # Validate file size
        file.file.seek(0, 2)  # Move to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))