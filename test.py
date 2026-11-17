from app.database import pool

pool.open()

with pool.connection() as conn:
    print(conn.execute("SELECT 1 AS ok").fetchone())      # {'ok': 1}
    print(conn.execute("SELECT version()").fetchone())

pool.close()