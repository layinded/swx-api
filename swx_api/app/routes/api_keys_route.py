# Route generated based on controller and model.
import uuid
from datetime import timedelta, timezone, datetime
from typing import List

from fastapi import APIRouter, Request, Depends, Query, status
from swx_api.core.database.db import SessionDep
from swx_api.app.controllers.api_keys_controller import ApiKeysController
from swx_api.app.models.api_keys import (
    ApiKeysCreate,
    ApiKeysUpdate,
    ApiKeysRead,
    ApiKeysReadWithKey,
    ApiKeys,
)
from swx_api.core.security.dependencies import CurrentUser, AdminUser

router = APIRouter(
    prefix="/user/api_keys"
)


@router.get(
    "/",
    response_model=List[ApiKeysRead],
    summary="List API Keys",
    description="Retrieve all API keys with optional pagination."
)
def list_api_keys(
        request: Request,
        db: SessionDep,
        current_user: AdminUser,
        skip: int = Query(0, description="Number of items to skip"),
        limit: int = Query(100, description="Maximum number of items to return"),
):
    return ApiKeysController.list_api_keys(request, db, skip=skip, limit=limit)


@router.get(
    "/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate API Key",
    description="Validate an API key from the X-API-Key header and return the API key info."
)
def validate_api_key(
        _: None = Depends(ApiKeysController.get_valid_api_key)):
    return


@router.get(
    "/{id}",
    response_model=ApiKeysRead,
    summary="Get API Key by ID",
    description="Retrieve a single API key record by UUID."
)
def get_api_key_by_id(
        request: Request,
        id: uuid.UUID,
        db: SessionDep,
        current_user: AdminUser,
):
    return ApiKeysController.get_api_key_by_id(request, id, db)


@router.post(
    "/",
    response_model=ApiKeysReadWithKey,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="Create a new API key record."
)
def create_api_key(
        request: Request,
        data: ApiKeysCreate,
        db: SessionDep,
        current_user: CurrentUser,
):

    data.user_id = current_user.id
    return ApiKeysController.create_api_key(request, data, db)


@router.put(
    "/{id}",
    response_model=ApiKeysRead,
    summary="Update API Key",
    description="Update an existing API key record by UUID."
)
def update_api_key(
        request: Request,
        id: uuid.UUID,
        data: ApiKeysUpdate,
        db: SessionDep,
        current_user: AdminUser,
):
    return ApiKeysController.update_api_key(request, id, data, db)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API Key",
    description="Delete an API key record by UUID."
)
def delete_api_key(
        request: Request,
        id: uuid.UUID,
        db: SessionDep,
        current_user: CurrentUser,
):
    ApiKeysController.delete_api_key(request, id, db)
