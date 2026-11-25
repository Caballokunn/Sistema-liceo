from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_conn
from app.services.auth import get_current_user_optional
from app.services.consulta import (
    ConsultaNoEncontrada,
    LLMNoDisponible,
    continuarConsulta,
    crearConsultaConMensaje,
    obtenerConsultaPorId,
    obtenerLogs,
)
from app.schemas.consulta import ConsultaLogOut, ConsultaOut, MensajeIn, MensajeOut

router = APIRouter(prefix="/consulta", tags=["consulta"])


def _usuario_id(usuario: dict | None):
    return UUID(usuario["id"]) if usuario else None


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/mensaje", response_model=MensajeOut)
def iniciar_sesion(
    body: MensajeIn,
    conn=Depends(get_conn),
    usuario=Depends(get_current_user_optional),
):
    """Crea una sesión de consulta, con o sin usuario autenticado."""
    try:
        return crearConsultaConMensaje(
            usuario_id=_usuario_id(usuario),
            mensaje=body.mensaje,
            conn=conn,
            perfil=body.perfil,
            version=body.version,
            k=body.k,
        )
    except LLMNoDisponible as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{id}/mensaje", response_model=MensajeOut)
def continuar_sesion(
    id: UUID,
    body: MensajeIn,
    conn=Depends(get_conn),
    usuario=Depends(get_current_user_optional),
):
    """Agrega un mensaje a una sesión existente y usa los anteriores como contexto."""
    try:
        return continuarConsulta(
            consulta_id=id,
            usuario_id=_usuario_id(usuario),
            mensaje=body.mensaje,
            conn=conn,
            perfil=body.perfil,
            version=body.version,
            k=body.k,
        )
    except ConsultaNoEncontrada as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMNoDisponible as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{id}/logs", response_model=list[ConsultaLogOut])
def logs(
    id: UUID,
    conn=Depends(get_conn),
    usuario=Depends(get_current_user_optional),
):
    """Historial completo de mensajes y respuestas de una sesión."""
    try:
        return obtenerLogs(id, _usuario_id(usuario), conn)
    except ConsultaNoEncontrada as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{id}", response_model=ConsultaOut)
def obtener_consulta(
    id: UUID,
    conn=Depends(get_conn),
    usuario=Depends(get_current_user_optional),
):
    data = obtenerConsultaPorId(id, conn, _usuario_id(usuario))
    if not data:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return data
