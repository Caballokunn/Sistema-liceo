from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

EstadoCaso = Literal["Nuevo", "En Revisión", "En Proceso", "Cerrado"]
PrioridadCaso = Literal["baja", "media", "alta", "critica"]


class ParticipanteCasoIn(BaseModel):
    usuario_id: UUID
    rol_en_caso: str = Field(..., max_length=50, examples=["estudiante_afectado", "apoderado", "denunciante"])


class ParticipanteCasoOut(BaseModel):
    usuario_id: UUID
    nombre: str
    apellido1: str
    rut: str
    rol_en_caso: Optional[str] = None


class CrearCasoIn(BaseModel):
    departamento_id: int
    encargado_id: Optional[UUID] = None
    tipo_caso: str = Field(..., max_length=50, examples=["Convivencia", "Ciberacoso", "Disciplinario"])
    titulo: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    prioridad: PrioridadCaso = "media"
    participantes: list[ParticipanteCasoIn] = []


class ActualizarCasoIn(BaseModel):
    departamento_id: Optional[int] = None
    encargado_id: Optional[UUID] = None
    tipo_caso: Optional[str] = Field(None, max_length=50)
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    prioridad: Optional[PrioridadCaso] = None


class CambiarEstadoCasoIn(BaseModel):
    estado: EstadoCaso
    observacion: Optional[str] = None


class DerivarCasoIn(BaseModel):
    departamento_destino_id: int
    encargado_destino_id: Optional[UUID] = None
    instrucciones: str = Field(..., min_length=5)


class ObtenerCasoOut(BaseModel):
    id: int
    folio: str
    departamento_id: int
    departamento_nombre: Optional[str] = None
    encargado_id: Optional[UUID] = None
    encargado_nombre: Optional[str] = None
    tipo_caso: str
    titulo: str
    descripcion: Optional[str] = None
    prioridad: str
    estado: str
    fecha_creacion: datetime
    participantes: list[ParticipanteCasoOut] = []