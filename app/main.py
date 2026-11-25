from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import pool
from app.routers import auth, caso, consulta, departamento, rol, usuario

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(usuario.router)
app.include_router(rol.router)
app.include_router(departamento.router)
app.include_router(caso.router)
app.include_router(consulta.router)
