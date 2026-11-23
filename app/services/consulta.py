from dataclasses import dataclass, field

import app.database as db
import app.services.llm as llm
import app.services.seguridad as seguridad
from app.services.embeddings import embed_query
from app.schemas.consulta import MensajeIn, MensajeOut, Fuente


class LLMNoDisponible(RuntimeError):
    """Ningún backend del LLM pudo generar una respuesta."""


def enviarMensaje(pregunta: str, perfil: str = "estudiante", version: str | None = None,
              k: int = 6) -> MensajeOut:
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
        salida = llm.generate(llm.build_user_prompt(pregunta, chunks, perfil))
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
    # Nunca se baja la gravedad respecto de las reglas: ante la duda, se escala.
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


def obtenerConsultaPorId(id: int, conn):
    try:
        row = conn.execute("""SELECT user_id, rol_usuario, severidad, detalles, fecha_creacion FROM consultas WHERE id = %s""", (id,)).fetchone()
        return row
    except Exception as e:
        return None
