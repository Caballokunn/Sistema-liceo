from pydantic import BaseModel, Field
from datetime import date

class ObtenerUsuarioOut(BaseModel):
    rol: str
    departamento: str | None = None     
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    fecha_nacimiento: date

class CrearUsuarioIn(BaseModel):
    rol_id: int
    departamento_id: int
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    fecha_nacimiento: date
    contrasena: str = Field(min_length=8, max_length=72)


class ActualizarUsuarioIn(BaseModel):
    rol_id: int | None = None
    departamento_id: int | None = None
    nombre: str | None = None
    apellido1: str | None = None
    apellido2: str | None = None
    rut: str | None = None
    correo: str | None = None
    fecha_nacimiento: date | None = None
    contrasena: str | None = Field(default=None, min_length=8, max_length=72)


class LoginIn(BaseModel):
    correo: str
    contrasena: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
