from uuid import UUID

import app.database as db
import app.services.llm as llm
import app.services.seguridad as seguridad
from app.services.embeddings import embed_query
from app.schemas.consulta import MensajeOut, Fuente


class LLMNoDisponible(RuntimeError):
    """Ningún backend del LLM pudo generar una respuesta."""


class ConsultaNoEncontrada(LookupError):
    """La consulta no existe o no pertenece al usuario."""


# Cantidad de turnos previos que se envían al modelo como contexto de la conversación.
MAX_HISTORIAL = 10


def enviarMensaje(pregunta: str, perfil: str = "estudiante", version: str | None = None,
              k: int = 6, historial: list[dict] | None = None) -> MensajeOut:
    det = seguridad.detectar(pregunta)

    # Artículo 30° (criterios de gravedad) y protocolo del tema detectado: se fuerzan, no dependen de la búsqueda.
    forzados = db.buscar_articulos([30] + det.articulos[:2], por_articulo=1, version=version)
    encontrados = db.buscar(pregunta, embed_query(pregunta), k, version)
    vistos: set[int] = set()
    chunks = []
    for c in forzados + encontrados:
        if c["id"] not in vistos:
            vistos.add(c["id"])
            chunks.append(c)

    # Si hay un tema crítico, el aviso se entrega aunque falle el modelo o no haya resultados.
    nivel_regla = det.minimo
    if not chunks:
        nivel = nivel_regla if nivel_regla != "no_aplica" else "indeterminada"
        return MensajeOut(
            respuesta="Esto no consta en el reglamento.",
            gravedad=nivel,
            aviso=seguridad.aviso(nivel_regla, det.urgente, perfil),
            fuentes=[],
        )

    try:
        salida = llm.generate(llm.build_user_prompt(pregunta, chunks, perfil, historial))
    except RuntimeError as exc:
        if nivel_regla in ("grave", "gravisima"):
            return MensajeOut(
                respuesta="En este momento no pude generar una respuesta.",
                gravedad=nivel_regla,
                aviso=seguridad.aviso(nivel_regla, det.urgente, perfil),
                fuentes=[],
            )
        raise LLMNoDisponible(str(exc)) from exc

    gravedad_llm, respuesta = llm.parse_salida(salida)
    if gravedad_llm == "indeterminada":
        gravedad = nivel_regla if nivel_regla != "no_aplica" else "indeterminada"
    else:
        gravedad = seguridad.mayor(gravedad_llm, nivel_regla)

    fuentes = [
        Fuente(
            version=c["version"],
            capitulo=c["capitulo"],
            articulo=c["articulo"],
            pagina=c["pagina"],
            extracto=c["contenido"][:300],
            score=round(c["score"], 5),
        )
        for c in chunks
    ]
    return MensajeOut(
        respuesta=respuesta,
        gravedad=gravedad,
        aviso=seguridad.aviso(gravedad, det.urgente, perfil),
        fuentes=fuentes,
    )


def _obtenerRolIdPorPerfil(perfil: str, conn) -> int:
    """Rol del consultante anónimo, a partir del perfil recibido."""
    row = conn.execute(
        """SELECT id FROM roles WHERE lower(nombre) = lower(%s) ORDER BY id LIMIT 1""",
        (perfil,),
    ).fetchone()
    if row:
        return row["id"]

    # Garantiza que la consulta anónima se pueda registrar aunque el rol no esté creado.
    conn.execute(
        """INSERT INTO roles (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING""",
        (perfil,),
    )
    row = conn.execute(
        """SELECT id FROM roles WHERE lower(nombre) = lower(%s) ORDER BY id LIMIT 1""",
        (perfil,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"No se pudo obtener el rol '{perfil}'")
    return row["id"]


def _resolverSesion(usuario_id: UUID | None, perfil: str, conn) -> tuple[UUID | None, int]:
    """Si hay usuario autenticado usa su rol; si no, registra solo el rol del consultante."""
    if usuario_id is not None:
        row = conn.execute(
            """SELECT rol_id FROM usuarios WHERE id = %s""",
            (usuario_id,),
        ).fetchone()
        if row:
            return usuario_id, row["rol_id"]
    return None, _obtenerRolIdPorPerfil(perfil, conn)


def verificarConsulta(consulta_id: UUID, usuario_id: UUID | None, conn) -> None:
    row = conn.execute(
        """SELECT user_id FROM consultas WHERE id = %s""",
        (consulta_id,),
    ).fetchone()
    if not row:
        raise ConsultaNoEncontrada("Consulta no encontrada")

    # Las consultas anónimas no tienen dueño; las de un usuario solo las ve su dueño.
    duenio = row["user_id"]
    if duenio is not None and duenio != usuario_id:
        raise ConsultaNoEncontrada("Consulta no encontrada")


def obtenerHistorial(consulta_id: UUID, conn, limite: int = MAX_HISTORIAL) -> list[dict]:
    """Últimos turnos de la sesión, en orden cronológico para el prompt del modelo."""
    filas = conn.execute(
        """SELECT mensaje, respuesta
           FROM consulta_logs
           WHERE consulta_id = %s
           ORDER BY fecha_creacion DESC, id DESC
           LIMIT %s""",
        (consulta_id, limite),
    ).fetchall()
    return list(reversed(filas))


def guardarLog(consulta_id: UUID, mensaje: str, respuesta: str, conn) -> None:
    conn.execute(
        """INSERT INTO consulta_logs (consulta_id, mensaje, respuesta)
           VALUES (%s, %s, %s)""",
        (consulta_id, mensaje, respuesta),
    )


def crearConsultaConMensaje(
    usuario_id: UUID | None,
    mensaje: str,
    conn,
    perfil: str = "estudiante",
    version: str | None = None,
    k: int = 6,
) -> MensajeOut:
    """Crea una sesión de consulta (autenticada o anónima) y guarda el primer turno."""
    usuario_id, rol_id = _resolverSesion(usuario_id, perfil, conn)
    resultado = enviarMensaje(mensaje, perfil, version, k)

    try:
        consulta = conn.execute(
            """INSERT INTO consultas (user_id, rol_usuario_id, severidad, detalles)
               VALUES (%s, %s, %s, %s)
               RETURNING id""",
            (usuario_id, rol_id, resultado.gravedad, mensaje),
        ).fetchone()
        if not consulta:
            raise RuntimeError("No se pudo crear la consulta")

        guardarLog(consulta["id"], mensaje, resultado.respuesta, conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    resultado.consulta_id = consulta["id"]
    return resultado


def continuarConsulta(
    consulta_id: UUID,
    usuario_id: UUID | None,
    mensaje: str,
    conn,
    perfil: str = "estudiante",
    version: str | None = None,
    k: int = 6,
) -> MensajeOut:
    """Continúa una sesión existente usando los últimos mensajes como contexto."""
    verificarConsulta(consulta_id, usuario_id, conn)
    historial = obtenerHistorial(consulta_id, conn)
    resultado = enviarMensaje(mensaje, perfil, version, k, historial)

    try:
        guardarLog(consulta_id, mensaje, resultado.respuesta, conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    resultado.consulta_id = consulta_id
    return resultado


def obtenerLogs(consulta_id: UUID, usuario_id: UUID | None, conn) -> list[dict]:
    """Historial completo de una sesión, del mensaje más antiguo al más reciente."""
    verificarConsulta(consulta_id, usuario_id, conn)
    return conn.execute(
        """SELECT id, consulta_id, mensaje, adjunto, respuesta, fecha_creacion
           FROM consulta_logs
           WHERE consulta_id = %s
           ORDER BY fecha_creacion ASC, id ASC""",
        (consulta_id,),
    ).fetchall()


def obtenerConsultaPorId(id: UUID, conn, usuario_id: UUID | None = None):
    data = conn.execute(
        """SELECT user_id, rol_usuario_id, severidad, detalles, fecha_creacion
           FROM consultas
           WHERE id = %s""",
        (id,),
    ).fetchone()
    if not data:
        return None
    if data["user_id"] is not None and data["user_id"] != usuario_id:
        return None
    return data

