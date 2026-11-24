from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import pool
from app.routers import caso, consulta, usuario
from app.routers import consulta, rol, usuario
from app.routers import auth, caso, consulta, rol, usuario
from app.routers import caso, consulta, departamento, usuario

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(usuario.router)
app.include_router(consulta.router)
app.include_router(caso.router)
app.include_router(rol.router)
app.include_router(consulta.router)
app.include_router(departamento.router)