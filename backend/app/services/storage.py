import shutil
import os
from fastapi import UploadFile
from app.config import get_settings
from app.core.storage import s3_service
from uuid import uuid4
from datetime import datetime


async def save_file(file: UploadFile) -> str:
    settings = get_settings()
    if not file.filename:
        raise ValueError("Filename cannot be empty")

    filename = f"{uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"

    if settings.file_storage_type == "local":
        upload_dir = settings.local_storage_path

        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    elif settings.file_storage_type == "s3":
        file_content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        exists = await s3_service.upload_file(
            file_content=file_content, object_name=filename, content_type=content_type
        )
        if not exists:
            raise ValueError("Failed to upload file to S3")

        return filename

    else:
        raise ValueError(f"Unsupported file_storage_type: {settings.file_storage_type}")
