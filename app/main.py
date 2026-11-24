from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import pool
<<<<<<< Updated upstream
from app.routers import caso, consulta, usuario
=======
from app.routers import consulta, rol, usuario
>>>>>>> Stashed changes

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)
app.include_router(usuario.router)
<<<<<<< Updated upstream
app.include_router(consulta.router)
app.include_router(caso.router)
=======
app.include_router(rol.router)
app.include_router(consulta.router)
>>>>>>> Stashed changes
