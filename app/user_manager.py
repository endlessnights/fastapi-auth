# app/user_manager.py

import jwt
import logging
from fastapi import HTTPException, Request
from starlette import status

from app.config import (
    SECRET_KEY,
    ALGORITHM,
)
from app.models import User
from tortoise.exceptions import DoesNotExist

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        logger.warning("Access token cookie not found")
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # Split the token to remove the "Bearer " prefix
        scheme, token = token.split(" ")
        if scheme.lower() != "bearer":
            logger.warning(f"Invalid auth scheme: {scheme}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            logger.warning("Username not found in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Fetch the User instance from the database with groups
        user = await User.get(username=username).prefetch_related("groups")
        logger.info(f"Authenticated user: {user.username}")
        return user
    except (jwt.PyJWTError, ValueError) as e:
        logger.error(f"Error decoding JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DoesNotExist:
        logger.error(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
