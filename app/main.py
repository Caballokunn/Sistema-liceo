from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)
#app.include_router(usuarios.router)