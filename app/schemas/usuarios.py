from pydantic import BaseModel
from datetime import date

class ObtenerUsuarioOut(BaseModel):
    rol: str | None = None
    departamento: str | None = None     
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    fecha_nacimiento: date

class CrearUsuarioIn(BaseModel):
    rol: int | None = None          
    departamento: int | None = None     
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    fecha_nacimiento: date