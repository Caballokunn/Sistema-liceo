from uuid import UUID
from psycopg import Connection


def _formatearFolio(caso_id: int, fecha_creacion) -> str:
    anio = fecha_creacion.year if fecha_creacion else 2026
    return f"CASO-{anio}-{caso_id:04d}"


def crearCaso(datos: dict, conn: Connection) -> dict | None:
    participantes = datos.pop("participantes", [])
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO casos (
                    departamento_id, encargado_id, tipo_caso,
                    titulo, descripcion, prioridad, estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'Nuevo')
                RETURNING id, departamento_id, encargado_id, tipo_caso,
                          titulo, descripcion, prioridad, estado, fecha_creacion
                """,
                (
                    datos["departamento_id"],
                    datos.get("encargado_id"),
                    datos["tipo_caso"],
                    datos["titulo"],
                    datos.get("descripcion"),
                    datos.get("prioridad", "media"),
                ),
            )
            caso = cur.fetchone()
            if not caso:
                conn.rollback()
                return None

            for p in participantes:
                cur.execute(
                    """
                    INSERT INTO caso_participantes (caso_id, usuario_id, rol_en_caso)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (caso_id, usuario_id)
                    DO UPDATE SET rol_en_caso = EXCLUDED.rol_en_caso
                    """,
                    (caso["id"], p["usuario_id"], p.get("rol_en_caso")),
                )

        conn.commit()
        return obtenerCasoPorId(caso["id"], conn)
    except Exception:
        conn.rollback()
        return None


def listarCasos(
    conn: Connection,
    estado: str | None = None,
    departamento_id: int | None = None,
    encargado_id: UUID | None = None,
) -> list[dict]:
    filtros = []
    params = []

    if estado:
        filtros.append("c.estado = %s")
        params.append(estado)
    if departamento_id:
        filtros.append("c.departamento_id = %s")
        params.append(departamento_id)
    if encargado_id:
        filtros.append("c.encargado_id = %s")
        params.append(encargado_id)

    where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                c.id,
                c.departamento_id,
                d.nombre AS departamento_nombre,
                c.encargado_id,
                CONCAT_WS(' ', u.nombre, u.apellido1) AS encargado_nombre,
                c.tipo_caso,
                c.titulo,
                c.descripcion,
                c.prioridad,
                c.estado,
                c.fecha_creacion
            FROM casos c
            LEFT JOIN departamentos d ON d.id = c.departamento_id
            LEFT JOIN usuarios u ON u.id = c.encargado_id
            {where_sql}
            ORDER BY c.fecha_creacion DESC
            """,
            params,
        )
        filas = cur.fetchall()

    for f in filas:
        f["folio"] = _formatearFolio(f["id"], f["fecha_creacion"])
        f["participantes"] = []
    return filas


def obtenerCasoPorId(caso_id: int, conn: Connection) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.departamento_id,
                d.nombre AS departamento_nombre,
                c.encargado_id,
                CONCAT_WS(' ', u.nombre, u.apellido1) AS encargado_nombre,
                c.tipo_caso,
                c.titulo,
                c.descripcion,
                c.prioridad,
                c.estado,
                c.fecha_creacion
            FROM casos c
            LEFT JOIN departamentos d ON d.id = c.departamento_id
            LEFT JOIN usuarios u ON u.id = c.encargado_id
            WHERE c.id = %s
            """,
            (caso_id,),
        )
        caso = cur.fetchone()
        if not caso:
            return None

        cur.execute(
            """
            SELECT
                cp.usuario_id,
                u.nombre,
                u.apellido1,
                u.rut,
                cp.rol_en_caso
            FROM caso_participantes cp
            JOIN usuarios u ON u.id = cp.usuario_id
            WHERE cp.caso_id = %s
            """,
            (caso_id,),
        )
        caso["participantes"] = cur.fetchall()

    caso["folio"] = _formatearFolio(caso["id"], caso["fecha_creacion"])
    return caso


def actualizarCaso(caso_id: int, datos: dict, conn: Connection) -> bool:
    campos = {k: v for k, v in datos.items() if v is not None}
    if not campos:
        return False

    set_sql = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [caso_id]

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE casos SET {set_sql} WHERE id = %s RETURNING id",
                valores,
            )
            actualizado = cur.fetchone() is not None
        conn.commit()
        return actualizado
    except Exception:
        conn.rollback()
        return False


def cambiarEstadoCaso(caso_id: int, nuevo_estado: str, conn: Connection) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE casos SET estado = %s WHERE id = %s RETURNING id",
                (nuevo_estado, caso_id),
            )
            actualizado = cur.fetchone() is not None
        conn.commit()
        return actualizado
    except Exception:
        conn.rollback()
        return False


def derivarCaso(
    caso_id: int,
    departamento_destino_id: int,
    encargado_destino_id: UUID | None,
    instrucciones: str,
    conn: Connection,
) -> tuple[bool, str]:
    """RF-06: Solo permite derivar casos que estén 'En Proceso'."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT estado, descripcion FROM casos WHERE id = %s", (caso_id,))
            caso = cur.fetchone()
            if not caso:
                return False, "Caso no encontrado"
            if caso["estado"] != "En Proceso":
                return False, "Solo se pueden derivar casos en estado 'En Proceso'"

            nueva_desc = (
                f"{caso['descripcion'] or ''}\n\n"
                f"[DERIVACIÓN a Depto. {departamento_destino_id}]: {instrucciones}"
            ).strip()

            cur.execute(
                """
                UPDATE casos
                SET departamento_id = %s,
                    encargado_id = %s,
                    descripcion = %s
                WHERE id = %s
                """,
                (departamento_destino_id, encargado_destino_id, nueva_desc, caso_id),
            )
        conn.commit()
        return True, "Caso derivado exitosamente"
    except Exception as e:
        conn.rollback()
        return False, f"Error al derivar el caso: {str(e)}"


def agregarParticipante(caso_id: int, usuario_id: UUID, rol_en_caso: str, conn: Connection) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO caso_participantes (caso_id, usuario_id, rol_en_caso)
                VALUES (%s, %s, %s)
                ON CONFLICT (caso_id, usuario_id)
                DO UPDATE SET rol_en_caso = EXCLUDED.rol_en_caso
                RETURNING caso_id
                """,
                (caso_id, usuario_id, rol_en_caso),
            )
            ok = cur.fetchone() is not None
        conn.commit()
        return ok
    except Exception:
        conn.rollback()
        return False