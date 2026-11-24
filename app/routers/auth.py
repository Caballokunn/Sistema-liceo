from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_conn
from app.schemas.usuarios import LoginIn, TokenOut
from app.services.auth import autenticar, crear_access_token


router = APIRouter(prefix="/auth", tags=["autenticacion"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, conn=Depends(get_conn)):
    usuario = autenticar(body.correo, body.contrasena, conn)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenOut(
        access_token=crear_access_token(str(usuario["id"]), usuario["rol"]),
    )
