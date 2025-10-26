"""S3-based storage layer for the Task API.

This module provides a simple abstraction over AWS S3 for storing JSON data.
Each entity (user, call, task) is stored as a separate JSON file in S3.
"""

import json
import logging
from datetime import datetime
from typing import Any, List, Optional
from botocore.exceptions import ClientError
import boto3
from pydantic import BaseModel

from .config import get_settings

logger = logging.getLogger(__name__)


class StorageClient:
    """S3-based storage client for JSON data."""

    def __init__(self):
        """Initialize the S3 client."""
        settings = get_settings()

        # Support for LocalStack or AWS
        session_kwargs = {
            "region_name": settings.aws_region,
        }

        client_kwargs = {}
        if settings.aws_endpoint_url:
            client_kwargs["endpoint_url"] = settings.aws_endpoint_url

        self.s3_client = boto3.client("s3", **client_kwargs, **session_kwargs)
        self.bucket = settings.aws_s3_bucket

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create the S3 bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket '{self.bucket}' exists")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                logger.info(f"Creating bucket '{self.bucket}'")
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket '{self.bucket}' created successfully")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    def _get_key(self, entity_type: str, entity_id: str) -> str:
        """Generate S3 key for an entity.

        Args:
            entity_type: Type of entity (users, calls, tasks)
            entity_id: Unique identifier for the entity

        Returns:
            S3 key path
        """
        return f"{entity_type}/{entity_id}.json"

    def save(self, entity_type: str, entity_id: str, data: BaseModel | dict) -> bool:
        """Save an entity to S3.

        Args:
            entity_type: Type of entity (users, calls, tasks)
            entity_id: Unique identifier for the entity
            data: Pydantic model or dict to save

        Returns:
            True if successful
        """
        key = self._get_key(entity_type, entity_id)

        # Convert Pydantic model to dict if needed
        if isinstance(data, BaseModel):
            json_data = data.model_dump(mode="json")
        else:
            json_data = data

        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(json_data, default=str),
                ContentType="application/json"
            )
            logger.info(f"Saved {entity_type}/{entity_id} to S3")
            return True
        except ClientError as e:
            logger.error(f"Failed to save {entity_type}/{entity_id}: {e}")
            raise

    def get(self, entity_type: str, entity_id: str) -> Optional[dict]:
        """Retrieve an entity from S3.

        Args:
            entity_type: Type of entity (users, calls, tasks)
            entity_id: Unique identifier for the entity

        Returns:
            Entity data as dict or None if not found
        """
        key = self._get_key(entity_type, entity_id)

        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response["Body"].read().decode("utf-8"))
            logger.info(f"Retrieved {entity_type}/{entity_id} from S3")
            return data
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.warning(f"Entity {entity_type}/{entity_id} not found")
                return None
            logger.error(f"Failed to retrieve {entity_type}/{entity_id}: {e}")
            raise

    def list_all(self, entity_type: str) -> List[dict]:
        """List all entities of a given type.

        Args:
            entity_type: Type of entity (users, calls, tasks)

        Returns:
            List of entity data dicts
        """
        prefix = f"{entity_type}/"
        entities = []

        try:
            # List all objects with the prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    # Skip if it's just the prefix
                    if key == prefix:
                        continue

                    try:
                        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                        data = json.loads(response["Body"].read().decode("utf-8"))
                        entities.append(data)
                    except ClientError as e:
                        logger.error(f"Failed to retrieve {key}: {e}")
                        continue

            logger.info(f"Retrieved {len(entities)} {entity_type} from S3")
            return entities
        except ClientError as e:
            logger.error(f"Failed to list {entity_type}: {e}")
            raise

    def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity from S3.

        Args:
            entity_type: Type of entity (users, calls, tasks)
            entity_id: Unique identifier for the entity

        Returns:
            True if successful
        """
        key = self._get_key(entity_type, entity_id)

        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted {entity_type}/{entity_id} from S3")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {entity_type}/{entity_id}: {e}")
            raise

    def update(self, entity_type: str, entity_id: str, data: BaseModel | dict) -> bool:
        """Update an entity in S3.

        This is essentially the same as save, but explicitly for updates.
        Also updates the 'updated_at' timestamp.

        Args:
            entity_type: Type of entity (users, calls, tasks)
            entity_id: Unique identifier for the entity
            data: Updated data

        Returns:
            True if successful
        """
        # Convert to dict if needed
        if isinstance(data, BaseModel):
            json_data = data.model_dump(mode="json")
        else:
            json_data = data.copy()

        # Update timestamp
        json_data["updated_at"] = datetime.utcnow().isoformat()

        return self.save(entity_type, entity_id, json_data)


# Singleton instance
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get the storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
