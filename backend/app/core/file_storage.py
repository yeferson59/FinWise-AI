"""
File storage abstraction layer for local and S3-compatible storage.

This module provides a unified interface for file operations that works
seamlessly with both local filesystem and S3-compatible object storage.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import os
import tempfile
from contextlib import asynccontextmanager

import aioboto3
from botocore.client import Config

from app.config import get_settings


class FileStorageInterface(ABC):
    """
    Abstract base class for file storage backends.

    Provides a unified interface for saving and retrieving files
    regardless of the underlying storage mechanism.
    """

    @abstractmethod
    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Save a file to storage.

        Args:
            file_content: The file content as bytes
            filename: The name to save the file as
            content_type: MIME type of the file

        Returns:
            Storage identifier (path or key) for the saved file

        Raises:
            ValueError: If the file cannot be saved
        """
        pass

    @abstractmethod
    async def retrieve_file(self, file_identifier: str) -> bytes:
        """
        Retrieve a file from storage.

        Args:
            file_identifier: Storage identifier returned by save_file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be retrieved
        """
        pass

    @abstractmethod
    def get_local_path(self, file_identifier: str):  # type: ignore[func-returns-value]
        """
        Async context manager that provides a local file path for reading.

        For local storage, this returns the actual path.
        For S3 storage, this downloads to a temporary file.

        Args:
            file_identifier: Storage identifier returned by save_file

        Yields:
            Path to a local file that can be read

        Example:
            async with storage.get_local_path("file.pdf") as local_path:
                text = extract_text(local_path)

        Note: This method should be implemented as an async context manager.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_identifier: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_identifier: Storage identifier returned by save_file

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    async def file_exists(self, file_identifier: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_identifier: Storage identifier to check

        Returns:
            True if the file exists, False otherwise
        """
        pass


class LocalFileStorage(FileStorageInterface):
    """
    Local filesystem storage implementation.

    Stores files in a local directory structure.
    """

    def __init__(self, base_path: str = "uploads"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Save file to local filesystem."""
        file_path = self.base_path / filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            return str(file_path)
        except Exception as e:
            raise ValueError(f"Failed to save file to local storage: {str(e)}")

    async def retrieve_file(self, file_identifier: str) -> bytes:
        """Retrieve file from local filesystem."""
        file_path = Path(file_identifier)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_identifier}")

        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to retrieve file from local storage: {str(e)}")

    @asynccontextmanager
    async def get_local_path(self, file_identifier: str):
        """
        For local storage, just return the path directly.
        No cleanup needed since it's already local.
        """
        file_path = Path(file_identifier)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_identifier}")

        yield str(file_path)

    async def delete_file(self, file_identifier: str) -> bool:
        """Delete file from local filesystem."""
        try:
            file_path = Path(file_identifier)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def file_exists(self, file_identifier: str) -> bool:
        """Check if file exists in local filesystem."""
        return Path(file_identifier).exists()


class S3FileStorage(FileStorageInterface):
    """
    S3-compatible storage implementation.

    Works with AWS S3 and S3-compatible services (MinIO, Backblaze B2, etc.).
    """

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        signature_version: str = "s3v4",
    ):
        """
        Initialize S3 storage.

        Args:
            bucket_name: S3 bucket name
            access_key: AWS access key ID
            secret_key: AWS secret access key
            region: AWS region
            endpoint_url: Custom endpoint URL (for S3-compatible services)
            signature_version: Signature version for signing requests
        """
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url

        client_config: Config = Config(
            signature_version=signature_version, s3={"addressing_style": "path"}
        )

        self.client_params = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": client_config,
            "region_name": region,
        }

        if endpoint_url:
            self.client_params["endpoint_url"] = endpoint_url

        self.session: aioboto3.Session = aioboto3.Session()

    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Save file to S3."""
        try:
            async with self.session.client(**self.client_params) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=file_content,
                    ContentType=content_type,
                )
            return filename
        except Exception as e:
            raise ValueError(f"Failed to save file to S3: {str(e)}")

    async def retrieve_file(self, file_identifier: str) -> bytes:
        """Retrieve file from S3."""
        try:
            async with self.session.client(**self.client_params) as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name, Key=file_identifier
                )
                return await response["Body"].read()
        except Exception as e:
            raise ValueError(f"Failed to retrieve file from S3: {str(e)}")

    @asynccontextmanager
    async def get_local_path(self, file_identifier: str):
        """
        Download S3 file to a temporary location and provide path.
        Cleans up the temporary file after use.
        """

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file_identifier).suffix
        )
        temp_path = temp_file.name
        temp_file.close()

        try:
            # Download file from S3
            file_content = await self.retrieve_file(file_identifier)

            with open(temp_path, "wb") as f:
                f.write(file_content)

            yield temp_path
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass  # Best effort cleanup

    async def delete_file(self, file_identifier: str) -> bool:
        """Delete file from S3."""
        try:
            async with self.session.client(**self.client_params) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=file_identifier)
            return True
        except Exception:
            return False

    async def file_exists(self, file_identifier: str) -> bool:
        """Check if file exists in S3."""
        try:
            async with self.session.client(**self.client_params) as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=file_identifier)
            return True
        except Exception:
            return False


def get_file_storage() -> FileStorageInterface:
    """
    Factory function to get the configured file storage backend.

    Returns:
        FileStorageInterface instance configured based on settings

    Raises:
        ValueError: If storage type is not supported

    Example:
        storage = get_file_storage()
        file_id = await storage.save_file(content, "document.pdf")
    """
    settings = get_settings()

    if settings.file_storage_type == "local":
        return LocalFileStorage(base_path=settings.local_storage_path)
    elif settings.file_storage_type == "s3":
        if not all(
            [
                settings.s3_bucket,
                settings.s3_access_key,
                settings.s3_secret_key,
            ]
        ):
            raise ValueError(
                "S3 storage requires S3_BUCKET, S3_ACCESS_KEY, and S3_SECRET_KEY "
                "to be configured in environment variables"
            )

        return S3FileStorage(
            bucket_name=settings.s3_bucket,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region=settings.s3_region or "us-east-1",
            endpoint_url=settings.s3_endpoint,
        )
    else:
        raise ValueError(
            f"Unsupported file storage type: {settings.file_storage_type}. "
            "Must be 'local' or 's3'"
        )
