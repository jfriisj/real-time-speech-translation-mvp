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

    def upload_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
        return_key: bool = False,
        bucket: Optional[str] = None,
    ) -> str:
        target_bucket = bucket or self.bucket
        client = self._client()
        client.put_object(
            Bucket=target_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        if return_key:
            return self.build_uri(key=key, bucket=target_bucket)
        return self.presign_get(key=key, bucket=target_bucket)

    def download_bytes(
        self,
        *,
        uri: Optional[str] = None,
        key: Optional[str] = None,
        bucket: Optional[str] = None,
    ) -> bytes:
        if uri:
            bucket, key = self.parse_s3_uri(uri)
        if not key:
            raise ValueError("key or uri must be provided")
        target_bucket = bucket or self.bucket
        client = self._client()
        response = client.get_object(Bucket=target_bucket, Key=key)
        return response["Body"].read()

    def presign_get(self, *, key: str, bucket: Optional[str] = None) -> str:
        target_bucket = bucket or self.bucket
        client = self._client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": target_bucket, "Key": key},
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

    def build_uri(self, *, key: str, bucket: Optional[str] = None) -> str:
        target_bucket = bucket or self.bucket
        return f"s3://{target_bucket}/{key}"

    @staticmethod
    def parse_s3_uri(uri: str) -> tuple[str, str]:
        if not uri.startswith("s3://"):
            raise ValueError("uri must start with s3://")
        without_scheme = uri.replace("s3://", "", 1)
        bucket, _, key = without_scheme.partition("/")
        if not bucket or not key:
            raise ValueError("s3 uri must include bucket and key")
        return bucket, key
