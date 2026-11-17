import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

load_dotenv()

pool = ConnectionPool(
    conninfo=os.environ["DB_URL"],
    min_size=1,
    max_size=5,  # el pooler ya reparte conexiones, no necesitas muchas
    kwargs={
        "row_factory": dict_row,
        "prepare_threshold": None,  # desactiva prepared statements
    },
    open=False,
)

def get_conn():
    with pool.connection() as conn:
        yield conn