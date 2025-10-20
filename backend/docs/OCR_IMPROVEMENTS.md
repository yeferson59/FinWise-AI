# OCR Improvements Documentation

## Overview

This document describes the improvements made to the OCR (Optical Character Recognition) system in FinWise-AI to significantly enhance text extraction accuracy from images and PDFs.

## Why Was the Original `raw_text` Not Accurate?

The original implementation had several issues that affected OCR accuracy:

### 1. **Basic Tesseract Configuration**
- No Page Segmentation Mode (PSM) specified
- No OCR Engine Mode (OEM) specified
- Using default settings that aren't optimized for financial documents

### 2. **Overly Aggressive Preprocessing**
- Dilation and erosion operations were distorting text
- Fixed kernel sizes didn't adapt to different image types
- Otsu thresholding after morphological operations caused artifacts

### 3. **No Image Scaling**
- Small images resulted in poor OCR accuracy
- Tesseract works best with images at least 300 DPI or 1000+ pixels in height

### 4. **One-Size-Fits-All Approach**
- Same settings for all document types (receipts, invoices, forms, etc.)
- No optimization for specific use cases

### 5. **Poor Deskewing Algorithm**
- Hough Line Transform is sensitive to noise
- Can fail on images with complex layouts

## What Has Been Improved?

### 1. **Advanced Tesseract Configuration**
```python
# Before
extracted_text = pytesseract.image_to_string(image, lang="eng")

# After
custom_config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"
extracted_text = pytesseract.image_to_string(image, lang="eng", config=custom_config)
```

- **OEM 3**: Uses both Legacy and LSTM (neural network) engines
- **PSM 6**: Assumes single uniform block of text (best for most documents)
- **preserve_interword_spaces**: Maintains spacing between words

### 2. **Intelligent Image Preprocessing**
- **Image Scaling**: Automatically scales small images to optimal size
- **Better Deskewing**: Uses contour detection instead of Hough Transform
- **CLAHE Enhancement**: Improves contrast adaptively
- **Smart Denoising**: Uses Non-Local Means denoising
- **Configurable Parameters**: Different settings for different document types

### 3. **Document Type Profiles**
Pre-configured settings for different document types:
- **Receipt**: High resolution, enhanced contrast for small text
- **Invoice**: Optimized for tables and structured data
- **Document**: General text documents with paragraphs
- **Form**: Sparse text detection for forms with fields
- **Screenshot**: Minimal processing for digital text
- **Photo**: Aggressive denoising for camera images
- **General**: Balanced settings for unknown types

### 4. **Confidence Scoring**
New endpoint to get OCR confidence metrics:
- Average confidence per document
- Per-word confidence scores
- Low confidence word count

## How to Use

### Basic Usage (Backward Compatible)

```python
# In your endpoint (old way still works)
from app.services import preprocessing, extraction

file_path = await storage.save_file(file)
preprocessed_path = preprocessing.preprocess_image(file_path)
raw_text = extraction.extract_text(preprocessed_path)
```

### Using Document Type Optimization

```python
from app.services import preprocessing, extraction
from app.config.ocr_config import DocumentType

file_path = await storage.save_file(file)

# Preprocess with document type
preprocessed_path = preprocessing.preprocess_image(
    file_path,
    document_type=DocumentType.RECEIPT
)

# Extract with document type
raw_text = extraction.extract_text(
    preprocessed_path,
    document_type=DocumentType.RECEIPT
)
```

### Using Custom Configuration

```python
from app.config.ocr_config import OCRConfig, PSMMode, OEMMode, PreprocessingConfig

# Custom OCR config
ocr_config = OCRConfig(
    psm_mode=PSMMode.SINGLE_BLOCK,
    oem_mode=OEMMode.NEURAL_NET,
    language="eng",
    preserve_interword_spaces=True
)

# Custom preprocessing config
preprocessing_config = PreprocessingConfig(
    scale_min_height=1500,
    enable_deskew=True,
    denoise_strength=12,
    enable_clahe=True,
    clahe_clip_limit=3.0
)

# Use custom configs
preprocessed_path = preprocessing.preprocess_image(file_path, config=preprocessing_config)
raw_text = extraction.extract_text(preprocessed_path, ocr_config=ocr_config)
```

### API Endpoints

#### 1. Extract Text (Updated)

```bash
POST /api/v1/files/extract-text?document_type=receipt

# Response
{
  "raw_text": "RECEIPT\nStore Name\nTotal: $123.45",
  "document_type": "receipt",
  "file_type": "image"
}
```

#### 2. Extract Text with Confidence (New)

```bash
POST /api/v1/files/extract-text-with-confidence?document_type=invoice

# Response
{
  "raw_text": "INVOICE #12345\nAmount: $500.00",
  "confidence": {
    "average_confidence": 87.5,
    "min_confidence": 65,
    "max_confidence": 98,
    "word_count": 12,
    "low_confidence_words": 2
  },
  "document_type": "invoice"
}
```

#### 3. Get Document Types (New)

```bash
GET /api/v1/files/document-types

# Response
{
  "document_types": [
    {
      "type": "receipt",
      "name": "Receipt",
      "description": "Optimized for receipts with small text and numbers"
    },
    ...
  ]
}
```

## Document Type Guide

### When to Use Each Type

| Document Type | Best For | Key Features |
|--------------|----------|--------------|
| `receipt` | Store receipts, transaction slips | High resolution scaling, enhanced contrast, number-focused |
| `invoice` | Invoices, bills, statements | Table detection, structured data extraction |
| `document` | Letters, reports, articles | Paragraph segmentation, minimal processing |
| `form` | Application forms, surveys | Sparse text detection, field recognition |
| `screenshot` | Computer screenshots | Minimal processing, digital text optimization |
| `photo` | Camera photos of documents | Aggressive deskew, noise removal |
| `general` | Unknown or mixed types | Balanced settings |

## Configuration Parameters

### PSM (Page Segmentation Mode)

```python
PSMMode.OSD_ONLY = 0          # Orientation and script detection only
PSMMode.AUTO_OSD = 1          # Automatic with OSD
PSMMode.AUTO_ONLY = 2         # Automatic, no OSD
PSMMode.AUTO = 3              # Fully automatic (default)
PSMMode.SINGLE_COLUMN = 4     # Single column of text
PSMMode.SINGLE_BLOCK = 6      # Single uniform block ⭐ Best for most docs
PSMMode.SINGLE_LINE = 7       # Single text line
PSMMode.SINGLE_WORD = 8       # Single word
PSMMode.SPARSE_TEXT = 11      # Sparse text (forms)
```

### OEM (OCR Engine Mode)

```python
OEMMode.LEGACY = 0            # Legacy engine only
OEMMode.NEURAL_NET = 1        # LSTM engine only ⭐ Best for digital text
OEMMode.LEGACY_LSTM = 2       # Both engines
OEMMode.DEFAULT = 3           # Default (recommended) ⭐
```

### Preprocessing Parameters

```python
PreprocessingConfig(
    scale_min_height=1000,           # Minimum height in pixels
    enable_deskew=True,              # Correct rotation
    denoise_strength=10,             # 0-20, higher = more denoising
    enable_clahe=True,               # Contrast enhancement
    clahe_clip_limit=2.0,            # 1.0-4.0, higher = more contrast
    adaptive_threshold_block_size=15,# Must be odd number
    adaptive_threshold_c=5,          # Threshold constant
    enable_morphology=True,          # Noise removal
    morphology_kernel_size=(1, 1),  # Kernel size for morphology
    morphology_iterations=1          # Number of iterations
)
```

## Tips for Best Results

### 1. **Choose the Right Document Type**
```python
# ✅ Good
extract_text(file_path, document_type=DocumentType.RECEIPT)

# ❌ Less optimal
extract_text(file_path)  # Uses generic settings
```

### 2. **Check Confidence Scores**
```python
text, confidence = extraction.extract_text_with_confidence(file_path)
if confidence["average_confidence"] < 70:
    print("⚠️ Low confidence, results may be inaccurate")
```

### 3. **Image Quality Matters**
- **Minimum resolution**: 300 DPI or 1000px height
- **Lighting**: Even, no shadows
- **Focus**: Sharp, not blurry
- **Format**: PNG or JPEG with minimal compression

### 4. **For Poor Quality Images**
```python
# Use more aggressive settings
config = PreprocessingConfig(
    scale_min_height=1500,      # Higher scaling
    denoise_strength=15,        # More denoising
    clahe_clip_limit=3.0        # More contrast
)
```

### 5. **For High Quality Digital Images**
```python
# Use minimal processing
config = PreprocessingConfig(
    scale_min_height=800,
    enable_deskew=False,
    denoise_strength=5,
    enable_clahe=False
)
```

## Testing the Improvements

### Before and After Comparison

```python
# Test with your sample images
from app.config.ocr_config import DocumentType

# Old way (less accurate)
text_old = extraction.extract_text_simple(file_path)

# New way (more accurate)
text_new = extraction.extract_text(
    file_path,
    document_type=DocumentType.RECEIPT
)

print(f"Old: {len(text_old)} chars, New: {len(text_new)} chars")
```

### Debugging Low Accuracy

1. **Check preprocessed image**:
   - Look at the `*_preprocessed.png` file
   - Ensure text is clear and not distorted

2. **Try different PSM modes**:
   ```python
   for psm in [PSMMode.AUTO, PSMMode.SINGLE_BLOCK, PSMMode.SPARSE_TEXT]:
       config = OCRConfig(psm_mode=psm)
       text = extraction.extract_text(file_path, ocr_config=config)
       print(f"PSM {psm.value}: {text[:100]}")
   ```

3. **Check confidence scores**:
   ```python
   text, conf = extraction.extract_text_with_confidence(file_path)
   print(f"Avg confidence: {conf['average_confidence']:.1f}%")
   print(f"Low confidence words: {conf['low_confidence_words']}")
   ```

## Common Issues and Solutions

### Issue: Text is partially missing
**Solution**: Try `PSMMode.SPARSE_TEXT` or increase image resolution

### Issue: Extra characters or noise
**Solution**: Increase `denoise_strength` or use character whitelist

### Issue: Numbers are misread
**Solution**: Use `DocumentType.RECEIPT` profile with number whitelist

### Issue: Rotated text not detected
**Solution**: Ensure `enable_deskew=True` in preprocessing config

### Issue: Low confidence scores
**Solution**: Improve image quality or try different preprocessing settings

## Performance Considerations

### Processing Time by Configuration

- **Minimal preprocessing**: ~0.5-1s per image
- **Standard preprocessing**: ~1-2s per image
- **Aggressive preprocessing**: ~2-4s per image

### Optimization Tips

1. **Skip preprocessing for high-quality images**
2. **Use lower resolution for large images** (max 2000px height)
3. **Disable unused preprocessing steps**
4. **Cache preprocessed images** if processing multiple times

## Migration Guide

### Updating Existing Code

```python
# Old code
preprocessed_path = preprocessing.preprocess_image(file_path)
raw_text = extraction.extract_text(preprocessed_path)

# Updated code (recommended)
from app.config.ocr_config import DocumentType

preprocessed_path = preprocessing.preprocess_image(
    file_path,
    document_type=DocumentType.RECEIPT  # Choose appropriate type
)
raw_text = extraction.extract_text(
    preprocessed_path,
    document_type=DocumentType.RECEIPT
)
```

### Backward Compatibility

All old code will continue to work with default settings. The improvements are opt-in through the new parameters.

## Future Improvements

- [ ] Support for multi-language OCR
- [ ] GPU acceleration for faster processing
- [ ] Machine learning model for automatic document type detection
- [ ] Layout analysis and structured data extraction
- [ ] Support for handwritten text recognition

## References

- [Tesseract Documentation](https://tesseract-ocr.github.io/)
- [OpenCV Image Processing](https://docs.opencv.org/)
- [Best Practices for OCR](https://github.com/tesseract-ocr/tesseract/wiki/ImproveQuality)

## Support

If you encounter issues or have questions:
1. Check the preprocessed image output
2. Review confidence scores
3. Try different document type profiles
4. Consult this documentation
5. Open an issue with sample images (redacted if needed)
