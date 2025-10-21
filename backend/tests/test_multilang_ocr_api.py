"""
Integration tests for multi-language OCR API endpoints.
Tests the new intelligent extraction endpoint and language support.
"""

import pytest
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_test_image(text: str, width: int = 800, height: int = 400) -> BytesIO:
    """Create a test image with text for OCR testing"""
    # Create a white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text to the image
    try:
        # Try to use a default font, fall back to default if not available
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((50, 150), text, fill='black', font=font)
    
    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def english_receipt_image():
    """Create a test image with English receipt text"""
    text = "STORE RECEIPT\nTotal: $50.00\nThank you"
    return create_test_image(text)


@pytest.fixture
def spanish_receipt_image():
    """Create a test image with Spanish receipt text"""
    text = "RECIBO\nTotal: $50.00\nGracias"
    return create_test_image(text)


@pytest.fixture
def bilingual_image():
    """Create a test image with both English and Spanish"""
    text = "RECEIPT / RECIBO\nTotal: $50.00\nThank you / Gracias"
    return create_test_image(text)


class TestMultilangOCREndpoints:
    """Test multi-language OCR API endpoints"""
    
    def test_extract_text_basic_english(self, client, english_receipt_image):
        """Test basic text extraction with English text"""
        response = client.post(
            "/api/v1/files/extract-text",
            files={"file": ("receipt.png", english_receipt_image, "image/png")},
            params={"document_type": "receipt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "raw_text" in data
        assert "document_type" in data
        assert data["document_type"] == "receipt"
        assert data["file_type"] == "image"
        
        # Check that some text was extracted
        assert len(data["raw_text"]) > 0
    
    def test_extract_text_basic_spanish(self, client, spanish_receipt_image):
        """Test basic text extraction with Spanish text"""
        response = client.post(
            "/api/v1/files/extract-text",
            files={"file": ("recibo.png", spanish_receipt_image, "image/png")},
            params={"document_type": "receipt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "raw_text" in data
        assert len(data["raw_text"]) > 0
    
    def test_extract_text_intelligent_endpoint(self, client, bilingual_image):
        """Test intelligent extraction endpoint"""
        response = client.post(
            "/api/v1/files/extract-text-intelligent",
            files={"file": ("document.png", bilingual_image, "image/png")},
            params={
                "document_type": "general",
                "language": "eng+spa"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "text" in data
        assert "metadata" in data
        assert "quality" in data
        assert "document_type" in data
        assert "file_type" in data
        
        # Check metadata fields
        metadata = data["metadata"]
        assert "method_used" in metadata
        assert "detected_language" in metadata
        assert "text_length" in metadata
        
        # Check that language was detected
        assert metadata["detected_language"] in ["eng", "spa", "eng+spa"]
    
    def test_extract_text_intelligent_spanish_only(self, client, spanish_receipt_image):
        """Test intelligent extraction with Spanish language parameter"""
        response = client.post(
            "/api/v1/files/extract-text-intelligent",
            files={"file": ("recibo.png", spanish_receipt_image, "image/png")},
            params={
                "document_type": "receipt",
                "language": "spa"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "text" in data
        assert len(data["text"]) > 0
    
    def test_extract_text_with_confidence(self, client, english_receipt_image):
        """Test extraction with confidence scores"""
        response = client.post(
            "/api/v1/files/extract-text-with-confidence",
            files={"file": ("receipt.png", english_receipt_image, "image/png")},
            params={"document_type": "receipt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "raw_text" in data
        assert "confidence" in data
        
        confidence = data["confidence"]
        # Check confidence fields (if image was processed successfully)
        if "average_confidence" in confidence:
            assert isinstance(confidence["average_confidence"], (int, float))
    
    def test_get_supported_languages(self, client):
        """Test getting supported languages endpoint"""
        response = client.get("/api/v1/files/supported-languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "languages" in data
        assert "default" in data
        assert "recommendation" in data
        
        # Check that Spanish is supported
        languages = data["languages"]
        assert len(languages) >= 3
        
        lang_codes = [lang["code"] for lang in languages]
        assert "eng" in lang_codes
        assert "spa" in lang_codes
        assert "eng+spa" in lang_codes
    
    def test_get_document_types(self, client):
        """Test getting document types endpoint"""
        response = client.get("/api/v1/files/document-types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "document_types" in data
        doc_types = data["document_types"]
        
        # Should have at least 7 document types
        assert len(doc_types) >= 7
        
        # Check structure of document types
        for doc_type in doc_types:
            assert "type" in doc_type
            assert "name" in doc_type
            assert "description" in doc_type
    
    def test_invalid_document_type(self, client, english_receipt_image):
        """Test with invalid document type"""
        response = client.post(
            "/api/v1/files/extract-text",
            files={"file": ("receipt.png", english_receipt_image, "image/png")},
            params={"document_type": "invalid_type"}
        )
        
        assert response.status_code == 400
        assert "Invalid document type" in response.json()["detail"]
    
    def test_invalid_file_format(self, client):
        """Test with invalid file format"""
        # Create a fake text file
        fake_file = BytesIO(b"This is not an image")
        
        response = client.post(
            "/api/v1/files/extract-text",
            files={"file": ("document.txt", fake_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]


class TestLanguageDetection:
    """Test language detection functionality"""
    
    def test_detect_english(self):
        """Test detection of English text"""
        from app.services.intelligent_extraction import detect_language
        
        text = "The quick brown fox jumps over the lazy dog"
        lang = detect_language(text)
        
        assert lang in ["eng", "eng+spa"]
    
    def test_detect_spanish(self):
        """Test detection of Spanish text"""
        from app.services.intelligent_extraction import detect_language
        
        text = "El rápido zorro marrón salta sobre el perro perezoso"
        lang = detect_language(text)
        
        assert lang in ["spa", "eng+spa"]
    
    def test_detect_bilingual(self):
        """Test detection of mixed text"""
        from app.services.intelligent_extraction import detect_language
        
        text = "The total is $150. El total es ciento cincuenta dólares."
        lang = detect_language(text)
        
        assert lang == "eng+spa"


class TestTextCleaning:
    """Test text cleaning functionality"""
    
    def test_clean_excessive_whitespace(self):
        """Test removal of excessive whitespace"""
        from app.services.intelligent_extraction import clean_text
        
        dirty = "Text  with   too    many     spaces"
        clean = clean_text(dirty)
        
        assert "  " not in clean
        assert clean == "Text with too many spaces"
    
    def test_clean_ocr_artifacts(self):
        """Test removal of OCR artifacts"""
        from app.services.intelligent_extraction import clean_text
        
        dirty = "Text||with|||artifacts___here"
        clean = clean_text(dirty)
        
        assert "||" not in clean
        assert "___" not in clean
    
    def test_clean_line_breaks(self):
        """Test normalization of line breaks"""
        from app.services.intelligent_extraction import clean_text
        
        dirty = "Line 1\n\n\n\nLine 2"
        clean = clean_text(dirty)
        
        assert "\n\n\n" not in clean


class TestQualityValidation:
    """Test quality validation functionality"""
    
    def test_excellent_quality(self):
        """Test validation with excellent confidence"""
        from app.services.intelligent_extraction import validate_extraction_quality
        
        confidence_data = {
            'average_confidence': 90,
            'low_confidence_words': 2,
            'word_count': 100
        }
        
        result = validate_extraction_quality("Sample text", confidence_data)
        
        assert result['quality'] == 'excellent'
        assert result['score'] == 90
    
    def test_poor_quality_with_recommendations(self):
        """Test validation with poor confidence provides recommendations"""
        from app.services.intelligent_extraction import validate_extraction_quality
        
        confidence_data = {
            'average_confidence': 40,
            'low_confidence_words': 50,
            'word_count': 100
        }
        
        result = validate_extraction_quality("Test", confidence_data)
        
        assert result['quality'] == 'poor'
        assert len(result['recommendations']) > 0


# Pytest fixtures for client
@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
