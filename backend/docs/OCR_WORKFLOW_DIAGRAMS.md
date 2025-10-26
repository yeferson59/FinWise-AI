# OCR Image Processing Workflow Diagrams

## Complete Workflow with S3 Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                    OCR Image Processing Flow                     │
└─────────────────────────────────────────────────────────────────┘

User Upload
    │
    ▼
┌─────────────────────┐
│  Step 1: Save File  │  → Original image uploaded to S3
│  to Storage (S3)    │     Returns: file_identifier
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  Step 2: Get Local Path  │  → Downloads from S3 to /tmp/xyz.jpg
│  (Context Manager)       │     (Automatic cleanup on exit)
└──────────┬───────────────┘
           │
           ▼
┌───────────────────────────┐
│  Step 3: Preprocess Image │  → Creates /tmp/ocr_abc_preprocessed.jpg
│  (save_to_temp=True)      │     Applies filters, deskew, etc.
└──────────┬────────────────┘
           │
           ▼
┌──────────────────────────┐
│  Step 4: Extract Text    │  → Runs Tesseract OCR
│  with OCR                │     Returns: extracted_text
└──────────┬───────────────┘
           │
           ▼
┌────────────────────────────┐
│  Step 5: Upload Preprocessed│ → Uploads /tmp/ocr_abc_preprocessed.jpg
│  Image to S3               │     to S3 as preprocessed_{file_identifier}
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Step 6: Cleanup Temp Files│ → Removes /tmp/ocr_abc_preprocessed.jpg
│  (finally block)           │     (Original /tmp/xyz.jpg cleaned by context mgr)
└──────────┬─────────────────┘
           │
           ▼
     Return Response
     {
       "raw_text": "...",
       "preprocessed_file_id": "..."
     }
```

## Local Storage Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              OCR Image Processing Flow (Local)                   │
└─────────────────────────────────────────────────────────────────┘

User Upload
    │
    ▼
┌─────────────────────┐
│  Step 1: Save File  │  → Original saved to uploads/xyz.jpg
│  to Local Storage   │     Returns: uploads/xyz.jpg
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  Step 2: Get Local Path  │  → Returns: uploads/xyz.jpg
│  (No download needed)    │     (Already local)
└──────────┬───────────────┘
           │
           ▼
┌───────────────────────────┐
│  Step 3: Preprocess Image │  → Creates /tmp/ocr_abc_preprocessed.jpg
│  (save_to_temp=True)      │     Applies filters, deskew, etc.
└──────────┬────────────────┘
           │
           ▼
┌──────────────────────────┐
│  Step 4: Extract Text    │  → Runs Tesseract OCR
│  with OCR                │     Returns: extracted_text
└──────────┬───────────────┘
           │
           ▼
┌────────────────────────────┐
│  Step 5: (Skip S3 Upload)  │ → Local storage, no S3 upload
│                            │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Step 6: Cleanup Temp Files│ → Removes /tmp/ocr_abc_preprocessed.jpg
│  (finally block)           │     Original remains in uploads/
└──────────┬─────────────────┘
           │
           ▼
     Return Response
     {
       "raw_text": "..."
       // No preprocessed_file_id
     }
```

## File Lifecycle

```
S3 Storage Mode:
═══════════════

Original File:
  User Upload → S3 Bucket (permanent) → Downloaded to /tmp/ (temp) → Cleaned up
  
Preprocessed File:
  Created in /tmp/ (temp) → Uploaded to S3 Bucket (permanent) → Cleaned up


Local Storage Mode:
══════════════════

Original File:
  User Upload → Local uploads/ (permanent)
  
Preprocessed File:
  Created in /tmp/ (temp) → Cleaned up
```

## Error Handling

```
┌──────────────────────┐
│   Any Step Fails     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Exception Caught    │  → HTTPException raised
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Finally Block       │  → cleanup_temp_file() always runs
│  Executes            │     Removes temp preprocessed file
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Context Manager     │  → Exits, removing temp downloaded file (S3)
│  Cleanup             │
└──────────┬───────────┘
           │
           ▼
     Error Response
     {
       "detail": "Error message"
     }
```

## Component Interactions

```
┌─────────────┐
│  FastAPI    │
│  Endpoint   │
└──────┬──────┘
       │
       │ calls
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  storage    │────▶│ file_storage │────▶│     S3      │
│  service    │     │  interface   │     │   Bucket    │
└──────┬──────┘     └──────────────┘     └─────────────┘
       │
       │ calls
       ▼
┌─────────────┐     ┌──────────────┐
│preprocessing│────▶│    OpenCV    │
│  service    │     │  + rembg     │
└──────┬──────┘     └──────────────┘
       │
       │ provides
       ▼
┌─────────────┐     ┌──────────────┐
│ extraction  │────▶│  Tesseract   │
│  service    │     │     OCR      │
└─────────────┘     └──────────────┘
```

## Storage Comparison

| Aspect               | Local Storage           | S3 Storage                    |
|---------------------|-------------------------|-------------------------------|
| Original File       | `uploads/xyz.jpg`       | `s3://bucket/xyz.jpg`         |
| Preprocessed File   | `/tmp/preprocessed.jpg` | `s3://bucket/preprocessed_*`  |
| Temp Download       | N/A                     | `/tmp/xyz.jpg`                |
| Cleanup Required    | Preprocessed only       | Preprocessed + Downloaded     |
| Response Field      | No extra fields         | `preprocessed_file_id`        |
| Persistence         | Original only           | Original + Preprocessed       |
