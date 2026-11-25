from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
from uuid import UUID

class MensajeIn(BaseModel):
    mensaje: str = Field(min_length=3, max_length=1000)
    perfil: Literal["estudiante", "apoderado"] = "estudiante"
    version: str | None = Field(default=None, description="Versión del reglamento; vacío = vigentes")
    k: int = Field(default=6, ge=1, le=12)


class Fuente(BaseModel):
    version: str
    capitulo: str | None
    articulo: str | None
    pagina: int | None
    extracto: str
    score: float


class MensajeOut(BaseModel):
    consulta_id: UUID | None = None
    respuesta: str
    gravedad: str  # no_aplica | leve | grave | gravisima | indeterminada
    aviso: str | None  # texto fijo de "qué hacer ahora" (None si no corresponde)
    fuentes: list[Fuente]

class ConsultaOut(BaseModel): 
    user_id: UUID | None = None
    rol_usuario_id: int
    severidad: str | None = None
    detalles: str | None = None
    fecha_creacion: datetime

class ConsultaLogOut(BaseModel):
    id: UUID
    consulta_id: UUID
    mensaje: str | None = None
    adjunto: str | None = None
    respuesta: str | None = None
    fecha_creacion: datetime