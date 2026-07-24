#!/usr/bin/env python3
"""
Metadatos editoriales canónicos de los 58 volúmenes de Aṭṭhakathā (set ROTB).

Por qué este módulo existe
--------------------------
El campo `head` de la base de datos (cabecera de página) NO es fiable para
título ni transliteración: viene de una conversión de fuente legacy con un mapa
de caracteres corrupto (p. ej. `n→ṃ`, `ṇ→ṅ`, `ṃ→ḍ`, `ḷ→ā`), y además incluye
números de página y ruido. El cuerpo del texto (UNITEXT, base64) sí decodifica
bien, pero las cabeceras no. Por eso los títulos, las cornisas y la portada se
toman de aquí, no del `head`.

Cada entrada: book_no → (title, sigla, vol, mula)
  - title : título canónico de la obra (diacríticos correctos)
  - sigla : abreviatura académica estándar (citación)
  - vol   : número de volumen dentro de la obra ("" si es volumen único)
  - mula  : texto canónico comentado (Tipiṭaka)

Identificación: los vols. 1–51 están bien establecidos. Los vols. 52–58 se
identificaron por el texto inicial de cada libro (ver README); revísalos si
dispones de los impresos PTS:
  52–56 = Pañcappakaraṇaṭṭhakathā (Dhātukathā, Puggalapaññatti, Kathāvatthu,
          Yamaka, Paṭṭhāna), 57 = Milindapañha, 58 = Visuddhimagga.
"""

BOOK_META = {
    # Vinaya-aṭṭhakathā — Samantapāsādikā (PTS vols I–VII)
    1: ("Samantapāsādikā", "Sp", "I", "Vinaya"),
    2: ("Samantapāsādikā", "Sp", "II", "Vinaya"),
    3: ("Samantapāsādikā", "Sp", "III", "Vinaya"),
    4: ("Samantapāsādikā", "Sp", "IV", "Vinaya"),
    5: ("Samantapāsādikā", "Sp", "V", "Vinaya"),
    6: ("Samantapāsādikā", "Sp", "VI", "Vinaya"),
    7: ("Samantapāsādikā", "Sp", "VII", "Vinaya"),
    # Pātimokkha
    8: ("Kaṅkhāvitaraṇī", "Kkh", "", "Pātimokkha"),
    # Dīghanikāya-aṭṭhakathā — Sumaṅgalavilāsinī
    9: ("Sumaṅgalavilāsinī", "Sv", "I", "Dīghanikāya"),
    10: ("Sumaṅgalavilāsinī", "Sv", "II", "Dīghanikāya"),
    11: ("Sumaṅgalavilāsinī", "Sv", "III", "Dīghanikāya"),
    # Majjhimanikāya-aṭṭhakathā — Papañcasūdanī
    12: ("Papañcasūdanī", "Ps", "I", "Majjhimanikāya"),
    13: ("Papañcasūdanī", "Ps", "II", "Majjhimanikāya"),
    14: ("Papañcasūdanī", "Ps", "III", "Majjhimanikāya"),
    15: ("Papañcasūdanī", "Ps", "IV", "Majjhimanikāya"),
    16: ("Papañcasūdanī", "Ps", "V", "Majjhimanikāya"),
    # Saṃyuttanikāya-aṭṭhakathā — Sāratthappakāsinī
    17: ("Sāratthappakāsinī", "Spk", "I", "Saṃyuttanikāya"),
    18: ("Sāratthappakāsinī", "Spk", "II", "Saṃyuttanikāya"),
    19: ("Sāratthappakāsinī", "Spk", "III", "Saṃyuttanikāya"),
    # Aṅguttaranikāya-aṭṭhakathā — Manorathapūraṇī
    20: ("Manorathapūraṇī", "Mp", "I", "Aṅguttaranikāya"),
    21: ("Manorathapūraṇī", "Mp", "II", "Aṅguttaranikāya"),
    22: ("Manorathapūraṇī", "Mp", "III", "Aṅguttaranikāya"),
    23: ("Manorathapūraṇī", "Mp", "IV", "Aṅguttaranikāya"),
    24: ("Manorathapūraṇī", "Mp", "V", "Aṅguttaranikāya"),
    # Khuddaka — comentarios menores
    25: ("Paramatthajotikā I (Khuddakapāṭha-aṭṭhakathā)", "Pj I", "", "Khuddakapāṭha"),
    26: ("Dhammapada-aṭṭhakathā", "Dhp-a", "I", "Dhammapada"),
    27: ("Dhammapada-aṭṭhakathā", "Dhp-a", "II", "Dhammapada"),
    28: ("Dhammapada-aṭṭhakathā", "Dhp-a", "III", "Dhammapada"),
    29: ("Dhammapada-aṭṭhakathā", "Dhp-a", "IV", "Dhammapada"),
    30: ("Paramatthadīpanī (Udāna-aṭṭhakathā)", "Ud-a", "", "Udāna"),
    31: ("Paramatthadīpanī (Itivuttaka-aṭṭhakathā)", "It-a", "I", "Itivuttaka"),
    32: ("Paramatthadīpanī (Itivuttaka-aṭṭhakathā)", "It-a", "II", "Itivuttaka"),
    33: ("Paramatthajotikā II (Suttanipāta-aṭṭhakathā)", "Pj II", "I", "Suttanipāta"),
    34: ("Paramatthajotikā II (Suttanipāta-aṭṭhakathā)", "Pj II", "II", "Suttanipāta"),
    35: ("Paramatthadīpanī (Vimānavatthu-aṭṭhakathā)", "Vv-a", "", "Vimānavatthu"),
    36: ("Paramatthadīpanī (Petavatthu-aṭṭhakathā)", "Pv-a", "", "Petavatthu"),
    37: ("Paramatthadīpanī (Theragāthā-aṭṭhakathā)", "Th-a", "I", "Theragāthā"),
    38: ("Paramatthadīpanī (Theragāthā-aṭṭhakathā)", "Th-a", "II", "Theragāthā"),
    39: ("Paramatthadīpanī (Theragāthā-aṭṭhakathā)", "Th-a", "III", "Theragāthā"),
    40: ("Paramatthadīpanī (Therīgāthā-aṭṭhakathā)", "Thī-a", "", "Therīgāthā"),
    41: ("Saddhammapajjotikā (Niddesa-aṭṭhakathā)", "Nidd-a", "I", "Niddesa"),
    42: ("Saddhammapajjotikā (Niddesa-aṭṭhakathā)", "Nidd-a", "II", "Niddesa"),
    43: ("Saddhammapajjotikā (Niddesa-aṭṭhakathā)", "Nidd-a", "III", "Niddesa"),
    44: ("Saddhammappakāsinī (Paṭisambhidāmagga-aṭṭhakathā)", "Paṭis-a", "I", "Paṭisambhidāmagga"),
    45: ("Saddhammappakāsinī (Paṭisambhidāmagga-aṭṭhakathā)", "Paṭis-a", "II", "Paṭisambhidāmagga"),
    46: ("Saddhammappakāsinī (Paṭisambhidāmagga-aṭṭhakathā)", "Paṭis-a", "III", "Paṭisambhidāmagga"),
    47: ("Visuddhajanavilāsinī (Apadāna-aṭṭhakathā)", "Ap-a", "", "Apadāna"),
    48: ("Madhuratthavilāsinī (Buddhavaṃsa-aṭṭhakathā)", "Bv-a", "", "Buddhavaṃsa"),
    49: ("Paramatthadīpanī (Cariyāpiṭaka-aṭṭhakathā)", "Cp-a", "", "Cariyāpiṭaka"),
    # Abhidhamma-aṭṭhakathā
    50: ("Atthasālinī (Dhammasaṅgaṇī-aṭṭhakathā)", "As", "", "Dhammasaṅgaṇī"),
    51: ("Sammohavinodanī (Vibhaṅga-aṭṭhakathā)", "Vibh-a", "", "Vibhaṅga"),
    52: ("Pañcappakaraṇaṭṭhakathā (Dhātukathā-aṭṭhakathā)", "Pañc-a", "", "Dhātukathā"),
    53: ("Pañcappakaraṇaṭṭhakathā (Puggalapaññatti-aṭṭhakathā)", "Pañc-a", "", "Puggalapaññatti"),
    54: ("Pañcappakaraṇaṭṭhakathā (Kathāvatthu-aṭṭhakathā)", "Pañc-a", "", "Kathāvatthu"),
    55: ("Pañcappakaraṇaṭṭhakathā (Yamaka-aṭṭhakathā)", "Pañc-a", "", "Yamaka"),
    56: ("Pañcappakaraṇaṭṭhakathā (Paṭṭhāna-aṭṭhakathā)", "Pañc-a", "", "Paṭṭhāna"),
    # Extra-canónicos incluidos en el set
    57: ("Milindapañha", "Mil", "", "—"),
    58: ("Visuddhimagga", "Vism", "", "—"),
}


def book_title(book_no: int) -> str:
    """Título canónico + volumen para la portada / título del documento."""
    m = BOOK_META.get(book_no)
    if not m:
        return f"Aṭṭhakathā — Libro {book_no}"
    title, _sigla, vol, _mula = m
    return f"{title} {vol}".strip()


def book_running_head(book_no: int) -> str:
    """Cornisa de citación, p. ej. 'Sumaṅgalavilāsinī · Sv I'."""
    m = BOOK_META.get(book_no)
    if not m:
        return f"Libro {book_no}"
    title, sigla, vol, _mula = m
    cite = f"{sigla} {vol}".strip()
    return f"{title} · {cite}"


def book_sigla(book_no: int) -> str:
    """Sigla + volumen, p. ej. 'Sv I' (vacío si desconocido)."""
    m = BOOK_META.get(book_no)
    if not m:
        return ""
    _title, sigla, vol, _mula = m
    return f"{sigla} {vol}".strip()
