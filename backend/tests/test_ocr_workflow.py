"""
Test OCR workflow improvements - ensuring proper file handling and cleanup.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
from PIL import Image
from app.services import file as file_service


def create_test_image(width: int = 400, height: int = 300) -> BytesIO:
    """Create a simple test image"""
    img = Image.new("RGB", (width, height), color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


class TestPreprocessing:
    """Test preprocessing with temp file handling"""

    def test_preprocess_saves_to_temp(self):
        """Test that preprocessing creates temp files by default"""
        from app.services import preprocessing
        from app.ocr_config import DocumentType

        # Create a temp test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            test_image = create_test_image()
            tmp.write(test_image.read())
            tmp_path = tmp.name

        try:
            # Preprocess with save_to_temp=True (default)
            preprocessed_path = preprocessing.preprocess_image(
                tmp_path, document_type=DocumentType.GENERAL, save_to_temp=True
            )

            # Verify preprocessed file exists
            assert os.path.exists(preprocessed_path)

            # Verify it's in temp directory
            temp_dir = tempfile.gettempdir()
            assert preprocessed_path.startswith(temp_dir)

            # Verify it's different from original
            assert preprocessed_path != tmp_path

            # Clean up preprocessed file
            preprocessing.cleanup_temp_file(preprocessed_path)

            # Verify cleanup worked
            assert not os.path.exists(preprocessed_path)

        finally:
            # Clean up test file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_preprocess_legacy_mode(self):
        """Test backward compatibility with save_to_temp=False"""
        from app.services import preprocessing
        from app.ocr_config import DocumentType

        # Create a temp test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            test_image = create_test_image()
            tmp.write(test_image.read())
            tmp_path = tmp.name

        try:
            # Preprocess with save_to_temp=False (legacy)
            preprocessed_path = preprocessing.preprocess_image(
                tmp_path, document_type=DocumentType.GENERAL, save_to_temp=False
            )

            # Verify preprocessed file exists
            assert os.path.exists(preprocessed_path)

            # Verify it's next to original file
            assert "_preprocessed." in preprocessed_path
            assert Path(preprocessed_path).parent == Path(tmp_path).parent

        finally:
            # Clean up both files
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(preprocessed_path):
                os.unlink(preprocessed_path)

    def test_cleanup_nonexistent_file(self):
        """Test cleanup handles nonexistent files gracefully"""
        from app.services import preprocessing

        # Should not raise an error
        preprocessing.cleanup_temp_file("/nonexistent/file.png")
        preprocessing.cleanup_temp_file("")


class TestStorageService:
    """Test storage service enhancements"""

    @pytest.mark.asyncio
    async def test_save_file_from_path_creates_unique_filename(self):
        """Test that save_file_from_path generates unique filenames"""
        from app.services import storage

        # Create a temp test file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            test_image = create_test_image()
            tmp.write(test_image.read())
            tmp_path = tmp.name

        try:
            # Mock the storage backend
            with patch("app.services.storage.get_file_storage") as mock_get_storage:
                mock_storage = Mock()
                mock_storage.save_file = AsyncMock(return_value="mocked_id")
                mock_get_storage.return_value = mock_storage

                # Save file without custom filename
                await storage.save_file_from_path(tmp_path)

                # Verify save_file was called
                assert mock_storage.save_file.called

                # Get the filename that was passed
                call_args = mock_storage.save_file.call_args
                filename = call_args[0][1]  # Second argument is filename

                # Verify filename has timestamp and extension
                assert filename.endswith(".png")
                assert len(filename) > 20  # UUID + timestamp

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_save_file_from_path_with_custom_filename(self):
        """Test save_file_from_path with custom filename"""
        from app.services import storage

        # Create a temp test file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            test_image = create_test_image()
            tmp.write(test_image.read())
            tmp_path = tmp.name

        try:
            # Mock the storage backend
            with patch("app.services.storage.get_file_storage") as mock_get_storage:
                mock_storage = Mock()
                mock_storage.save_file = AsyncMock(return_value="mocked_id")
                mock_get_storage.return_value = mock_storage

                # Save file with custom filename
                custom_name = "preprocessed_test.jpg"
                await storage.save_file_from_path(
                    tmp_path, filename=custom_name
                )

                # Verify save_file was called with custom filename
                call_args = mock_storage.save_file.call_args
                filename = call_args[0][1]
                assert filename == custom_name

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_save_file_from_path_detects_content_type(self):
        """Test that save_file_from_path detects correct content types"""
        from app.services import storage

        test_cases = [
            (".png", "image/png"),
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
            (".pdf", "application/pdf"),
            (".tiff", "image/tiff"),
            (".tif", "image/tiff"),
        ]

        for extension, expected_content_type in test_cases:
            # Create a temp file with the extension
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
                tmp.write(b"test content")
                tmp_path = tmp.name

            try:
                # Mock the storage backend
                with patch("app.services.storage.get_file_storage") as mock_get_storage:
                    mock_storage = Mock()
                    mock_storage.save_file = AsyncMock(return_value="mocked_id")
                    mock_get_storage.return_value = mock_storage

                    # Save file
                    await storage.save_file_from_path(tmp_path)

                    # Verify content type
                    call_args = mock_storage.save_file.call_args
                    content_type = call_args[0][2]
                    assert content_type == expected_content_type

            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


class TestWorkflowIntegration:
    """Test the complete OCR workflow"""

    def test_workflow_critical_operations(self):
        """Verify that critical workflow operations are present in endpoints"""
        import inspect

        # Check extract_text endpoint
        extract_text_source = inspect.getsource(file_service.extract_text)

        # Verify critical operations are present
        assert "save_file_locally" in extract_text_source
        assert "preprocess_image" in extract_text_source
        assert "extract_text" in extract_text_source
        assert "upload_to_s3_if_configured" in extract_text_source
        assert "cleanup_files" in extract_text_source
        assert "finally:" in extract_text_source

        # Verify helper functions exist
        # Note: Helper functions are now in file_service module
        assert hasattr(file_service, "validate_file_format")
        assert hasattr(file_service, "parse_document_type")
        assert hasattr(file_service, "upload_to_s3_if_configured")
        assert hasattr(file_service, "cleanup_files")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
