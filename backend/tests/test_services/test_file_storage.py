"""
Tests for file storage abstraction layer.

This module tests both LocalFileStorage and S3FileStorage implementations
to ensure they work correctly and provide a consistent interface.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.file_storage import (
    LocalFileStorage,
    S3FileStorage,
    get_file_storage,
)


class TestLocalFileStorage:
    """Test cases for LocalFileStorage implementation."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a LocalFileStorage instance for testing."""
        return LocalFileStorage(base_path=temp_storage_dir)

    @pytest.mark.asyncio
    async def test_save_file(self, storage, temp_storage_dir):
        """Test saving a file to local storage."""
        file_content = b"Test file content"
        filename = "test.txt"

        file_identifier = await storage.save_file(file_content, filename)

        # Verify file was saved
        assert file_identifier == os.path.realpath(str(Path(temp_storage_dir) / filename))
        assert os.path.exists(file_identifier)

        # Verify content
        with open(file_identifier, "rb") as f:
            assert f.read() == file_content

    @pytest.mark.asyncio
    async def test_retrieve_file(self, storage, temp_storage_dir):
        """Test retrieving a file from local storage."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Save file first
        file_identifier = await storage.save_file(file_content, filename)

        # Retrieve file
        retrieved_content = await storage.retrieve_file(file_identifier)

        assert retrieved_content == file_content

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_file(self, storage):
        """Test retrieving a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            await storage.retrieve_file("/nonexistent/path/file.txt")

    @pytest.mark.asyncio
    async def test_get_local_path(self, storage, temp_storage_dir):
        """Test get_local_path context manager for local storage."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Create a test file
        test_path = Path(temp_storage_dir) / filename
        with open(test_path, "wb") as f:
            f.write(file_content)

        # Use get_local_path
        async with storage.get_local_path(str(test_path)) as local_path:
            assert os.path.exists(local_path)
            with open(local_path, "rb") as f:
                assert f.read() == file_content

        # File should still exist after context (no cleanup for local)
        assert os.path.exists(str(test_path))

    @pytest.mark.asyncio
    async def test_get_local_path_nonexistent(self, storage):
        """Test get_local_path with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            async with storage.get_local_path("/nonexistent/file.txt"):
                pass

    @pytest.mark.asyncio
    async def test_delete_file(self, storage, temp_storage_dir):
        """Test deleting a file from local storage."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Save file first
        file_identifier = await storage.save_file(file_content, filename)
        assert os.path.exists(file_identifier)

        # Delete file
        result = await storage.delete_file(file_identifier)

        assert result is True
        assert not os.path.exists(file_identifier)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage):
        """Test deleting a file that doesn't exist."""
        result = await storage.delete_file("/nonexistent/file.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists(self, storage, temp_storage_dir):
        """Test checking if a file exists."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Save file
        file_identifier = await storage.save_file(file_content, filename)

        # Check existence
        exists = await storage.file_exists(file_identifier)
        assert exists is True

        # Check nonexistent file
        exists = await storage.file_exists("/nonexistent/file.txt")
        assert exists is False


class TestS3FileStorage:
    """Test cases for S3FileStorage implementation."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_session(self, mock_s3_client):
        """Create a mock aioboto3 session."""
        session = MagicMock()
        # Make the context manager return our mock client
        session.client.return_value.__aenter__.return_value = mock_s3_client
        session.client.return_value.__aexit__.return_value = None
        return session

    @pytest.fixture
    def storage(self, mock_session):
        """Create an S3FileStorage instance with mocked session."""
        storage = S3FileStorage(
            bucket_name="test-bucket",
            access_key="test-access-key",
            secret_key="test-secret-key",
            region="us-east-1",
        )
        storage.session = mock_session
        return storage

    @pytest.mark.asyncio
    async def test_save_file(self, storage, mock_s3_client):
        """Test saving a file to S3."""
        file_content = b"Test file content"
        filename = "test.txt"
        content_type = "text/plain"

        file_identifier = await storage.save_file(file_content, filename, content_type)

        # Verify S3 put_object was called correctly
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=filename,
            Body=file_content,
            ContentType=content_type,
        )
        assert file_identifier == filename

    @pytest.mark.asyncio
    async def test_retrieve_file(self, storage, mock_s3_client):
        """Test retrieving a file from S3."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Mock the response
        mock_body = AsyncMock()
        mock_body.read.return_value = file_content
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Retrieve file
        retrieved_content = await storage.retrieve_file(filename)

        # Verify S3 get_object was called correctly
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key=filename
        )
        assert retrieved_content == file_content

    @pytest.mark.asyncio
    async def test_retrieve_file_error(self, storage, mock_s3_client):
        """Test retrieving a file that doesn't exist in S3."""
        mock_s3_client.get_object.side_effect = Exception("Not found")

        with pytest.raises(ValueError, match="Failed to retrieve file from S3"):
            await storage.retrieve_file("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete_file(self, storage, mock_s3_client):
        """Test deleting a file from S3."""
        filename = "test.txt"

        result = await storage.delete_file(filename)

        # Verify S3 delete_object was called
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key=filename
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_error(self, storage, mock_s3_client):
        """Test deleting a file with error."""
        mock_s3_client.delete_object.side_effect = Exception("Delete failed")

        result = await storage.delete_file("test.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists(self, storage, mock_s3_client):
        """Test checking if a file exists in S3."""
        filename = "test.txt"

        # File exists
        result = await storage.file_exists(filename)
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key=filename
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_file_not_exists(self, storage, mock_s3_client):
        """Test checking if a nonexistent file exists in S3."""
        mock_s3_client.head_object.side_effect = Exception("Not found")

        result = await storage.file_exists("nonexistent.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_local_path(self, storage, mock_s3_client):
        """Test get_local_path downloads file to temp location."""
        file_content = b"Test file content"
        filename = "test.txt"

        # We need to mock the retrieve_file method instead
        with patch.object(
            storage, "retrieve_file", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = file_content

            async with storage.get_local_path(filename) as local_path:
                # Verify a temporary file was created
                assert os.path.exists(local_path)
                assert local_path.endswith(".txt")

                # Verify content was written
                with open(local_path, "rb") as f:
                    assert f.read() == file_content

            # Verify temp file was cleaned up
            assert not os.path.exists(local_path)


class TestGetFileStorage:
    """Test cases for the get_file_storage factory function."""

    def test_get_local_storage(self):
        """Test getting local file storage."""
        with patch("app.core.file_storage.get_settings") as mock_settings:
            mock_settings.return_value.file_storage_type = "local"
            mock_settings.return_value.local_storage_path = "uploads"

            storage = get_file_storage()

            assert isinstance(storage, LocalFileStorage)

    def test_get_s3_storage(self):
        """Test getting S3 file storage."""
        with patch("app.core.file_storage.get_settings") as mock_settings:
            mock_settings.return_value.file_storage_type = "s3"
            mock_settings.return_value.s3_bucket = "test-bucket"
            mock_settings.return_value.s3_access_key = "access-key"
            mock_settings.return_value.s3_secret_key = "secret-key"
            mock_settings.return_value.s3_region = "us-east-1"
            mock_settings.return_value.s3_endpoint = None

            storage = get_file_storage()

            assert isinstance(storage, S3FileStorage)

    def test_get_s3_storage_missing_config(self):
        """Test getting S3 storage with missing configuration."""
        with patch("app.core.file_storage.get_settings") as mock_settings:
            mock_settings.return_value.file_storage_type = "s3"
            mock_settings.return_value.s3_bucket = ""
            mock_settings.return_value.s3_access_key = ""
            mock_settings.return_value.s3_secret_key = ""

            with pytest.raises(ValueError, match="S3 storage requires"):
                get_file_storage()

    def test_get_unsupported_storage(self):
        """Test getting unsupported storage type."""
        with patch("app.core.file_storage.get_settings") as mock_settings:
            mock_settings.return_value.file_storage_type = "unsupported"

            with pytest.raises(ValueError, match="Unsupported file storage type"):
                get_file_storage()


class TestStorageIntegration:
    """Integration tests for storage service with new abstraction."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_save_and_retrieve_workflow(self, temp_storage_dir):
        """Test complete workflow of saving and retrieving a file."""
        with patch("app.core.file_storage.get_settings") as mock_settings:
            mock_settings.return_value.file_storage_type = "local"
            mock_settings.return_value.local_storage_path = temp_storage_dir

            from app.services import storage as storage_service
            from fastapi import UploadFile
            from io import BytesIO

            # Create a mock uploaded file
            file_content = b"Test document content"
            file = UploadFile(filename="test_document.txt", file=BytesIO(file_content))

            # Save file
            file_identifier = await storage_service.save_file(file)
            assert file_identifier is not None

            # Retrieve file
            retrieved_content = await storage_service.retrieve_file(file_identifier)
            assert retrieved_content == file_content

            # Get local path
            async with storage_service.get_local_path(file_identifier) as local_path:
                assert os.path.exists(local_path)
                with open(local_path, "rb") as f:
                    assert f.read() == file_content
