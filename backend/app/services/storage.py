"""
File storage service using unified storage abstraction.

This service provides backward-compatible file operations while using
the new FileStorageInterface for seamless local and S3 support.
"""

from fastapi import UploadFile
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from app.core.file_storage import get_file_storage


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

    # Generate unique filename with timestamp
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"{uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if file_extension:
        filename = f"{filename}.{file_extension}"

    # Read file content
    file_content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Get storage backend and save
    storage = get_file_storage()
    file_identifier = await storage.save_file(file_content, filename, content_type)

    return file_identifier


async def save_file_from_path(filepath: str, filename: str | None = None) -> str:
    """
    Save a file from a local path to configured storage backend.
    
    This is useful for uploading preprocessed images to S3 after OCR processing.

    Args:
        filepath: Path to the local file to upload
        filename: Optional custom filename, otherwise uses the original filename

    Returns:
        Storage identifier (path or key) for the saved file

    Raises:
        ValueError: If file cannot be saved or doesn't exist
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(filepath)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Use provided filename or generate one from the original
    if filename is None:
        # Generate unique filename with timestamp
        file_extension = file_path.suffix
        filename = f"{uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
    
    # Read file content
    with open(filepath, "rb") as f:
        file_content = f.read()
    
    # Determine content type based on extension
    content_type = "application/octet-stream"
    if filepath.lower().endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif filepath.lower().endswith(".png"):
        content_type = "image/png"
    elif filepath.lower().endswith(".pdf"):
        content_type = "application/pdf"
    elif filepath.lower().endswith((".tiff", ".tif")):
        content_type = "image/tiff"
    
    # Get storage backend and save
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


def get_local_path(file_identifier: str):
    """
    Get a context manager for local file path access.

    For local storage, returns the actual path.
    For S3, downloads to temporary file and cleans up after use.

    Args:
        file_identifier: Storage identifier returned by save_file

    Returns:
        Context manager that yields a local file path

    Example:
        with get_local_path(file_id) as path:
            text = extract_text(path)
    """
    storage = get_file_storage()
    return storage.get_local_path(file_identifier)
