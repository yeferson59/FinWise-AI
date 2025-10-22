import shutil
import os
from fastapi import UploadFile
from app.config import get_settings


async def save_file(file: UploadFile) -> str:
    settings = get_settings()
    upload_dir = settings.local_storage_path

    os.makedirs(upload_dir, exist_ok=True)

    filename = file.filename
    if not filename:
        raise ValueError("Uploaded file must have a filename")

    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path
