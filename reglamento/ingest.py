"""Ingesta del PDF del reglamento a Supabase, un chunk por artículo.

Uso:
  python ingest.py reglamento.pdf --version 2026-03 --dry-run   # solo revisa el parseo
  python ingest.py reglamento.pdf --version 2026-03             # indexa

Opcional: --skip-pages 1-5 para forzar que se omitan páginas (el índice se detecta solo).
"""
import argparse
import re
from dataclasses import dataclass

import pymupdf  # PyMuPDF

MAX_CHARS = 1800  # artículos más largos se parten por párrafos (E5 trunca ~512 tokens)

# Encabezado de artículo: "Artículo 4°:", "ARTÍCULO 39°:", "Articulo N°36", "Artículo 1. Título".
# Grupos: 1 palabra, 2 número, 3 puntuación, 4 resto de la línea.
ART_RE = re.compile(
    r"^\s*(Art[ií]culo|ART[IÍ]CULO|Art\.)\s*(?:N\s*[°º.]?\s*)?(\d+[\w°º\-]*)\s*([.\-–:]*)\s*(.*)$"
)
CAP_RE = re.compile(r"^\s*((?:CAP[IÍ]TULO|T[IÍ]TULO|Cap[ií]tulo|T[ií]tulo)\s+[IVXLCDM\d]+.*)$")
ITEM_RE = re.compile(r"^\s*([a-zñ]\)|\d+[.)]|[-•])\s")
DOTS_RE = re.compile(r"(\.{5,}|…{3,})")  # puntos guía del índice
BLOQUE_RE = re.compile(r"^(PROTOCOLO|NORMATIVA|ANEXO|REGLAMENTO)\b")
TOC_RATIO = 0.3  # una página con >= 30% de líneas con puntos guía se considera índice


@dataclass
class Chunk:
    capitulo: str | None
    articulo: str
    parte: int
    pagina: int | None
    contenido: str
    titulo: str = ""


def parse_pages(spec: str | None) -> set[int]:
    pages: set[int] = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if part:
            a, _, b = part.partition("-")
            pages.update(range(int(a), int(b or a) + 1))
    return pages


def read_pages(pdf_path: str, skip_pages: set[int]) -> tuple[list[tuple[int, str]], list[int]]:
    """Devuelve las líneas del cuerpo y las páginas omitidas (índice o indicadas a mano)."""
    lines: list[tuple[int, str]] = []
    skipped: list[int] = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            raw = [ln.strip() for ln in page.get_text("text").splitlines()]
            raw = [ln for ln in raw if ln and not re.fullmatch(r"\d{1,3}", ln)]  # números de página sueltos
            dotted = sum(1 for ln in raw if DOTS_RE.search(ln))
            if i in skip_pages or (raw and dotted / len(raw) >= TOC_RATIO):
                skipped.append(i)
                continue
            lines.extend((i, ln) for ln in raw if not DOTS_RE.search(ln))
    return lines, skipped


def join_lines(lines: list[str]) -> str:
    """Une líneas cortadas por el PDF en párrafos; conserva incisos (a), 1., -) en línea propia."""
    out: list[str] = []
    for line in lines:
        if out and not ITEM_RE.match(line):
            prev = out[-1]
            out[-1] = prev[:-1] + line if prev.endswith("-") and line[:1].islower() else f"{prev} {line}"
        else:
            out.append(line)
    return "\n".join(out)


def split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    parts, current = [], ""
    for para in text.split("\n"):
        if current and len(current) + len(para) + 1 > MAX_CHARS:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def is_heading(m: re.Match) -> bool:
    """Descarta referencias partidas por salto de línea, ej. 'Artículo 5°, donde se señala...'."""
    punct, rest = m.group(3), m.group(4).strip()
    if not rest:
        return True
    if "." in punct or ":" in punct:  # "Artículo 5. Texto" / "Artículo 5°: Texto"
        return True
    return not (rest[0].islower() or rest[0] in ",;)")


def nice(text: str) -> str:
    return text.capitalize() if text.isupper() else text


def parse(pdf_path: str, skip_pages: set[int] | None = None) -> tuple[list[Chunk], list[int], list[str]]:
    lines, skipped = read_pages(pdf_path, skip_pages or set())
    chunks: list[Chunk] = []
    avisos: list[str] = []
    used: set[str] = set()
    capitulo: str | None = None
    cap_pending = False
    bloque: str | None = None  # anexo con numeración propia (ej. protocolo de celulares con Artículo 1..14)
    art_label: str | None = None
    art_title = ""
    art_page: int | None = None
    art_lines: list[str] = []

    def unique_label(base: str, title: str) -> str:
        label = f"{base} ({bloque})" if bloque else base
        if label in used:
            alt = f"{label} - {nice(title)[:50]}" if title else label
            if alt in used:
                alt = f"{label} #{sum(1 for u in used if u.startswith(label)) + 1}"
            avisos.append(f"'{label}' aparece más de una vez (pág {art_page}); se guarda como '{alt}'")
            label = alt
        used.add(label)
        return label

    def flush():
        nonlocal art_label, art_title, art_lines
        if art_label and art_lines:
            label = unique_label(art_label, art_title)
            for n, part in enumerate(split_long(join_lines(art_lines)), start=1):
                chunks.append(Chunk(capitulo, label, n, art_page, part, nice(art_title)))
        art_label, art_title, art_lines = None, "", []

    def detect_bloque(i: int) -> tuple[str, int] | None:
        """Línea en mayúsculas 'PROTOCOLO ...' (hasta 3 líneas) seguida de un encabezado de artículo."""
        line = lines[i][1]
        if not (line.isupper() and len(line) >= 15 and BLOQUE_RE.match(line)):
            return None
        title, j = line, i + 1
        while j < len(lines) and j - i < 3 and lines[j][1].isupper() and not ART_RE.match(lines[j][1]):
            title += " " + lines[j][1]
            j += 1
        if j < len(lines):
            m = ART_RE.match(lines[j][1])
            if m and is_heading(m):
                return title, j
        return None

    i = 0
    while i < len(lines):
        page, line = lines[i]

        found = detect_bloque(i)
        if found:
            flush()
            bloque, i = nice(found[0]), found[1]
            cap_pending = False
            continue

        cap = CAP_RE.match(line)
        art = ART_RE.match(line)
        if art and not is_heading(art):
            art = None

        if cap and not art:
            flush()
            bloque = None
            capitulo, cap_pending = cap.group(1).strip(), True
            i += 1
            continue
        if cap_pending and not art:
            cap_pending = False
            if len(line) < 100 and line.isupper():  # título del capítulo en su propia línea
                capitulo = f"{capitulo} - {line}"
                i += 1
                continue
        if art:
            cap_pending = False
            flush()
            art_label = f"Artículo {art.group(2)}"
            art_page = page
            rest = re.sub(r"^[\\º°:.\-–\s]+", "", art.group(4)).strip()  # limpia restos como "\º:"
            art_title = rest
            if rest:
                art_lines.append(rest)
        elif art_label:
            art_lines.append(line)
        i += 1
    flush()

    if not chunks:  # el PDF no tiene formato "Artículo N": fallback por tamaño
        text = join_lines([ln for _, ln in lines])
        for n, part in enumerate(split_long(text), start=1):
            chunks.append(Chunk(None, f"Sección {n}", 1, None, part))
    return chunks, skipped, avisos


def embed_text(c: Chunk) -> str:
    """Texto que se vectoriza: incluye capítulo, artículo y título para dar contexto al embedding."""
    header = " - ".join(x for x in (c.capitulo, c.articulo, c.titulo) if x)
    return f"{header}\n{c.contenido}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--version", required=True, help="ej: 2026-03")
    ap.add_argument("--skip-pages", help="páginas a omitir a mano, ej: 1-5 (el índice se detecta solo)")
    ap.add_argument("--dry-run", action="store_true", help="solo muestra cómo se parseó el PDF")
    ap.add_argument("--no-supersede", action="store_true", help="no marcar otras versiones como no vigentes")
    args = ap.parse_args()

    chunks, skipped, avisos = parse(args.pdf, parse_pages(args.skip_pages))
    labels = list(dict.fromkeys(c.articulo for c in chunks))
    print(f"{len(chunks)} chunks, {len(labels)} artículos/secciones detectados")
    print(f"Páginas omitidas (índice): {skipped or 'ninguna'}")
    for a in avisos:
        print("AVISO:", a)

    if args.dry_run:
        print("\nOrden detectado:", ", ".join(l.replace("Artículo ", "") for l in labels))
        for c in chunks[:5] + [x for x in chunks[-2:] if x not in chunks[:5]]:
            print(f"\n[{c.capitulo} | {c.articulo} | parte {c.parte} | pág {c.pagina}]\n{c.contenido[:300]}")
        return

    from pgvector import Vector

    import db
    from app.services.embeddings import embed_passages

    vectors = embed_passages([embed_text(c) for c in chunks])
    db.pool.open()
    with db.pool.connection() as conn:
        with conn.transaction():
            conn.execute("delete from reglamento_chunks where version = %s", (args.version,))
            with conn.cursor() as cur:
                cur.executemany(
                    """insert into reglamento_chunks
                       (version, vigente, fuente, capitulo, articulo, parte, pagina, contenido, embedding)
                       values (%s, true, %s, %s, %s, %s, %s, %s, %s)""",
                    [
                        (args.version, args.pdf, c.capitulo, c.articulo, c.parte, c.pagina, c.contenido, Vector(v))
                        for c, v in zip(chunks, vectors)
                    ],
                )
            if not args.no_supersede:
                conn.execute("update reglamento_chunks set vigente = false where version <> %s", (args.version,))
    db.pool.close()
    print("Listo.")


if __name__ == "__main__":
    main()