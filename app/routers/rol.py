from fastapi import APIRouter, Depends, HTTPException
from app.database import get_conn
from app.schemas.rol import ObtenerRolOut, CrearRolIn
from app.services.auth import get_current_user
from app.services.rol import obtenerRoles, obtenerRolPorId, crearRol, actualizarRol, eliminarRol

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_user)],
)

@router.get("", response_model=list[ObtenerRolOut])
def listar(conn = Depends(get_conn)):
    data = obtenerRoles(conn)
    if data is None:
        raise HTTPException(status_code=500, detail="Error al obtener los roles")
    return data

@router.get("/{id}", response_model=ObtenerRolOut)
def obtener(id: int, conn = Depends(get_conn)):
    data = obtenerRolPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return data

@router.post("/crear", response_model=str)
def crear(rol: CrearRolIn, conn = Depends(get_conn)):
    status = crearRol(rol.dict(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al crear el rol")
    return 'Rol creado exitosamente'

@router.patch("/actualizar/{id}", response_model=str)
def actualizar(id: int, rol: CrearRolIn, conn = Depends(get_conn)):
    status = actualizarRol(id, rol.dict(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al actualizar el rol")
    return 'Rol actualizado exitosamente'

@router.delete("/eliminar/{id}", response_model=str)
def eliminar(id: int, conn = Depends(get_conn)):
    status = eliminarRol(id, conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al eliminar el rol")
    return 'Rol eliminado exitosamente'
