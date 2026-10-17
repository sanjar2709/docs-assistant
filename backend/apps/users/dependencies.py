from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.db import DBSession
from core.security import decode_token

from .models import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Not authenticated',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_token(credentials.credentials, 'access')
    if user_id is None:
        raise unauthorized
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user



CurrentUser = Annotated[User, Depends(get_current_user)]
