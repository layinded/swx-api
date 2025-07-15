# Service generated based on repository and model.
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlmodel import select

from swx_api.app.models.api_keys import ApiKeysCreate, ApiKeysUpdate, ApiKeys
from swx_api.app.repositories.api_keys_repository import ApiKeysRepository
from swx_api.app.utils.security import generate_api_key
from swx_api.core.database.db import SessionDep
from swx_api.core.middleware.logging_middleware import logger

MAX_USAGE_LIMIT = 1000


class ApiKeysService:
    @staticmethod
    def list_api_keys(
            db: SessionDep,
            skip: int = 0,
            limit: int = 100
    ):
        """Retrieve all API keys with pagination."""
        return ApiKeysRepository.list_api_keys(db, skip=skip, limit=limit)

    @staticmethod
    def get_api_key_by_key(
            db: SessionDep,
            key: str
    ) -> ApiKeys | None:
        """Retrieve an API key by its string value."""
        return ApiKeysRepository.get_api_key_by_key(db, key)

    @staticmethod
    def increment_usage_count(
            db: SessionDep,
            api_key: ApiKeys
    ) -> None:
        """Increment the usage count of an API key."""
        ApiKeysRepository.increment_usage_count(db, api_key)

    @staticmethod
    def validate_and_increment_usage(
            db: SessionDep,
            key_str: str
    ) -> tuple[bool, ApiKeys | dict]:
        """
        Validate the API key and increment usage count.

        Returns:
            (True, ApiKeys) if valid.
            (False, {"status": int, "detail": str}) if invalid.
        """
        try:
            api_key = ApiKeysService.get_api_key_by_key(db, key_str)

            if not api_key:
                return False, {"status": 401, "detail": "Invalid API Key"}

            if api_key.revoked:
                return False, {"status": 403, "detail": "API Key has been revoked"}

            # Normalize expires_at timezone
            expires_at = api_key.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                return False, {"status": 403, "detail": "API Key has expired"}

            if api_key.usage_count >= MAX_USAGE_LIMIT:
                return False, {"status": 429, "detail": "API Key usage limit exceeded"}

            ApiKeysService.increment_usage_count(db, api_key)
            return True, api_key

        except Exception as e:
            logger.error("Error validating API key: %s", e)
            return False, {"status": 500, "detail": "Internal Server Error"}

    @staticmethod
    def get_api_key_by_id(
            db: SessionDep,
            id: uuid.UUID
    ):
        """Retrieve a single API key by ID."""
        return ApiKeysRepository.get_api_key_by_id(db, id)

    @staticmethod
    def create_api_key(
            db: SessionDep,
            data: ApiKeysCreate
    ) -> ApiKeys:
        """Create a new API key, enforcing one active key per user."""

        # Check for existing valid key
        existing = db.exec(
            select(ApiKeys).where(
                ApiKeys.user_id == data.user_id,
                ApiKeys.revoked == False,
                ApiKeys.expires_at >= datetime.now(timezone.utc)
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User already has an active API key."
            )

        # Generate key string
        key_str = generate_api_key()

        # Determine expiry
        expires_at = data.expires_at or (datetime.now(timezone.utc) + timedelta(days=365))

        # Build ApiKeys instance
        api_key = ApiKeys(
            key=key_str,
            name="Production Key",
            revoked=False,
            usage_count=0,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            user_id=data.user_id,
        )

        return ApiKeysRepository.create_api_key(db, api_key)

    @staticmethod
    def update_api_key(
            db: SessionDep,
            id: uuid.UUID,
            data: ApiKeysUpdate
    ):
        """Update an existing API key."""
        return ApiKeysRepository.update_api_key(db, id, data)

    @staticmethod
    def delete_api_key(
            db: SessionDep,
            id: uuid.UUID
    ):
        """Delete an API key."""
        return ApiKeysRepository.delete_api_key(db, id)
