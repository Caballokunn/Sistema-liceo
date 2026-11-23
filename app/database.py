import os
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

load_dotenv()

pool = ConnectionPool(
    conninfo=os.environ["DB_URL"],
    min_size=1,
    max_size=5, 
    kwargs={
        "row_factory": dict_row,
        "prepare_threshold": None
    },
    open=False,
    configure=register_vector
)

def get_conn():
    with pool.connection() as conn:
        yield conn

def buscar_articulos(numeros: list[int], por_articulo: int = 1, version: str | None = None) -> list[dict]:
    """Trae las primeras partes de artículos concretos (p. ej. el 30° y el protocolo del tema detectado)."""
    out: list[dict] = []
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        for n in numeros:
            cur.execute(
                """select id, version, capitulo, articulo, parte, pagina, contenido, 0.0::float8 as score
                   from reglamento_chunks
                   where vigente and (%s::text is null or version = %s)
                     and articulo ~ %s
                   order by parte
                   limit %s""",
                (version, version, rf"^Artículo {n}([^0-9]|$)", por_articulo),
            )
            out.extend(cur.fetchall())
    return out

def buscar(query: str, embedding: list[float], k: int = 6, version: str | None = None) -> list[dict]:
    """Búsqueda híbrida (función SQL buscar_hibrido)."""
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "select * from buscar_hibrido(%s, %s, %s, %s)",
            (query, Vector(embedding), k, version),
        )
        return cur.fetchall()