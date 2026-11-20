from fastapi import APIRouter, Depends, HTTPException
from app.database import get_conn
from app.schemas.usuarios import GetUsuarioOut
from app.services.usuarios import GetUsuarioById
from uuid import UUID

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.get("/{id}", response_model=GetUsuarioOut)
def listar(id: UUID, conn = Depends(get_conn)):
    data = GetUsuarioById(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return data