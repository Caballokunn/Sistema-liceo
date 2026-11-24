from psycopg import Connection


def listarDepartamentos(conn: Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre FROM departamentos ORDER BY id ASC")
        return cur.fetchall()


def crearDepartamento(nombre: str, conn: Connection) -> dict | None:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO departamentos (nombre)
                VALUES (%s)
                ON CONFLICT (nombre) DO NOTHING
                RETURNING id, nombre
                """,
                (nombre.strip(),),
            )
            depto = cur.fetchone()
        conn.commit()
        return depto
    except Exception:
        conn.rollback()
        return None


def inicializarDepartamentosBase(conn: Connection) -> list[dict]:
    """Carga los departamentos oficiales del ERS (RF-06) si no existen."""
    unidades = [
        "Convivencia Escolar",
        "Unidad Técnico Pedagógica (UTP)",
        "Inspectoría General",
        "Orientación",
        "Programa de Integración Escolar (PIE)",
    ]
    try:
        with conn.cursor() as cur:
            for nombre in unidades:
                cur.execute(
                    "INSERT INTO departamentos (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING",
                    (nombre,),
                )
        conn.commit()
        return listarDepartamentos(conn)
    except Exception:
        conn.rollback()
        return []