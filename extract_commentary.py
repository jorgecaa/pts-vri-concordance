#!/usr/bin/env python3
"""
Extract atthakatha (Aṭṭhakathā) commentary to JSON — Unicode only.

Output: decoded Romanized Pali text preserving {variants}, [F.N], ║N║.
Mejoras editoriales:
  - Se rejuntan las palabras partidas por guion de fin de línea del impreso
    (`word-\\n  resto` → `wordresto`) antes de calcular posiciones (#1).
  - El aparato crítico se parsea en notas numeradas {num: texto} enlazables (#2).
  - El título/sigla/volumen sale del mapa canónico `book_meta`, no del `head`
    (que está corrupto en la fuente) (#4/#6/#9).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from main.database import TipitakaDatabase, decode_unitext  # noqa: E402
from book_meta import BOOK_META, book_title  # noqa: E402


# Letra pāli/latina (para detectar guiones de fin de línea entre palabras)
_LETTER = r"[A-Za-zĀāĪīŪūṄṅÑñṬṭḌḍṆṇḶḷṂṃ]"


def dehyphenate(text: str) -> str:
    """Une palabras partidas por la justificación del impreso PTS.

    En el original, la composición parte palabras al final de renglón con un
    guion (`sacchi-\\n  katvā`). Ese guion no es léxico: hay que eliminarlo y
    unir los fragmentos (`sacchikatvā`). Se exige que el carácter previo al
    guion sea una letra, para no tocar guiones de puntuación ni rayas.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # letra + '-' + fin de línea + sangría de continuación → unir sin guion
    return re.sub(rf"({_LETTER})-\n[ \t]*", r"\1", text)


def correct_head(head: str, head_old: str) -> str:
    """Reconstruye la cabecera a partir de los dos campos corruptos de la BD.

    `head` y `head_old` se corrompieron de forma COMPLEMENTARIA al convertir la
    fuente legacy a Unicode:
      · `head`     decodifica bien las MAYÚSCULAS (Ṇ Ī Ū Ṭ Ṃ Ñ…) salvo la nasal
                   velar, que aparece como Ḷ/ḷ (`SUMAḷGALA` ← `SUMAṄGALA`).
      · `head_old` decodifica bien las MINÚSCULAS (`Kaṅkhāvitaraṇī`,
                   `Papañcasūdanī`) pero estropea las mayúsculas (Ī→M, Ṭ→R…).
    Los títulos de sección PTS van en mayúsculas → se toma `head` (+ Ḷ/ḷ→Ṅ); las
    cornisas de obra en minúsculas → se toma `head_old`.
    """
    head = (head or "").strip()
    head_old = (head_old or "").strip()
    letters = [c for c in head if c.isalpha()]
    if not letters:
        return head
    upper = sum(1 for c in letters if c.isupper())
    if upper >= len(letters) * 0.6:  # título en mayúsculas → nasal velar = Ṅ
        return head.replace("Ḷ", "Ṅ").replace("ḷ", "Ṅ")
    return head_old or head  # cornisa en minúsculas


def parse_apparatus(app: str) -> dict:
    """Convierte el aparato crudo en {num_nota: texto}.

    Formato fuente: '    1 Recurs below, § 63.    2 §§ 3-10 recur ...'.
    Se separa por ' N ' (número rodeado de espacios); así no parte '§ 63.'
    ni rangos como '3-10'.
    """
    if not app:
        return {}
    flat = re.sub(r"\s+", " ", app.strip())
    parts = re.split(r"\s(\d{1,3})\s", " " + flat + " ")
    notes = {}
    it = iter(parts[1:])  # parts[0] = texto previo al primer número
    for num, txt in zip(it, it):
        txt = txt.strip()
        if txt:
            notes[int(num)] = txt
    return notes


def extract(db_path: str, output_dir: str):
    db = TipitakaDatabase(db_path, edition="atthakatha")
    if not db.connect():
        print("Error: Could not connect to database")
        sys.exit(1)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    books = db.get_all_books()
    print(f"{len(books)} libros\n")

    index = {"edition": "atthakatha", "books": []}
    cur = db.connection.cursor()

    for book in books:
        bn = book["book_no"]
        cur.execute(
            "SELECT COUNT(*) FROM pages WHERE edition='atthakatha' AND book_no=?", (bn,)
        )
        total = cur.fetchone()[0]
        if total == 0:
            continue

        print(f"  {bn:02d}: {total:4d} págs — ", end="", flush=True)

        pages = []
        cur.execute(
            "SELECT page_no, head, head_old, unitext FROM pages"
            " WHERE edition='atthakatha' AND book_no=? ORDER BY page_no",
            (bn,),
        )

        for row in cur.fetchall():
            plain = dehyphenate(decode_unitext(row["unitext"] or ""))
            page_data = {
                "page": row["page_no"],
                "head": correct_head(row["head"], row["head_old"]),
                "text": plain,
            }

            # Extract variant markers {word} → record positions for italic
            variants = []
            depth = 0
            start = -1
            for i, ch in enumerate(plain):
                if ch == "{":
                    depth += 1
                    if depth == 1:
                        start = i
                elif ch == "}":
                    if depth == 1 and start >= 0:
                        variants.append(
                            {"start": start, "end": i + 1, "text": plain[start + 1 : i]}
                        )
                    depth = max(0, depth - 1)
            if variants:
                page_data["variants"] = variants

            # Extract folio markers
            folios = []
            for m in re.finditer(r"\[F\.(\d+[vr]?)\]", plain):
                folios.append({"start": m.start(), "end": m.end(), "text": m.group()})
            if folios:
                page_data["folios"] = folios

            # Extract section markers
            sections = []
            for m in re.finditer(r"║(\d+)║", plain):
                sections.append({"start": m.start(), "end": m.end(), "text": m.group()})
            if sections:
                page_data["sections"] = sections

            # Apparatus criticus: texto crudo + notas numeradas (para enlazar)
            cur2 = db.connection.cursor()
            cur2.execute(
                "SELECT unitext FROM footnotes WHERE edition='atthakatha' AND book_no=? AND page_no=?",
                (bn, row["page_no"]),
            )
            fn = cur2.fetchone()
            if fn and fn["unitext"]:
                app = decode_unitext(fn["unitext"])
                page_data["apparatus"] = app
                notes = parse_apparatus(app)
                if notes:
                    # JSON exige claves str; el generador las reconvierte a int
                    page_data["notes"] = {str(k): v for k, v in notes.items()}

            pages.append(page_data)

        # Título canónico desde book_meta (NO desde head, que está corrupto)
        name = book_title(bn)
        meta = BOOK_META.get(bn)

        fname = f"book_{bn:02d}.json"
        book_obj = {
            "book_no": bn,
            "name": name,
            "total_pages": total,
            "pages": pages,
        }
        if meta:
            work, sigla, vol, mula = meta
            book_obj.update({"work": work, "sigla": sigla, "vol": vol, "mula": mula})
        (out / fname).write_text(
            json.dumps(book_obj, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        index_entry = {"book_no": bn, "name": name, "pages": total, "file": fname}
        if meta:
            index_entry["sigla"] = f"{meta[1]} {meta[2]}".strip()
        index["books"].append(index_entry)
        print(name[:50])

    (out / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_pages = sum(b["pages"] for b in index["books"])
    print(f"\n✓ {len(index['books'])} libros · {total_pages:,} páginas → {output_dir}/")
    db.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "src/data/tipitaka.sqlite"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "rotb_commentary"
    extract(db_path, out_dir)
