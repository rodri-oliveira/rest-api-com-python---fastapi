from database.connection import db
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from utils.security import SECRET_KEY, ALGORITHM
from models.usuario_model import Usuario


# Esquemas HTTP Bearer para o Swagger mostrar campo de colar token
http_bearer_access = HTTPBearer(scheme_name="AccessToken")
http_bearer_refresh = HTTPBearer(scheme_name="RefreshToken")


def get_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_payload(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.", headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer_access),
    session: Session = Depends(get_session),
):
    payload = get_token_payload(token.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.", headers={"WWW-Authenticate": "Bearer"})

    user_id = payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.", headers={"WWW-Authenticate": "Bearer"})

    usuario = session.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado.", headers={"WWW-Authenticate": "Bearer"})
    if not usuario.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inativo.", headers={"WWW-Authenticate": "Bearer"})
    return usuario


def verify_refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.", headers={"WWW-Authenticate": "Bearer"})
    return payload


def verify_refresh_bearer(token: HTTPAuthorizationCredentials = Depends(http_bearer_refresh)):
    """Valida refresh token lido do header Authorization: Bearer."""
    payload = verify_token(token.credentials)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.", headers={"WWW-Authenticate": "Bearer"})
    return payload