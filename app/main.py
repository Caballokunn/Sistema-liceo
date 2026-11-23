from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import pool
from app.routers import consulta, usuario

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)
app.include_router(usuario.router)
app.include_router(consulta.router)