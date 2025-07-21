from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from swx_api.app.controllers.api_keys_controller import ApiKeysController
from swx_api.core.database.db import get_db
from swx_api.core.utils.helper import extract_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            api_key = extract_api_key(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": {"code": e.status_code, "message": e.detail}}
            )

        if not api_key:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": 400, "message": "Missing API Key"}}
            )

        db_gen = get_db()
        db = next(db_gen)
        try:
            await ApiKeysController.get_valid_api_key(
                db=db,
                api_key=api_key
            )
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": {"code": e.status_code, "message": e.detail}}
            )
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": 401, "message": "Unauthorized"}}
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        return await call_next(request)
