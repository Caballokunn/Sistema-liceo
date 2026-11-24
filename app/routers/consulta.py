from fastapi import APIRouter, Depends, HTTPException

from app.database import get_conn
from app.services.consulta import enviarMensaje, LLMNoDisponible, obtenerConsultaPorId
from app.schemas.consulta import ConsultaOut, MensajeIn, MensajeOut, Fuente
from app.services.auth import get_current_user
from uuid import UUID

router = APIRouter(prefix="/consulta", tags=["consulta"])

@router.get("/health")
def health():
    return {"ok": True}

# Endpoint síncrono (def): FastAPI lo ejecuta en un threadpool, así no bloquea el event loop.
@router.post("/consultar", response_model=MensajeOut)
def consultar(body: MensajeIn, _usuario=Depends(get_current_user)):
    try:
        resultado = enviarMensaje(
            pregunta=body.mensaje,
            perfil=body.perfil,
            version=body.version,
            k=body.k,
        )
    except LLMNoDisponible as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return MensajeOut(
        respuesta=resultado.respuesta,
        gravedad=resultado.gravedad,
        aviso=resultado.aviso,
        fuentes=[Fuente(**vars(f)) for f in resultado.fuentes],
    )

@router.get("/{id}", response_model=ConsultaOut)
def obtener_consulta(id: UUID, conn=Depends(get_conn), _usuario=Depends(get_current_user)):
    data = obtenerConsultaPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return data