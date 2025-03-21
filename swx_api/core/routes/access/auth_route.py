"""
Authentication Routes
----------------------
This module defines the API routes for authentication-related operations.

Features:
- User login (local authentication).
- Token refresh for authentication renewal.
- User registration.
- User logout (revoking refresh tokens).
- Password recovery and reset.

Methods:
- `login()`: Handles user login.
- `refresh_token()`: Generates a new access token using a refresh token.
- `register()`: Registers a new user.
- `logout()`: Revokes the user's refresh token.
- `recover_password()`: Sends a password reset email.
- `reset_password()`: Resets a user's password and revokes active tokens.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from swx_api.core.controllers.auth_controller import (
    login_controller,
    logout_controller,
    refresh_token_controller,
    recover_password_controller,
    reset_password_controller,
    register_controller,
)
from swx_api.core.database.db import SessionDep
from swx_api.core.models.common import Message
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.models.user import UserCreate, UserNewPassword, UserPublic

# Initialize API router with a prefix for authentication-related endpoints
router = APIRouter(prefix="/auth")


@router.post("/", response_model=Token)
def login(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
) -> Token:
    """
    Handles user login.

    Args:
        session: The database session.
        form_data (OAuth2PasswordRequestForm): The login form containing username and password.
        request (Request, optional): The HTTP request object.

    Returns:
        Token: A dictionary containing the access token, refresh token, and token type.
    """
    return login_controller(session, form_data, request)


@router.post("/refresh", response_model=Token)
def refresh_token(
    session: SessionDep, request_data: TokenRefreshRequest, request: Request
) -> Token:
    """
    Generates a new access token using a refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token request data.
        request (Request): The HTTP request object.

    Returns:
        Token: A dictionary containing the new access token, refresh token, and token type.
    """
    return refresh_token_controller(session, request_data, request)


@router.post("/register", response_model=UserPublic, operation_id="register_new_user")
def register(session: SessionDep, user_in: UserCreate, request: Request):
    """
    Registers a new user.

    Args:
        session: The database session.
        user_in (UserCreate): The user registration data.
        request (Request): The HTTP request object.

    Returns:
        UserPublic: The newly created user.
    """
    return register_controller(session, user_in, request)


@router.post("/revoke")
def logout(session: SessionDep, request_data: TokenRefreshRequest, request: Request):
    """
    Logs out the user by revoking their refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token to revoke.
        request (Request): The HTTP request object.

    Returns:
        dict: A message indicating successful logout.
    """
    return logout_controller(session, request_data, request)


@router.post("/password/recover/{email}", response_model=Message)
def recover_password(email: str, session: SessionDep, request: Request = None):
    """
    Sends a password reset email to the user.

    Args:
        email (str): The user's email address.
        session: The database session.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A response indicating that the reset email has been sent.
    """
    return recover_password_controller(email, session, request)


@router.post("/password/reset", response_model=Message)
def reset_password(session: SessionDep, body: UserNewPassword, request: Request = None):
    """
    Resets the user's password and revokes all active tokens.

    Args:
        session: The database session.
        body (UserNewPassword): The password reset request data.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A success message indicating that the password has been reset.
    """
    return reset_password_controller(session, body, request)
