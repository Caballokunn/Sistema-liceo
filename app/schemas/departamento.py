from pydantic import BaseModel, Field


class CrearDepartamentoIn(BaseModel):
    nombre: str = Field(..., max_length=150, examples=["Convivencia Escolar"])


class DepartamentoOut(BaseModel):
    id: int
    nombre: str