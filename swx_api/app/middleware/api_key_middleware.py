from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from swx_api.app.controllers.api_keys_controller import ApiKeysController
from fastapi import HTTPException

from swx_api.core.database.db import get_db


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication.
    """
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("x_api_key")
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
                content=e.detail
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


