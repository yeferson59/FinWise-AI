# File Storage Configuration Guide

This guide explains how to configure and use the file storage abstraction in FinWise-AI Backend for seamless support of both local filesystem and S3-compatible object storage.

## Overview

The file storage system provides a unified interface for saving and retrieving files regardless of the underlying storage backend. This abstraction makes it easy to:

- Switch between local and S3 storage without code changes
- Support S3-compatible services (AWS S3, MinIO, Backblaze B2, DigitalOcean Spaces, etc.)
- Ensure text extraction works seamlessly with both storage types
- Maintain consistent error handling across storage backends

## Architecture

The storage system consists of three main components:

1. **FileStorageInterface** - Abstract base class defining the storage contract
2. **LocalFileStorage** - Local filesystem implementation
3. **S3FileStorage** - S3-compatible storage implementation

All file operations in the application use this abstraction through the `get_file_storage()` factory function.

## Configuration

### Local Storage (Default)

Local storage saves files to the local filesystem. This is the default configuration for development.

**Environment Variables:**

```env
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=uploads
```

**Characteristics:**
- ✅ Simple setup - no external dependencies
- ✅ Fast for development and testing
- ✅ No additional costs
- ❌ Not suitable for distributed deployments
- ❌ No built-in redundancy

**Best for:** Development, testing, single-server deployments

### S3-Compatible Storage

S3 storage works with AWS S3 and any S3-compatible service.

**Environment Variables:**

```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT=https://s3.amazonaws.com  # Optional, for S3-compatible services
```

**Characteristics:**
- ✅ Highly scalable and distributed
- ✅ Built-in redundancy and durability
- ✅ Works with multiple cloud providers
- ✅ Suitable for production deployments
- ❌ Requires external service setup
- ❌ May incur storage and transfer costs

**Best for:** Production, distributed systems, high-availability deployments

## Supported S3-Compatible Services

The S3 storage implementation works with any S3-compatible service:

### AWS S3
```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=my-finwise-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# S3_ENDPOINT is not needed for AWS S3
```

### MinIO (Self-Hosted)
```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=finwise
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_ENDPOINT=http://localhost:9000
```

### Backblaze B2
```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=my-finwise-bucket
S3_REGION=us-west-002
S3_ACCESS_KEY=<your-b2-key-id>
S3_SECRET_KEY=<your-b2-application-key>
S3_ENDPOINT=https://s3.us-west-002.backblazeb2.com
```

### DigitalOcean Spaces
```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=finwise-storage
S3_REGION=nyc3
S3_ACCESS_KEY=<your-spaces-key>
S3_SECRET_KEY=<your-spaces-secret>
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

### Cloudflare R2
```env
FILE_STORAGE_TYPE=s3
S3_BUCKET=finwise
S3_REGION=auto
S3_ACCESS_KEY=<your-r2-access-key>
S3_SECRET_KEY=<your-r2-secret-key>
S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
```

## Usage Examples

### Basic File Operations

```python
from app.core.file_storage import get_file_storage

# Get configured storage backend
storage = get_file_storage()

# Save a file
file_content = b"Document content"
file_id = await storage.save_file(file_content, "document.pdf", "application/pdf")

# Retrieve a file
content = await storage.retrieve_file(file_id)

# Check if file exists
exists = await storage.file_exists(file_id)

# Delete a file
deleted = await storage.delete_file(file_id)
```

### Text Extraction from Stored Files

The key feature is the `get_local_path()` context manager, which provides a local file path regardless of storage backend:

```python
from app.core.file_storage import get_file_storage
from app.services.extraction import extract_text

storage = get_file_storage()

# For local storage: returns the actual path
# For S3 storage: downloads to temp file and cleans up after
with storage.get_local_path(file_id) as local_path:
    # local_path is always a valid local file path
    text = extract_text(local_path)
    # Process extracted text...
# Temporary files are automatically cleaned up
```

### Using the Storage Service

The `app/services/storage.py` module provides a convenient wrapper:

```python
from app.services import storage
from fastapi import UploadFile

# Save an uploaded file
async def handle_upload(file: UploadFile):
    file_id = await storage.save_file(file)
    
    # Use the file for text extraction
    with storage.get_local_path(file_id) as local_path:
        text = extract_text(local_path)
    
    return {"file_id": file_id, "text": text}
```

## API Endpoints

The file extraction endpoints automatically use the configured storage backend:

### Extract Text
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=invoice"
```

### Extract Text with Confidence
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text-with-confidence" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@receipt.jpg" \
  -F "document_type=receipt"
```

### Intelligent Text Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text-intelligent" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.jpg" \
  -F "document_type=invoice" \
  -F "language=eng+spa"
```

All these endpoints work identically whether you're using local or S3 storage.

## Migration Between Storage Types

### From Local to S3

1. Set up your S3 bucket and credentials
2. Update environment variables:
   ```env
   FILE_STORAGE_TYPE=s3
   S3_BUCKET=your-bucket
   S3_ACCESS_KEY=your-key
   S3_SECRET_KEY=your-secret
   ```
3. Optionally migrate existing files:
   ```python
   # Migration script example
   from app.core.file_storage import LocalFileStorage, S3FileStorage
   import os
   
   local = LocalFileStorage("uploads")
   s3 = S3FileStorage(
       bucket_name="your-bucket",
       access_key="your-key",
       secret_key="your-secret",
       region="us-east-1"
   )
   
   for filename in os.listdir("uploads"):
       filepath = os.path.join("uploads", filename)
       with open(filepath, "rb") as f:
           content = f.read()
       await s3.save_file(content, filename)
   ```

### From S3 to Local

1. Update environment variables:
   ```env
   FILE_STORAGE_TYPE=local
   LOCAL_STORAGE_PATH=uploads
   ```
2. Optionally download existing files from S3

## Error Handling

The storage abstraction provides consistent error handling:

```python
from app.core.file_storage import get_file_storage

storage = get_file_storage()

try:
    content = await storage.retrieve_file("nonexistent.pdf")
except FileNotFoundError:
    # File doesn't exist
    pass
except ValueError as e:
    # Other storage errors
    print(f"Storage error: {e}")
```

## Testing

### Unit Tests

Tests for both storage implementations are in `tests/test_services/test_file_storage.py`:

```bash
# Run all storage tests
uv run pytest tests/test_services/test_file_storage.py -v

# Run specific test class
uv run pytest tests/test_services/test_file_storage.py::TestLocalFileStorage -v
uv run pytest tests/test_services/test_file_storage.py::TestS3FileStorage -v
```

### Integration Testing

To test with actual S3:

1. Set up test S3 bucket
2. Configure test environment:
   ```env
   # .env.test
   FILE_STORAGE_TYPE=s3
   S3_BUCKET=test-bucket
   S3_ACCESS_KEY=test-key
   S3_SECRET_KEY=test-secret
   ```
3. Run integration tests:
   ```bash
   uv run pytest tests/test_services/test_file_storage.py::TestStorageIntegration -v
   ```

## Performance Considerations

### Local Storage
- **Read/Write Speed**: Very fast (limited by disk I/O)
- **Latency**: Negligible
- **Throughput**: High for single server

### S3 Storage
- **Read/Write Speed**: Depends on network and S3 region
- **Latency**: Network-dependent (typically 50-200ms)
- **Throughput**: Excellent for distributed systems
- **Optimization Tips**:
  - Use S3 regions close to your server
  - Consider S3 Transfer Acceleration for large files
  - Implement caching for frequently accessed files

## Security Best Practices

### Local Storage
- Set appropriate file permissions on upload directory
- Use directory traversal protection (handled automatically)
- Regular backup of upload directory

### S3 Storage
- Use IAM roles instead of access keys when possible
- Enable S3 bucket versioning
- Enable S3 server-side encryption
- Configure bucket policies to restrict access
- Use HTTPS endpoints (default)
- Rotate access keys regularly
- Enable S3 access logging

Example IAM policy for S3:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket/*",
        "arn:aws:s3:::your-bucket"
      ]
    }
  ]
}
```

## Troubleshooting

### Issue: "S3 storage requires S3_BUCKET, S3_ACCESS_KEY, and S3_SECRET_KEY"

**Solution:** Ensure all required S3 environment variables are set:
```bash
echo $S3_BUCKET
echo $S3_ACCESS_KEY
echo $S3_SECRET_KEY
```

### Issue: "Failed to save file to S3"

**Possible causes:**
- Invalid credentials
- Bucket doesn't exist
- No write permissions
- Network connectivity issues

**Solution:** Verify credentials and bucket configuration with AWS CLI:
```bash
aws s3 ls s3://your-bucket --endpoint-url=$S3_ENDPOINT
```

### Issue: "Failed to retrieve file from S3"

**Possible causes:**
- File doesn't exist
- No read permissions
- Network issues

**Solution:** Check if file exists:
```bash
aws s3 ls s3://your-bucket/filename --endpoint-url=$S3_ENDPOINT
```

### Issue: Local storage running out of disk space

**Solution:**
- Implement file cleanup strategy
- Move to S3 storage for scalability
- Monitor disk usage:
  ```bash
  du -sh uploads/
  ```

## Monitoring

### Local Storage
Monitor disk usage:
```bash
df -h
du -sh uploads/
```

### S3 Storage
Monitor with CloudWatch (AWS) or equivalent:
- Number of requests
- Data transfer
- Storage usage
- Error rates

## Cost Optimization

### Local Storage
- Costs: Server disk space only
- No transfer fees

### S3 Storage
Optimize costs by:
- Using lifecycle policies to move old files to cheaper storage classes
- Enabling S3 Intelligent-Tiering
- Compressing files before upload
- Choosing appropriate storage class (Standard, IA, Glacier)

Example lifecycle policy:
```json
{
  "Rules": [
    {
      "Id": "MoveToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        }
      ]
    }
  ]
}
```

## Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [Backblaze B2 S3 Compatible API](https://www.backblaze.com/b2/docs/s3_compatible_api.html)
- [aioboto3 Documentation](https://aioboto3.readthedocs.io/)
