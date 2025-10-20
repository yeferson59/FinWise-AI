# API Examples - OCR Endpoints

This document provides practical examples of how to use the improved OCR API endpoints.

## Prerequisites

Make sure the backend server is running:

```bash
cd backend
uvicorn app.main:app --reload
```

## Base URL

```
http://localhost:8000/api/v1/files
```

## 1. Extract Text (Basic)

Extract text from an image without specifying document type:

```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"
```

**Response:**
```json
{
  "raw_text": "Extracted text content here...",
  "document_type": "general",
  "file_type": "image"
}
```

## 2. Extract Text with Document Type (Receipt)

Optimize extraction for receipts:

```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=receipt" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/receipt.jpg"
```

**Response:**
```json
{
  "raw_text": "STORE NAME\nRECEIPT #12345\n\nItem 1    $10.00\nItem 2    $15.50\nTax       $2.55\nTotal     $28.05",
  "document_type": "receipt",
  "file_type": "image"
}
```

## 3. Extract Text with Document Type (Invoice)

Optimize extraction for invoices:

```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/invoice.pdf"
```

**Response:**
```json
{
  "raw_text": "INVOICE\nInvoice #: INV-2024-001\nDate: 2024-01-15\n\nBill To:\nCompany Name\n123 Street\n\nAmount: $500.00",
  "document_type": "invoice",
  "file_type": "pdf"
}
```

## 4. Extract Text with Confidence Scores

Get OCR confidence metrics (images only):

```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text-with-confidence?document_type=receipt" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/receipt.jpg"
```

**Response:**
```json
{
  "raw_text": "STORE NAME\nRECEIPT #12345\nTotal: $28.05",
  "confidence": {
    "average_confidence": 87.5,
    "min_confidence": 65,
    "max_confidence": 98,
    "word_count": 12,
    "low_confidence_words": 2
  },
  "document_type": "receipt"
}
```

## 5. Get Available Document Types

List all supported document types:

```bash
curl -X GET "http://localhost:8000/api/v1/files/document-types" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "document_types": [
    {
      "type": "receipt",
      "name": "Receipt",
      "description": "Optimized for receipts with small text and numbers"
    },
    {
      "type": "invoice",
      "name": "Invoice",
      "description": "Optimized for invoices with tables and structured data"
    },
    {
      "type": "document",
      "name": "Document",
      "description": "General documents with paragraphs of text"
    },
    {
      "type": "form",
      "name": "Form",
      "description": "Forms with fields and checkboxes"
    },
    {
      "type": "screenshot",
      "name": "Screenshot",
      "description": "Computer screenshots with clear text"
    },
    {
      "type": "photo",
      "name": "Photo",
      "description": "Photos of documents taken with camera"
    },
    {
      "type": "general",
      "name": "General",
      "description": "Default profile for unknown document types"
    }
  ]
}
```

## 6. Document Type Examples

### Receipt
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=receipt" \
  -F "file=@receipt.jpg"
```

### Invoice
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=invoice" \
  -F "file=@invoice.pdf"
```

### Form
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=form" \
  -F "file=@application_form.png"
```

### Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=screenshot" \
  -F "file=@screenshot.png"
```

### Photo
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=photo" \
  -F "file=@photo_of_document.jpg"
```

## Python Examples

### Using Requests Library

```python
import requests

# Extract text with document type
url = "http://localhost:8000/api/v1/files/extract-text"
params = {"document_type": "receipt"}
files = {"file": open("receipt.jpg", "rb")}

response = requests.post(url, params=params, files=files)
data = response.json()

print(f"Extracted text: {data['raw_text']}")
print(f"Document type: {data['document_type']}")
```

### Extract with Confidence

```python
import requests

url = "http://localhost:8000/api/v1/files/extract-text-with-confidence"
params = {"document_type": "invoice"}
files = {"file": open("invoice.png", "rb")}

response = requests.post(url, params=params, files=files)
data = response.json()

print(f"Text: {data['raw_text']}")
print(f"Confidence: {data['confidence']['average_confidence']:.1f}%")
print(f"Low confidence words: {data['confidence']['low_confidence_words']}")
```

## JavaScript Examples

### Using Fetch API

```javascript
async function extractText(file, documentType = 'general') {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `http://localhost:8000/api/v1/files/extract-text?document_type=${documentType}`,
    {
      method: 'POST',
      body: formData
    }
  );

  const data = await response.json();
  return data;
}

// Usage
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];
const result = await extractText(file, 'receipt');
console.log(result.raw_text);
```

### Using Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extractTextWithConfidence(filePath, documentType) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/files/extract-text-with-confidence',
      formData,
      {
        params: { document_type: documentType },
        headers: formData.getHeaders()
      }
    );

    console.log('Text:', response.data.raw_text);
    console.log('Confidence:', response.data.confidence);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Usage
extractTextWithConfidence('receipt.jpg', 'receipt');
```

## Testing with Different Document Types

### Create a test script:

```bash
#!/bin/bash

# Test different document types with the same image
IMAGE_PATH="/path/to/test/image.jpg"

echo "Testing different document types..."

for DOCTYPE in receipt invoice document form screenshot photo general
do
  echo ""
  echo "Testing with document_type: $DOCTYPE"
  curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=$DOCTYPE" \
    -F "file=@$IMAGE_PATH" \
    | jq '.raw_text' | head -n 5
done
```

Save as `test_document_types.sh` and run:
```bash
chmod +x test_document_types.sh
./test_document_types.sh
```

## Error Handling

### Invalid file format:
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text" \
  -F "file=@document.txt"
```

**Response (400):**
```json
{
  "detail": "Invalid file format"
}
```

### Invalid document type:
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=invalid" \
  -F "file=@image.jpg"
```

**Response (400):**
```json
{
  "detail": "Invalid document type. Must be one of: receipt, invoice, document, form, screenshot, photo, general"
}
```

## Tips for Best Results

1. **Choose the correct document type** for your use case
2. **Use high-quality images** (minimum 300 DPI)
3. **Check confidence scores** for quality assessment
4. **Test different document types** if results are poor
5. **Ensure good lighting** and minimal blur in photos

## Performance Benchmarks

Approximate processing times (may vary based on hardware):

- Small image (< 1MB): 0.5-1s
- Medium image (1-3MB): 1-2s
- Large image (> 3MB): 2-4s
- PDF (single page): 0.3-0.7s
- PDF (multi-page): 0.5s per page

## Support

For issues or questions:
1. Check the OCR_IMPROVEMENTS.md documentation
2. Verify image quality and format
3. Try different document_type values
4. Check confidence scores for quality metrics
