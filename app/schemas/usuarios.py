from pydantic import BaseModel
from datetime import date

class GetUsuarioOut(BaseModel):
    rol: str | None = None
    departamento: str | None = None     
    nombre: str          
    apellido1: str          
    apellido2: str | None = None
    rut: str          
    correo: str | None = None
    fecha_nacimiento: date
    