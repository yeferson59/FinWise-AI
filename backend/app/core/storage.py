"""
DEPRECATED: This module is deprecated and will be removed in a future version.

Use app.core.file_storage instead, which provides a unified abstraction
for both local and S3 storage with better error handling and features.

Migration guide:
    Old: from app.core.storage import s3_service
    New: from app.core.file_storage import get_file_storage
         storage = get_file_storage()  # Returns S3FileStorage or LocalFileStorage

The new abstraction provides:
- Unified interface for local and S3 storage
- Context manager for transparent local path access
- Better error handling
- Support for file existence checks and deletion
"""

import aioboto3
from app.config import get_settings
from botocore.client import Config
from typing import Any
import warnings

warnings.warn(
    "app.core.storage is deprecated. Use app.core.file_storage instead.",
    DeprecationWarning,
    stacklevel=2,
)

settings = get_settings()


class S3Storage:
    """
    DEPRECATED: Use S3FileStorage from app.core.file_storage instead.

    This class is maintained for backward compatibility only.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        endpoint_url: str | None,
        region: str,
        signature_version: str = "s3v4",
    ):
        self.bucket_name: str = bucket_name
        self.endpoint_url: str | None = endpoint_url

        client_config = Config(
            signature_version=signature_version, s3={"addressing_style": "path"}
        )

        self.client_params: dict[str, Any] = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": client_config,
            "region_name": region,
        }

        if endpoint_url:
            self.client_params["endpoint_url"] = endpoint_url

        self.session: aioboto3.Session = aioboto3.Session()

    async def upload_file(
        self,
        file_content: bytes,
        object_name: str,
        content_type: str = "image/jpeg",
    ) -> bool:
        async with self.session.client(**self.client_params) as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_content,
                ContentType=content_type,
            )
        return True

    async def download_file(
        self,
        object_name: str,
    ) -> bytes | None:
        async with self.session.client(**self.client_params) as s3:
            try:
                response = await s3.get_object(
                    Bucket=self.bucket_name, Key=object_name
                )
                return await response["Body"].read()
            except Exception as e:
                print(f"Error downloading file: {e}")
                return None


# DEPRECATED: This instance is maintained for backward compatibility only
# Use get_file_storage() from app.core.file_storage instead
s3_service = S3Storage(
    access_key=settings.s3_access_key,
    secret_key=settings.s3_secret_key,
    bucket_name=settings.s3_bucket,
    endpoint_url=settings.s3_endpoint,
    region=settings.s3_region,
)
