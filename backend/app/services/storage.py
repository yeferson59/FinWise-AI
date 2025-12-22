from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.core.file_storage import LocalFileStorage, get_file_storage

mimeContentType = [
    (".jpg", "image/jpeg"),
    (".jpeg", "image/jpeg"),
    (".png", "image/png"),
    (".pdf", "application/pdf"),
    (".tiff", "image/tiff"),
    (".tif", "image/tiff"),
    (".webp", "image/webp"),
]


def generate_unique_filename(original_filename: str) -> str:
    file_extension = (
        original_filename.split(".")[-1] if "." in original_filename else ""
    )
    filename = f"{uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if file_extension:
        filename = f"{filename}.{file_extension}"

    return filename


def detect_content_type(filepath: str) -> str:
    filepath_lower = filepath.lower()

    for extension, content_type in mimeContentType:
        if filepath_lower.endswith(extension):
            return content_type

    return "application/octet-stream"


async def save_file_locally(file: UploadFile) -> str:
    if not file.filename:
        raise ValueError("Filename cannot be empty")

    filename = generate_unique_filename(file.filename)
    file_content = await file.read()

    if not file_content:
        raise ValueError("Uploaded file is empty")

    settings = get_settings()
    storage = LocalFileStorage(base_path=settings.local_storage_path)
    file_identifier = await storage.save_file(
        file_content, filename, file.content_type or "application/octet-stream"
    )

    return str(Path(file_identifier).resolve())


async def save_file(file: UploadFile) -> str:
    """
    Save an uploaded file to configured storage backend.

    Args:
        file: The uploaded file

    Returns:
        Storage identifier (path or key) for the saved file

    Raises:
        ValueError: If filename is empty or file cannot be saved
    """
    if not file.filename:
        raise ValueError("Filename cannot be empty")

    filename = generate_unique_filename(file.filename)
    file_content = await file.read()

    storage = get_file_storage()
    file_identifier = await storage.save_file(
        file_content=file_content,
        filename=filename,
        content_type=(file.content_type or "application/octet-stream"),
    )

    return file_identifier


async def save_file_from_path(filepath: str, filename: str) -> str:
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "rb") as f:
        file_content = f.read()

    content_type = detect_content_type(filepath)

    storage = get_file_storage()
    file_identifier = await storage.save_file(file_content, filename, content_type)

    return file_identifier


async def retrieve_file(file_identifier: str) -> bytes:
    storage = get_file_storage()
    data = await storage.retrieve_file(file_identifier)

    return data


async def delete_file(file_identifier: str) -> bool:
    storage = get_file_storage()
    is_deleted = await storage.delete_file(file_identifier)

    return is_deleted


async def file_exists(file_identifier: str) -> bool:
    storage = get_file_storage()
    exists = await storage.file_exists(file_identifier)

    return exists


@asynccontextmanager
async def get_local_path(file_identifier: str):
    """
    Async context manager that yields a local file path.

    For local storage, returns the actual path.
    For S3, downloads to a temporary file and cleans up after use.

    Args:
        file_identifier: Storage identifier returned by save_file

    Yields:
        Local file path as a string

    Example:
        async with get_local_path(file_id) as path:
            text = extract_text(path)
    """
    storage = get_file_storage()
    # Delegate to the storage backend's async context manager.
    # This ensures callers can always use `async with get_local_path(...)`.
    async with storage.get_local_path(file_identifier) as local_path:  # type: ignore[attr-defined, func-returns-value]
        yield local_path
