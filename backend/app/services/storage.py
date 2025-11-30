"""
File storage service using unified storage abstraction.

This service provides backward-compatible file operations while using
the new FileStorageInterface for seamless local and S3 support.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.core.file_storage import LocalFileStorage, get_file_storage


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename with timestamp and UUID.

    Args:
        original_filename: Original filename to extract extension from

    Returns:
        Unique filename with format: {uuid}-{timestamp}.{extension}
    """
    file_extension = (
        original_filename.split(".")[-1] if "." in original_filename else ""
    )
    filename = f"{uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if file_extension:
        filename = f"{filename}.{file_extension}"
    return filename


def detect_content_type(filepath: str) -> str:
    """
    Detect MIME content type based on file extension.

    Args:
        filepath: Path to the file

    Returns:
        MIME content type string
    """
    filepath_lower = filepath.lower()
    if filepath_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif filepath_lower.endswith(".png"):
        return "image/png"
    elif filepath_lower.endswith(".pdf"):
        return "application/pdf"
    elif filepath_lower.endswith((".tiff", ".tif")):
        return "image/tiff"
    return "application/octet-stream"


async def save_file_locally(file: UploadFile) -> str:
    """
    Save an uploaded file to local storage for processing.

    This function always saves files locally, regardless of the global storage configuration.
    Useful for OCR processing where files need to be processed locally first.

    Args:
        file: The uploaded file

    Returns:
        Local file path for the saved file

    Raises:
        ValueError: If filename is empty or file cannot be saved
    """
    if not file.filename:
        raise ValueError("Filename cannot be empty")

    filename = generate_unique_filename(file.filename)

    file_content = await file.read()
    if not file_content:
        raise ValueError("Uploaded file is empty")

    content_type = file.content_type or "application/octet-stream"

    settings = get_settings()
    storage = LocalFileStorage(base_path=settings.local_storage_path)
    file_identifier = await storage.save_file(file_content, filename, content_type)

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
    content_type = file.content_type or "application/octet-stream"

    storage = get_file_storage()
    file_identifier = await storage.save_file(file_content, filename, content_type)

    return file_identifier


async def save_file_from_path(filepath: str, filename: str | None = None) -> str:
    """
    Save a file from a local path to configured storage backend.

    This is useful for uploading preprocessed images to S3 after OCR processing.

    Args:
        filepath: Path to the local file to upload
        filename: Optional custom filename, otherwise generates unique filename

    Returns:
        Storage identifier (path or key) for the saved file

    Raises:
        ValueError: If file cannot be saved or doesn't exist
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if filename is None:
        filename = generate_unique_filename(file_path.name)

    with open(filepath, "rb") as f:
        file_content = f.read()

    content_type = detect_content_type(filepath)

    storage = get_file_storage()
    file_identifier = await storage.save_file(file_content, filename, content_type)

    return file_identifier


async def retrieve_file(file_identifier: str) -> bytes:
    """
    Retrieve a file from storage.

    Args:
        file_identifier: Storage identifier returned by save_file

    Returns:
        File content as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be retrieved
    """
    storage = get_file_storage()
    return await storage.retrieve_file(file_identifier)


async def delete_file(file_identifier: str) -> bool:
    """
    Delete a file from storage.

    Args:
        file_identifier: Storage identifier returned by save_file

    Returns:
        True if deletion was successful, False otherwise
    """
    storage = get_file_storage()
    return await storage.delete_file(file_identifier)


async def file_exists(file_identifier: str) -> bool:
    """
    Check if a file exists in storage.

    Args:
        file_identifier: Storage identifier to check

    Returns:
        True if file exists, False otherwise
    """
    storage = get_file_storage()
    return await storage.file_exists(file_identifier)


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
