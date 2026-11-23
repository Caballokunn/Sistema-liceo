"""Reglas de seguridad que NO dependen del modelo.

- Detectan temas críticos en la consulta (abuso, violencia, acoso, drogas, autolesión...).
- Fuerzan la recuperación del protocolo correspondiente del reglamento.
- Fijan un nivel mínimo de gravedad (ante la duda se escala, nunca se baja).
- Generan el aviso de "qué hacer ahora" con texto fijo, según el perfil (estudiante / apoderado).

IMPORTANTE: los textos de aviso y las palabras clave son un punto de partida.
Debe revisarlos el colegio (convivencia escolar) antes de usarlo con estudiantes.
"""
import os
import re
import unicodedata
from dataclasses import dataclass, field

NIVELES = ["no_aplica", "leve", "grave", "gravisima"]  # orden de menor a mayor

# tema -> (patrones sobre texto sin tildes y en minúsculas, n° de artículo del protocolo, nivel mínimo, urgente)
TEMAS: dict[str, dict] = {
    "autolesion": {
        "patrones": [r"suicid", r"quitarme la vida", r"quiero morir", r"no quiero vivir", r"matarme",
                     r"autolesion", r"hacerme dano", r"cortarme", r"me corto", r"se corta", r"ideacion"],
        "articulo": 48, "minimo": "gravisima", "urgente": True,
    },
    "sexual": {
        "patrones": [r"abuso sexual", r"agresion sexual", r"violacion", r"violar", r"violaron", r"\bviolo\b",
                     r"\b(me|le|la|lo|les|nos) toco\b", r"\btoco (a|mi|su|el|la)\b", r"\btocaron\b", r"\btocan\b",
                     r"tocaje", r"tocamiento", r"acoso sexual", r"manose", r"fotos intimas", r"connotacion sexual",
                     r"desnud", r"se propaso", r"me obligo a"],
        "articulo": 43, "minimo": "gravisima", "urgente": True,
    },
    "violencia": {
        "patrones": [r"golpe", r"\bpego\b", r"\bpegar\b", r"\bpegaron\b", r"agred", r"pelea", r"amenaz",
                     r"maltrat", r"violencia", r"\barmas?\b", r"cuchillo", r"apunal"],
        "articulo": 40, "minimo": "grave", "urgente": False,
    },
    "acoso": {
        "patrones": [r"bullying", r"acoso", r"ciberacoso", r"hostiga", r"\bfuna\b", r"se burlan", r"me molestan"],
        "articulo": 44, "minimo": "grave", "urgente": False,
    },
    "drogas": {
        "patrones": [r"droga", r"marihuana", r"\bporro", r"cocaina", r"pasta base", r"alcohol", r"consumo"],
        "articulo": 41, "minimo": "grave", "urgente": False,
    },
    "trafico": {
        "patrones": [r"trafic", r"microtrafic", r"vend(e|en|er|iendo) (droga|marihuana|pasta)"],
        "articulo": 41, "minimo": "gravisima", "urgente": False,
    },
    "discriminacion": {
        "patrones": [r"discrimin", r"racis", r"homofob", r"xenofob"],
        "articulo": 42, "minimo": "grave", "urgente": False,
    },
    "vulneracion": {
        "patrones": [r"vulneracion", r"abandono", r"negligencia", r"violencia intrafamiliar",
                     r"me pegan en (mi )?casa"],
        "articulo": 39, "minimo": "grave", "urgente": False,
    },
}


@dataclass
class Deteccion:
    temas: list[str] = field(default_factory=list)
    articulos: list[int] = field(default_factory=list)
    minimo: str = "no_aplica"
    urgente: bool = False


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def mayor(a: str, b: str) -> str:
    return a if NIVELES.index(a) >= NIVELES.index(b) else b


def detectar(texto: str) -> Deteccion:
    t = normalizar(texto)
    det = Deteccion()
    for tema, cfg in TEMAS.items():
        if any(re.search(p, t) for p in cfg["patrones"]):
            det.temas.append(tema)
            if cfg["articulo"] not in det.articulos:
                det.articulos.append(cfg["articulo"])
            det.minimo = mayor(det.minimo, cfg["minimo"])
            det.urgente = det.urgente or cfg["urgente"]
    # los protocolos más delicados primero (autolesión y abuso sexual)
    prioridad = {48: 0, 43: 1, 40: 2, 39: 3, 44: 4, 41: 5, 42: 6}
    det.articulos.sort(key=lambda n: prioridad.get(n, 9))
    return det


def _urgencia() -> str:
    # Texto con teléfonos/contactos VERIFICADOS por el colegio (convivencia, emergencias, líneas de ayuda).
    return os.environ.get("AVISO_URGENCIA", "").strip()


def aviso(nivel: str, urgente: bool, perfil: str) -> str | None:
    extra = f" {_urgencia()}" if _urgencia() else ""
    if perfil == "apoderado":
        if urgente:
            return ("Si existe riesgo inmediato para el o la estudiante, busque ayuda de urgencia ahora y avise "
                    "de inmediato al establecimiento (Inspectoría General o Encargado/a de Convivencia Escolar)."
                    + extra)
        if nivel == "gravisima":
            return ("Por la naturaleza de lo descrito, le recomendamos contactar a la brevedad al establecimiento "
                    "(Inspectoría General o Encargado/a de Convivencia Escolar) para que se active el protocolo "
                    "correspondiente, y dejar constancia por escrito." + extra)
        if nivel == "grave":
            return ("Le recomendamos informar al profesor/a jefe o a Inspectoría General para que se evalúe la "
                    "situación y quede registro.")
        return None
    # estudiante (por defecto)
    if urgente:
        return ("Si tú o alguien más está en riesgo ahora, avisa de inmediato a un adulto de confianza que esté "
                "cerca. No tienes que enfrentarlo solo/a. En el colegio puedes acudir hoy mismo a tu profesor/a "
                "jefe, a Inspectoría General o al Encargado/a de Convivencia Escolar." + extra)
    if nivel == "gravisima":
        return ("Una situación así es seria y no tienes que resolverla solo/a. Cuéntasela hoy a un adulto del "
                "colegio en quien confíes (profesor/a jefe, Inspectoría General o Encargado/a de Convivencia "
                "Escolar) para que se active el protocolo del reglamento." + extra)
    if nivel == "grave":
        return "Te recomendamos avisar a tu profesor/a jefe o a Inspectoría General para que puedan ayudarte y registrar lo ocurrido."
    return None