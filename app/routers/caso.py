from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_conn
from app.services.auth import get_current_user
from app.schemas.caso import (
    ActualizarCasoIn,
    CambiarEstadoCasoIn,
    CrearCasoIn,
    DerivarCasoIn,
    EstadoCaso,
    ObtenerCasoOut,
    ParticipanteCasoIn,
)
from app.services.caso import (
    actualizarCaso,
    agregarParticipante,
    cambiarEstadoCaso,
    crearCaso,
    derivarCaso,
    listarCasos,
    obtenerCasoPorId,
)

router = APIRouter(
    prefix="/caso",
    tags=["casos"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[ObtenerCasoOut])
def listar(
    estado: Optional[EstadoCaso] = Query(None),
    departamento_id: Optional[int] = Query(None),
    encargado_id: Optional[UUID] = Query(None),
    conn=Depends(get_conn),
):
    return listarCasos(conn, estado=estado, departamento_id=departamento_id, encargado_id=encargado_id)


@router.get("/{id}", response_model=ObtenerCasoOut)
def obtener(id: int, conn=Depends(get_conn)):
    data = obtenerCasoPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return data


@router.post("/crear", response_model=ObtenerCasoOut)
def crear(caso: CrearCasoIn, conn=Depends(get_conn)):
    nuevo = crearCaso(caso.model_dump(), conn)
    if not nuevo:
        raise HTTPException(
            status_code=400,
            detail="Error al crear el caso. Verifica que departamento_id y los usuarios existan.",
        )
    return nuevo


@router.patch("/actualizar/{id}", response_model=str)
def actualizar(id: int, caso: ActualizarCasoIn, conn=Depends(get_conn)):
    status = actualizarCaso(id, caso.model_dump(), conn)
    if not status:
        raise HTTPException(status_code=400, detail="Error al actualizar el caso o sin cambios")
    return "Caso actualizado exitosamente"


@router.patch("/{id}/estado", response_model=str)
def cambiar_estado(id: int, body: CambiarEstadoCasoIn, conn=Depends(get_conn)):
    status = cambiarEstadoCaso(id, body.estado, conn)
    if not status:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return f"Estado actualizado a '{body.estado}'"


@router.post("/{id}/derivar", response_model=str)
def derivar(id: int, body: DerivarCasoIn, conn=Depends(get_conn)):
    ok, mensaje = derivarCaso(
        caso_id=id,
        departamento_destino_id=body.departamento_destino_id,
        encargado_destino_id=body.encargado_destino_id,
        instrucciones=body.instrucciones,
        conn=conn,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=mensaje)
    return mensaje


@router.post("/{id}/participantes", response_model=str)
def vincular_participante(id: int, participante: ParticipanteCasoIn, conn=Depends(get_conn)):
    ok = agregarParticipante(id, participante.usuario_id, participante.rol_en_caso, conn)
    if not ok:
        raise HTTPException(status_code=400, detail="Error al agregar participante al caso")
    return "Participante vinculado exitosamente"