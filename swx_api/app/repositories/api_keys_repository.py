# Repository generated based on model fields.
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlmodel import select

from swx_api.app.models.api_keys import ApiKeys, ApiKeysCreate, ApiKeysUpdate
from swx_api.app.utils.security import generate_api_key
from swx_api.core.database.db import SessionDep


class ApiKeysRepository:
    @staticmethod
    def list_api_keys(
            db: SessionDep,
            skip: int = 0,
            limit: int = 100
    ) -> List[ApiKeys]:
        """Retrieve all API keys with pagination."""
        query = select(ApiKeys).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def get_api_key_by_key(
            db: SessionDep,
            key_str: str
    ) -> ApiKeys | None:
        """Retrieve an API key by its string value."""
        statement = select(ApiKeys).where(ApiKeys.key == key_str)
        return db.exec(statement).first()

    @staticmethod
    def increment_usage_count(
            db: SessionDep,
            api_key: ApiKeys
    ) -> None:
        """Increment the usage count of the API key."""
        api_key.usage_count += 1
        db.add(api_key)
        db.commit()

    @staticmethod
    def get_api_key_by_id(
            db: SessionDep,
            id: uuid.UUID
    ) -> Optional[ApiKeys]:
        """Retrieve a single API key by ID."""
        return db.get(ApiKeys, id)

    @staticmethod
    def create_api_key(
            db: SessionDep,
            api_key: ApiKeys
    ) -> ApiKeys:
        """Persist a new API key instance."""
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def update_api_key(
            db: SessionDep,
            id: uuid.UUID,
            data: ApiKeysUpdate
    ) -> Optional[ApiKeys]:
        """Update an existing API key."""
        obj = db.get(ApiKeys, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_api_key(
            db: SessionDep,
            id: uuid.UUID
    ) -> bool:
        """Delete an existing API key."""
        obj = db.get(ApiKeys, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
