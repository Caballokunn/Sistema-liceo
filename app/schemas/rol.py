from pydantic import BaseModel, Field

class ObtenerRolOut(BaseModel):
    id: int
    nombre: str

class CrearRolIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
