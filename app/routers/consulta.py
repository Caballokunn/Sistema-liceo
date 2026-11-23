import secrets

from fastapi import APIRouter, Depends, Header, HTTPException

import app.config as config
from app.database import get_conn
from app.services.consulta import enviarMensaje, LLMNoDisponible, obtenerConsultaPorId
from app.schemas.consulta import MensajeIn, MensajeOut, Fuente


def check_key(x_api_key: str = Header(...)):
    if not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(status_code=401, detail="API key inválida")

router = APIRouter(prefix="/consulta", tags=["consulta"])

@router.get("/health")
def health():
    return {"ok": True}

# Endpoint síncrono (def): FastAPI lo ejecuta en un threadpool, así no bloquea el event loop.
@router.post("/consultar", response_model=MensajeOut, dependencies=[Depends(check_key)])
def consultar(body: MensajeIn):
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

@router.post("/{id}", response_model=MensajeOut)
def obtener_consulta(id: str, conn = Depends(get_conn)):
    data = obtenerConsultaPorId(id, conn)
    if not data:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return MensajeOut(respuesta=data["respuesta"], fuentes=data["fuentes"])