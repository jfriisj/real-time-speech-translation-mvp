from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

import boto3


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectStorage:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool
    public_endpoint: Optional[str] = None
    presign_expiry_seconds: int = 60 * 60 * 24

    def _client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="us-east-1",
            use_ssl=self.secure,
        )

    def upload_bytes(self, *, key: str, data: bytes, content_type: str) -> str:
        client = self._client()
        client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.presign_expiry_seconds,
        )
        if not self.public_endpoint:
            return url

        parsed = urlparse(url)
        public_parsed = urlparse(self.public_endpoint)
        rewritten = parsed._replace(
            scheme=public_parsed.scheme or parsed.scheme,
            netloc=public_parsed.netloc or parsed.netloc,
        )
        return urlunparse(rewritten)
