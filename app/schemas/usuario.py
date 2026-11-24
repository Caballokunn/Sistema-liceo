from pydantic import BaseModel
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
    rol: int          
    departamento: int | None = None     
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    contrasenia: str
    fecha_nacimiento: date