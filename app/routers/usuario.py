from fastapi import APIRouter, Depends, HTTPException
from app.database import get_conn
from app.schemas.usuarios import ObtenerUsuarioOut, CrearUsuarioIn
from app.services.usuario import obtenerUsuarioPorId, crearUsuario, actualizarUsuario, eliminarUsuario
from uuid import UUID

router = APIRouter(prefix="/usuario", tags=["usuarios"])

@router.get("/{id}", response_model=ObtenerUsuarioOut)
def obtener(id: UUID, conn = Depends(get_conn)):
    data = obtenerUsuarioPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return data

@router.post("/crear", response_model=str)
def crear(usuario: CrearUsuarioIn, conn = Depends(get_conn)):
    status = crearUsuario(usuario.dict(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al crear el usuario")
    return 'Usuario creado exitosamente'

@router.patch("/actualizar/{id}", response_model=str)
def actualizar(id: UUID, usuario: CrearUsuarioIn, conn = Depends(get_conn)):
    status = actualizarUsuario(id, usuario.dict(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al actualizar el usuario")
    return 'Usuario actualizado exitosamente'

@router.delete("/eliminar/{id}", response_model=str)
def eliminar(id: UUID, conn = Depends(get_conn)):
    status = eliminarUsuario(id, conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al eliminar el usuario")
    return 'Usuario eliminado exitosamente'