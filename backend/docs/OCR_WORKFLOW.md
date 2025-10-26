# OCR Image Processing Workflow Documentation

## Overview

This document describes the improved OCR image processing workflow that ensures proper handling of temporary files, S3 uploads, and cleanup operations.

## Problem Statement

The original OCR workflow had several critical issues:

1. **Preprocessed images were not uploaded to S3**: When S3 storage was configured, the original uploaded file would be saved to S3, but the preprocessed image (which is actually used for OCR) was only saved locally and never uploaded.

2. **No cleanup of temporary files**: Both the downloaded original files (when using S3) and preprocessed images were left on the local filesystem without cleanup, leading to disk space issues.

3. **Inconsistent storage handling**: The workflow didn't properly handle the case where files are stored in S3 but need to be processed locally.

## Solution

### Workflow Steps

The improved workflow follows these steps for each OCR endpoint:

```
1. Save uploaded file → Storage (Local or S3)
2. Get local path for processing → Download from S3 if needed (temp)
3. Preprocess image → Create temp preprocessed file
4. Extract text with OCR → Use preprocessed file
5. Upload preprocessed image to S3 → If S3 is configured
6. Clean up temp files → Always, even on errors
```

### Key Changes

#### 1. preprocessing.py

**Added `save_to_temp` parameter:**
```python
def preprocess_image(
    filepath: str,
    document_type: DocumentType | None = None,
    config: PreprocessingConfig | None = None,
    save_to_temp: bool = True,  # NEW
) -> str:
```

- When `save_to_temp=True` (default): Creates a temporary file using `tempfile.mkstemp()`
- When `save_to_temp=False`: Uses legacy behavior (saves alongside original)
- Temporary files are created in the system temp directory with unique names

**Added cleanup function:**
```python
def cleanup_temp_file(filepath: str) -> None:
    """Remove a temporary file if it exists."""
```

#### 2. storage.py

**Added new function to upload local files:**
```python
async def save_file_from_path(filepath: str, filename: str | None = None) -> str:
    """
    Save a file from a local path to configured storage backend.
    Useful for uploading preprocessed images to S3 after OCR processing.
    """
```

Features:
- Reads file from local path
- Automatically detects content type based on extension
- Generates unique filename if not provided
- Uploads to configured storage (Local or S3)

#### 3. files.py Endpoints

All three endpoints (`extract-text`, `extract-text-with-confidence`, `extract-text-intelligent`) now follow the same pattern:

**Variable Management:**
```python
processed_path = None  # Track preprocessed file path
is_pdf = False  # Track file type for cleanup logic
try:
    # Processing happens here
finally:
    # Cleanup only if it's not a PDF and we created a temp file
    if processed_path and not is_pdf:
        preprocessing.cleanup_temp_file(processed_path)
```

**S3 Upload Integration:**
```python
# Step 5: Upload preprocessed image to S3 if configured
settings = get_settings()
processed_file_id = None
if settings.file_storage_type == "s3" and not is_pdf:
    try:
        processed_file_id = await storage.save_file_from_path(
            processed_path, 
            filename=f"preprocessed_{file_identifier}"
        )
    except Exception as e:
        print(f"Warning: Failed to upload preprocessed image to S3: {e}")
```

**Response Enhancement:**
```python
# Include preprocessed file ID in response when available
if processed_file_id:
    result["preprocessed_file_id"] = processed_file_id
```

## Usage Examples

### Local Storage Configuration

```env
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=uploads
```

**Behavior:**
- Original file saved to `uploads/` directory
- Preprocessed image created in `/tmp/` directory
- OCR performed on preprocessed image
- Preprocessed image cleaned up after OCR
- Original file remains in `uploads/`

### S3 Storage Configuration

```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=my-bucket
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

**Behavior:**
- Original file uploaded to S3
- Original file downloaded to `/tmp/` for processing
- Preprocessed image created in `/tmp/` directory
- OCR performed on preprocessed image
- Preprocessed image uploaded to S3 with key `preprocessed_{original_file_id}`
- Both temp files cleaned up after OCR
- Both original and preprocessed files remain in S3

## Benefits

1. **Disk Space Management**: Temporary files are always cleaned up, preventing disk space issues
2. **S3 Integration**: Preprocessed images are properly stored in S3 when configured
3. **Traceability**: Response includes `preprocessed_file_id` when S3 is used
4. **Backward Compatibility**: Legacy behavior available via `save_to_temp=False`
5. **Error Handling**: Cleanup happens even if OCR fails
6. **Flexibility**: Works with both local and S3 storage seamlessly

## Testing

Comprehensive tests have been added in `tests/test_ocr_workflow.py`:

- **Preprocessing Tests**: Verify temp file creation and cleanup
- **Storage Tests**: Verify file upload from local paths
- **Integration Tests**: Verify complete workflow documentation
- **Cleanup Tests**: Verify cleanup handles edge cases

## API Response Changes

When using S3 storage, the API responses now include an additional field:

```json
{
  "raw_text": "Extracted text...",
  "document_type": "receipt",
  "file_type": "image",
  "preprocessed_file_id": "preprocessed_abc123-20231026..."  // NEW
}
```

This allows clients to:
- Track which preprocessed image was used
- Download the preprocessed image for debugging
- Maintain audit trails of OCR operations

## Migration Notes

For existing deployments:

1. **No breaking changes**: The API interface remains the same
2. **New field in response**: Clients can ignore `preprocessed_file_id` if not needed
3. **Cleanup is automatic**: No manual intervention needed for temp files
4. **S3 storage grows**: Preprocessed images will now be stored in S3, increasing storage usage

## Troubleshooting

### Issue: Temp files not cleaned up

**Symptoms**: `/tmp/` directory fills up with `ocr_*_preprocessed.*` files

**Solution**: Ensure the `finally` block is not being bypassed. Check application logs for errors.

### Issue: Preprocessed images not in S3

**Symptoms**: `preprocessed_file_id` not in response

**Solutions**:
1. Verify `FILE_STORAGE_TYPE=s3` is set
2. Check S3 credentials are valid
3. Look for warnings in application logs

### Issue: OCR quality degraded

**Symptoms**: Text extraction accuracy decreased

**Solution**: The preprocessed image is now uploaded to S3. You can download it using the `preprocessed_file_id` to verify preprocessing quality.

## Future Enhancements

Potential improvements:

1. **Configurable cleanup**: Option to keep temp files for debugging
2. **Preprocessing cache**: Cache preprocessed images to avoid reprocessing
3. **Async cleanup**: Cleanup temp files asynchronously to improve response time
4. **Storage quotas**: Monitor and limit storage usage
5. **Image comparison**: Compare original vs preprocessed for quality metrics
