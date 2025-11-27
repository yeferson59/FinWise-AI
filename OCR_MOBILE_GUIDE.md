# OCR Mobile Implementation Guide

## Overview

The OCR feature in the mobile app now uses **real backend OCR processing** with the actual API instead of a placeholder. When a user captures or selects an image, it's processed by the backend using Tesseract OCR with AI-powered enhancements.

## Features

### Camera & Photo Library Integration
- **Camera**: Capture documents in real-time
- **Photo Library**: Select existing images from device storage
- Permission handling with user-friendly alerts

### Real OCR Processing
- Uses backend Tesseract OCR engine
- Supports multiple document types (receipt, invoice, document, form, screenshot, photo, general)
- Automatic language detection (English + Spanish)
- Quality assessment and auto-correction

### Confidence Metrics
- Displays OCR confidence score (0-100%)
- Visual progress bar:
  - **Green** (≥70%): High confidence
  - **Yellow** (<70%): Lower confidence
- Confidence extracted from OCR metadata

### Transaction Data Extraction
- **Amount**: Automatically extracted and parsed
- **Date**: Date detection and parsing
- **Description**: Transaction description from extracted text
- Auto-categorization using AI
- Auto-classification of transaction source

### Results Display
- Extracted text in scrollable box
- Parsed transaction data display
- Success confirmation when transaction is created
- Option to scan another document

## How to Use

### Step 1: Open OCR Section
Navigate to the OCR section from the app menu.

### Step 2: Start Scanning
Tap the **"Iniciar escaneo"** button

### Step 3: Choose Source
- **Camera**: Capture document with device camera
- **Photo Library**: Select existing image from device

### Step 4: View Results
The app displays:
- ✅ Confidence score with visual indicator
- ✅ Full extracted text
- ✅ Parsed data (amount, date, description)
- ✅ Success message if transaction was created

### Step 5: Continue or Go Back
- **Escanear otro documento**: Scan another document
- **Volver**: Return to previous screen

## Technical Details

### API Endpoint Used
```
POST /api/v1/transactions/process-from-file
?user_id={user_id}
&source_id={source_id}
&document_type={document_type}
```

### Response Structure
```json
{
  "file_info": {
    "filename": "receipt_123.jpg",
    "file_type": "image",
    "size": 1024000
  },
  "extraction": {
    "raw_text": "Extracted text from image...",
    "confidence": 85,
    "document_type": "photo",
    "file_type": "image",
    "metadata": {
      "strategy_used": "phase1_standard",
      "image_size": {"width": 1920, "height": 1080},
      "quality_info": {...}
    }
  },
  "category": {
    "id": 1,
    "name": "Food & Dining",
    "description": "Restaurant and food expenses"
  },
  "source": {
    "id": 2,
    "name": "Receipt",
    "description": "Physical receipt scanning"
  },
  "parsed_data": {
    "amount": 45.99,
    "date": "2024-11-20T00:00:00+00:00",
    "description": "Restaurant ABC - Lunch",
    "confidence": 92
  },
  "transaction": {
    "id": "uuid-here",
    "user_id": 1,
    "category_id": 1,
    "source_id": 2,
    "description": "Restaurant ABC - Lunch",
    "amount": 45.99,
    "date": "2024-11-20T00:00:00+00:00",
    "state": "pending",
    "created_at": "2024-11-20T18:30:00+00:00",
    "updated_at": "2024-11-20T18:30:00+00:00"
  }
}
```

## Backend Processing Flow

1. **Image Upload**: Mobile sends image to backend via FormData
2. **Text Extraction**: Tesseract OCR with preprocessing
3. **Quality Assessment**: Image quality check with auto-correction if needed
4. **Confidence Calculation**: Confidence score based on OCR metadata
5. **Text Parsing**: AI-powered parsing to extract structured data
6. **Category Classification**: Automatic category assignment
7. **Source Classification**: Automatic source assignment
8. **Transaction Creation**: New transaction created in database
9. **Response**: All results sent back to mobile

## OCR Improvements Used

The backend applies multiple OCR optimization phases:

### Phase 1: Quality & Caching
- Image quality assessment
- Auto-correction when needed
- Cache check for fast results

### Phase 2: Advanced Strategies
- Multiple binarization methods
- Orientation detection and correction
- Multi-strategy voting for difficult images

### Phase 3: Optimizations
- Incremental processing for large images
- Parallel execution for speed

## Error Handling

The app handles various error scenarios:

- **Permission denied**: User denied camera/photo library access
- **Processing failed**: Backend OCR extraction error
- **Not authenticated**: User session expired
- **Network error**: Connection issue with backend

All errors are displayed as user-friendly alerts with actionable messages.

## Performance

- **Small images** (<4MB): Usually 2-5 seconds
- **Large images** (>4MB): 5-10 seconds using incremental processing
- **Cached results**: <100ms for exact duplicate images

## Supported Document Types

When processing, you can specify document type for optimization:

- **receipt**: Receipts with small text and numbers
- **invoice**: Invoices with tables and structured data
- **document**: General documents with paragraphs
- **form**: Forms with fields and checkboxes
- **screenshot**: Computer screenshots
- **photo**: Camera photos of documents
- **general**: Default for unknown types (default used)

## Dependencies

The OCR feature requires:
- `expo-image-picker@~17.0.8`: Camera and photo library access
- `shared` package: API communication

## Setup Instructions

1. Install dependencies:
   ```bash
   cd frontend/mobile
   npm install
   ```

2. Start the app:
   ```bash
   npm start
   ```

3. Navigate to OCR section
4. Grant camera/photo library permissions if prompted
5. Start scanning documents

## Troubleshooting

### Camera not working
- Grant camera permission in app settings
- Ensure good lighting for image capture
- Use device camera app to test camera functionality

### Poor OCR results
- Ensure document is well-lit and clear
- Hold camera steady and perpendicular to document
- Use high-quality images
- Check confidence score to assess quality

### Transaction not created
- Check network connection
- Ensure user is authenticated
- Verify backend is running
- Check backend logs for errors

## Future Improvements

Potential enhancements:
- Real-time document preview
- Confidence threshold warning
- Manual text editing before saving
- Batch scanning multiple documents
- PDF document support
- Multi-language support optimization
