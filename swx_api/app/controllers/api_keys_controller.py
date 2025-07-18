# Controller generated based on model fields.
import uuid
from typing import List

from fastapi import HTTPException, Request, Header, Depends
from swx_api.app.models.api_keys import (
    ApiKeysCreate,
    ApiKeysUpdate,
    ApiKeysRead,
    ApiKeysReadWithKey,
)
from swx_api.app.services.api_keys_service import ApiKeysService
from swx_api.core.database.db import SessionDep, get_db
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.utils.language_helper import translate


class ApiKeysController:

    @staticmethod
    async def get_valid_api_key(
            db: SessionDep,
            api_key: str = Header(..., description="API Key")
    ) -> None:
        """
        Dependency: validate API key and raise if invalid.
        Returns nothing (or you could return True).
        """
        success, result = ApiKeysService.validate_and_increment_usage(db, api_key)

        if not success:
            logger.warning("API Key validation failed: %s", result)
            raise HTTPException(
                status_code=result["status"],
                detail={
                    "error": {
                        "code": result["status"],
                        "message": result["detail"]
                    }
                }
            )

    @staticmethod
    def list_api_keys(
            request: Request,
            db: SessionDep,
            skip: int = 0,
            limit: int = 100,
    ) -> List[ApiKeysRead]:
        """Retrieve all API keys with pagination."""
        try:
            return ApiKeysService.list_api_keys(db, skip=skip, limit=limit)
        except Exception as e:
            logger.error("Error in list_api_keys: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def get_api_key_by_id(
            request: Request,
            id: uuid.UUID,
            db: SessionDep,
    ) -> ApiKeysRead:
        """Retrieve a single API key by ID."""
        item = ApiKeysService.get_api_key_by_id(db, id)
        if not item:
            raise HTTPException(
                status_code=404,
                detail=translate(request, "api_keys.not_found"),
            )
        return item

    @staticmethod
    def create_api_key(
            request: Request,
            data: ApiKeysCreate,
            db: SessionDep,
    ) -> ApiKeysReadWithKey:
        """Create a new API key."""
        try:
            return ApiKeysService.create_api_key(db, data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in create_api_key: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def update_api_key(
            request: Request,
            id: uuid.UUID,
            data: ApiKeysUpdate,
            db: SessionDep,
    ) -> ApiKeysRead:
        """Update an existing API key."""
        item = ApiKeysService.update_api_key(db, id, data)
        if not item:
            raise HTTPException(
                status_code=404,
                detail=translate(request, "api_keys.not_found"),
            )
        return item

    @staticmethod
    def delete_api_key(
            request: Request,
            id: uuid.UUID,
            db: SessionDep,
    ) -> None:
        """Delete an API key."""
        success = ApiKeysService.delete_api_key(db, id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=translate(request, "api_keys.not_found"),
            )
        return None
