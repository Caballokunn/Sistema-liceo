from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import app.config as config


bearer = HTTPBearer(auto_error=False)


def verificar_contrasena(contrasena: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(contrasena.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def crear_access_token(usuario_id: str, rol: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def autenticar(correo: str, contrasena: str, conn) -> dict | None:
    usuario = conn.execute(
        """SELECT u.id, u.contrasenia, r.nombre AS rol
           FROM usuarios u
           JOIN roles r ON r.id = u.rol_id
           WHERE u.correo = %s""",
        (correo,),
    ).fetchone()
    if not usuario or not verificar_contrasena(contrasena, usuario["contrasenia"]):
        return None
    return usuario


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict | None:
    """Devuelve el usuario del token o None si la petición es anónima."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
        )
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise jwt.InvalidTokenError
        return {"id": usuario_id, "rol": payload.get("rol")}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    usuario = get_current_user_optional(credentials)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales requeridas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario

