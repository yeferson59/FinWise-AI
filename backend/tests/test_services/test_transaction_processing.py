"""Tests for unified transaction processing service."""

import pytest
import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from app.services.transaction_processing import (
    detect_file_type,
    parse_transaction_data,
    FileType,
    process_transaction_from_file
)
from app.models.transaction import Transaction, Source
from app.models.user import User
from app.models.category import Category
from fastapi import HTTPException, UploadFile


class TestFileTypeDetection:
    """Test file type detection functionality."""

    def test_detect_image_file_jpg(self):
        """Test JPG file detection."""
        result = detect_file_type("receipt.jpg")
        assert result == FileType.IMAGE

    def test_detect_image_file_png(self):
        """Test PNG file detection."""
        result = detect_file_type("receipt.png")
        assert result == FileType.IMAGE

    def test_detect_document_file_pdf(self):
        """Test PDF file detection."""
        result = detect_file_type("invoice.pdf")
        assert result == FileType.DOCUMENT

    def test_detect_audio_file_mp3(self):
        """Test MP3 file detection."""
        result = detect_file_type("audio.mp3")
        assert result == FileType.AUDIO

    def test_detect_unsupported_file(self):
        """Test unsupported file type raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            detect_file_type("document.docx")
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)

    def test_detect_no_extension(self):
        """Test file without extension raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            detect_file_type("document")
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)


class TestTransactionDataParsing:
    """Test transaction data parsing functionality."""

    def test_parse_amount_dollar(self):
        """Test parsing dollar amount."""
        text = "Total: $123.45"
        result = parse_transaction_data(text)
        assert result["amount"] == 123.45

    def test_parse_amount_euro(self):
        """Test parsing euro amount."""
        text = "Amount: 67.89 EUR"
        result = parse_transaction_data(text)
        assert result["amount"] == 67.89

    def test_parse_amount_no_currency(self):
        """Test parsing amount without currency symbol."""
        text = "Total amount: 456.78"
        result = parse_transaction_data(text)
        assert result["amount"] == 456.78

    def test_parse_date_dd_mm_yyyy(self):
        """Test parsing date in DD/MM/YYYY format."""
        text = "Date: 15/03/2024"
        result = parse_transaction_data(text)
        assert result["date"].day == 15
        assert result["date"].month == 3
        assert result["date"].year == 2024

    def test_parse_date_yyyy_mm_dd(self):
        """Test parsing date in YYYY/MM/DD format."""
        text = "Transaction date: 2024/03/15"
        result = parse_transaction_data(text)
        assert result["date"].day == 15
        assert result["date"].month == 3
        assert result["date"].year == 2024

    def test_parse_description(self):
        """Test description extraction."""
        text = "This is a test transaction description that should be truncated."
        result = parse_transaction_data(text)
        assert result["description"] == text[:200]

    def test_parse_no_amount(self):
        """Test parsing when no amount is found."""
        text = "This is just some text without any amount."
        result = parse_transaction_data(text)
        assert result["amount"] is None

    def test_parse_no_date(self):
        """Test parsing when no date is found."""
        text = "This is just some text without any date."
        result = parse_transaction_data(text)
        # Should have current date
        assert result["date"] is not None


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_category(test_db):
    """Create a test category."""
    category = Category(name="Test Category", description="Test description")
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category


@pytest.fixture
def test_source(test_db):
    """Create a test source."""
    source = Source(name="Test Source")
    test_db.add(source)
    test_db.commit()
    test_db.refresh(source)
    return source


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Create a minimal PNG file content
    file_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    return UploadFile(
        filename="test_receipt.png",
        file=io.BytesIO(file_content)
    )


class TestTransactionProcessing:
    """Test the complete transaction processing flow."""

    @pytest.mark.asyncio
    async def test_process_transaction_image_file(self, test_db, test_user, test_category, test_source, sample_image_file):
        """Test processing an image file into a transaction."""
        # Mock the file service functions
        with patch('app.services.transaction_processing.file_service') as mock_file_service, \
             patch('app.services.transaction_processing.category_service') as mock_category_service, \
             patch('app.services.transaction_processing.transaction_service') as mock_transaction_service:

            # Mock OCR extraction
            mock_file_service.extract_text_intelligent_endpoint.return_value = {
                "raw_text": "Receipt for $25.50 on 15/03/2024",
                "confidence": 0.95,
                "document_type": "receipt",
                "file_type": "image",
                "extraction_method": "intelligent_ocr"
            }

            # Mock classification
            mock_category_service.classification.return_value = test_category

            # Mock transaction creation
            mock_transaction = Transaction(
                user_id=test_user.id,
                category_id=test_category.id,
                source_id=test_source.id,
                description="Receipt for $25.50 on 15/03/2024",
                amount=25.50,
                date=datetime(2024, 3, 15, tzinfo=timezone.utc),
                state="pending"
            )
            mock_transaction_service.create_transaction.return_value = mock_transaction

            # Process the transaction
            result = await process_transaction_from_file(
                session=test_db,
                file=sample_image_file,
                user_id=test_user.id,
                source_id=test_source.id,
                document_type="receipt"
            )

            # Verify the result structure
            assert "file_info" in result
            assert "extraction" in result
            assert "category" in result
            assert "parsed_data" in result
            assert "transaction" in result

            # Verify file info
            assert result["file_info"]["filename"] == "test_receipt.png"
            assert result["file_info"]["file_type"] == FileType.IMAGE

            # Verify extraction
            assert result["extraction"]["text"] == "Receipt for $25.50 on 15/03/2024"
            assert result["extraction"]["extraction_method"] == "intelligent_ocr"

            # Verify category
            assert result["category"]["id"] == test_category.id
            assert result["category"]["name"] == test_category.name

            # Verify parsed data
            assert result["parsed_data"]["amount"] == 25.50
            assert result["parsed_data"]["description"] == "Receipt for $25.50 on 15/03/2024"

            # Verify transaction creation was called
            mock_transaction_service.create_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_transaction_no_filename(self, test_db, test_user, test_source):
        """Test processing fails when file has no filename."""
        file_without_name = UploadFile(
            filename=None,
            file=io.BytesIO(b"test content")
        )

        with pytest.raises(HTTPException) as exc_info:
            await process_transaction_from_file(
                session=test_db,
                file=file_without_name,
                user_id=test_user.id,
                source_id=test_source.id
            )

        assert exc_info.value.status_code == 400
        assert "File must have a filename" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_transaction_unsupported_file_type(self, test_db, test_user, test_source):
        """Test processing fails for unsupported file types."""
        unsupported_file = UploadFile(
            filename="document.docx",
            file=io.BytesIO(b"test content")
        )

        with pytest.raises(HTTPException) as exc_info:
            await process_transaction_from_file(
                session=test_db,
                file=unsupported_file,
                user_id=test_user.id,
                source_id=test_source.id
            )

        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_transaction_ocr_fallback(self, test_db, test_user, test_category, test_source, sample_image_file):
        """Test OCR fallback when intelligent extraction fails."""
        with patch('app.services.transaction_processing.file_service') as mock_file_service, \
             patch('app.services.transaction_processing.category_service') as mock_category_service, \
             patch('app.services.transaction_processing.transaction_service') as mock_transaction_service:

            # Mock intelligent OCR to fail, basic OCR to succeed
            mock_file_service.extract_text_intelligent_endpoint.side_effect = Exception("Intelligent OCR failed")
            mock_file_service.extract_text.return_value = {
                "raw_text": "Basic OCR result: $10.00",
                "confidence": 0.8,
                "document_type": "receipt",
                "file_type": "image"
            }

            # Mock classification and transaction creation
            mock_category_service.classification.return_value = test_category
            mock_transaction_service.create_transaction.return_value = Transaction(
                user_id=test_user.id,
                category_id=test_category.id,
                source_id=test_source.id,
                description="Basic OCR result: $10.00",
                amount=10.00,
                date=datetime.now(timezone.utc),
                state="pending"
            )

            # Process should succeed with fallback
            result = await process_transaction_from_file(
                session=test_db,
                file=sample_image_file,
                user_id=test_user.id,
                source_id=test_source.id
            )

            # Verify fallback was used
            assert result["extraction"]["extraction_method"] == "basic_ocr"
            assert "fallback_reason" in result["extraction"]
            assert result["parsed_data"]["amount"] == 10.00