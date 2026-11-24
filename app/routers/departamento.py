from fastapi import APIRouter, Depends, HTTPException
from app.database import get_conn
from app.schemas.departamento import CrearDepartamentoIn, DepartamentoOut
from app.services.departamento import (
    crearDepartamento,
    inicializarDepartamentosBase,
    listarDepartamentos,
)

router = APIRouter(prefix="/departamento", tags=["departamentos"])


@router.get("/", response_model=list[DepartamentoOut])
def listar(conn=Depends(get_conn)):
    return listarDepartamentos(conn)


@router.post("/crear", response_model=DepartamentoOut)
def crear(body: CrearDepartamentoIn, conn=Depends(get_conn)):
    nuevo = crearDepartamento(body.nombre, conn)
    if not nuevo:
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el departamento (puede que ya exista ese nombre).",
        )
    return nuevo


@router.post("/seed", response_model=list[DepartamentoOut])
def poblar_base(conn=Depends(get_conn)):
    """Inserta los 5 departamentos institucionales definidos en el ERS."""
    return inicializarDepartamentosBase(conn)