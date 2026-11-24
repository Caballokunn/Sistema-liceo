from fastapi import APIRouter, Depends, HTTPException
from app.database import get_conn
from app.schemas.usuario import (
    ObtenerUsuarioOut,
    CrearUsuarioIn,
    ActualizarUsuarioIn,
)
from app.services.auth import get_current_user
from app.services.usuario import obtenerUsuarioPorId, crearUsuario, actualizarUsuario, eliminarUsuario
from uuid import UUID

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.get("/{id}", response_model=ObtenerUsuarioOut)
def obtener(id: UUID, conn=Depends(get_conn), _usuario=Depends(get_current_user)):
    data = obtenerUsuarioPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return data

@router.post("/crear", response_model=str)
def crear(usuario: CrearUsuarioIn, conn=Depends(get_conn), _usuario=Depends(get_current_user)):
    status = crearUsuario(usuario.model_dump(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al crear el usuario")
    return 'Usuario creado exitosamente'

@router.patch("/actualizar/{id}", response_model=str)
def actualizar(id: UUID, usuario: ActualizarUsuarioIn, conn=Depends(get_conn), _usuario=Depends(get_current_user)):
    status = actualizarUsuario(id, usuario.model_dump(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al actualizar el usuario")
    return 'Usuario actualizado exitosamente'

@router.delete("/eliminar/{id}", response_model=str)
def eliminar(id: UUID, conn=Depends(get_conn), _usuario=Depends(get_current_user)):
    status = eliminarUsuario(id, conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al eliminar el usuario")
    return 'Usuario eliminado exitosamente'