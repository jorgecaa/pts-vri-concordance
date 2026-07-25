#!/usr/bin/env python3
"""
Reglas morfológicas Pali para validación de palabras.

Reglas:
  1. No hay consonantes triples ni cuádruples (máximo: dobles)
  2. No hay vocales consecutivas (āā, aa, aā, āa, ii, etc.)
  3. Las palabras no terminan en consonante, salvo niggahita (ṃ)
  4. Las sílabas deben pertenecer al alfabeto Pali
"""

import re

# ══════════════════════════════════════════════════════════════════════
# INVENTARIO FONOLÓGICO PALI
# Fuentes:
#   - Geiger, W. A Pāli Grammar. PTS, 2005 (rev. K.R. Norman)
#   - Bomhard, A.R. An Introductory Grammar of the Pāḷi Language. 2018
#   - Duroiselle, C. A Practical Grammar of the Pali Language. 1997
#   - Kaccāyana Vyākaraṇa (trad. ITBMU, 2007) — sandhi-kappa
#   - "Transforming Sanskrit into Pali" (ancient-buddhist-texts.net)
# ══════════════════════════════════════════════════════════════════════


# ── VOCALES ───────────────────────────────────────────────────────────
# 5 breves + 5 largas. e/o son alófonos de e:/o: ante cluster.
# Fuente: Geiger §7; languagesgulper.com/eng/Pali.html
PALI_VOWELS = {"a", "ā", "i", "ī", "u", "ū", "e", "o"}


# ── NIGGAHITA ────────────────────────────────────────────────────────
# Anusvara. No es vocal ni consonante plena; cierra sílaba.
NIGGAHITA = "ṃ"


# ── CONSONANTES ──────────────────────────────────────────────────────
# Clasificación vagga tradicional: 25 stops/nasales + 7 avagga = 32.
# ʼ (avagraha) EXCLUIDO: no es fonema Pali estándar.
# Fuente: Kaccāyana §6 (SesÈ byaṃjanā); Geiger §9.
PALI_CONSONANTS = {
    # Vagga 1 — velares
    "k",
    "kh",
    "g",
    "gh",
    "ṅ",
    # Vagga 2 — palatales (fonéticamente africadas)
    "c",
    "ch",
    "j",
    "jh",
    "ñ",
    # Vagga 3 — retroflexas
    "ṭ",
    "ṭh",
    "ḍ",
    "ḍh",
    "ṇ",
    # Vagga 4 — dentales
    "t",
    "th",
    "d",
    "dh",
    "n",
    # Vagga 5 — labiales
    "p",
    "ph",
    "b",
    "bh",
    "m",
    # Avagga (no-vagga)
    "y",
    "r",
    "l",
    "ḷ",
    "v",
    "s",
    "h",
}


# ── PRIMER ELEMENTO VÁLIDO DE CLUSTER ────────────────────────────────
# Principios derivados de Bomhard §1.6 y Geiger §37-40:
#   1. Aspiradas NUNCA inician cluster.
#   2. r se asimila SIEMPRE al preceder otra consonante
#      (excepción: "tr" y "br" en formas léxicas supervivientes).
#   3. h no inicia clusters (aparece como segundo elemento: ṇh, nh, mh, ḷh).
#   4. v puede iniciar "vy" (sandhi vi- + vocal, Kaccāyana §21/35).
VALID_CLUSTER_FIRST = {
    # Stops no aspirados
    "k",
    "g",
    "ṅ",
    "c",
    "j",
    "ñ",
    "ṭ",
    "ḍ",
    "ṇ",
    "t",
    "d",
    "n",
    "p",
    "b",
    "m",
    # Sibilante (para geminada "ss" y cluster "sv")
    "s",
    # Laterales (geminadas "ll", "ḷḷ"; ḷ también en "ḷh")
    "l",
    "ḷ",
    # Semivocales
    "y",  # geminada "yy" (ayya < ārya)
    "v",  # "vy" de sandhi vi- + vocal (vyaggaṃ); "sv" (svākhyāto)
    # Líquida superviviente (solo en formas léxicas específicas)
    "r",  # SOLO en "tr" (tatra) y "br" (brahma) — no regla general
}


# ── CLUSTERS VÁLIDOS ─────────────────────────────────────────────────
# Principio rector: Pali tiende a la asimilación progresiva de clusters.
# La mayoría de grupos consonánticos sánscritos se simplifican a
# geminadas o formas asimiladas. Lo que sobrevive son:
#   (a) geminadas, (b) nasal + stop homorgánico, (c) nasal + h,
#   (d) un subconjunto muy restringido de clusters heterogéneos.
# Fuente principal para cada grupo indicada en comentario.
VALID_CLUSTERS = {
    # ═══════════════════════════════════════════════════════════════
    # (a) GEMINADAS SIMPLES
    # Resultado principal de asimilación. Fuente: Bomhard §1.6.
    # ═══════════════════════════════════════════════════════════════
    # Velares
    "kk",  # cakkhu (cakṣu→cakkhu), sakka
    "gg",  # agga, khagga (khaḍga→khagga)
    # Palatales
    "cc",  # sacca (satya→sacca), āhacca, paccayo
    "jj",  # vajja, vijjā (vidyā→vijjā)
    "ññ",  # añña (anya→añña), paññā (prajñā→paññā)
    # Retroflexas
    "ṭṭ",  # kaṭṭha, diṭṭhi (dṛṣṭi→diṭṭhi)
    "ḍḍ",  # kuḍḍa (kuḍya→kuḍḍa)
    "ṇṇ",  # aṇṇava (arṇava→aṇṇava)
    # Dentales
    "tt",  # mutta (mukta→mutta), attha
    "dd",  # sadda (śabda→sadda)
    "nn",  # anna
    # Labiales
    "pp",  # appa, sappa
    "bb",  # abbha (abhra→abbha)
    "mm",  # amma, sammā
    # Sibilante
    "ss",  # vassa, dassana (darśana→dassana)
    # Laterales
    "ll",  # alla, ulla
    "ḷḷ",  # kaḷḷa
    # Semivocal palatal
    "yy",  # ayya (ārya→ayya)
    # ═══════════════════════════════════════════════════════════════
    # (b) GEMINADAS ASPIRADAS (stop no aspirado + aspirada homorgánica)
    # Fonológicamente el primer elemento es siempre no aspirado.
    # Fuente: Bomhard §1.6; ancient-buddhist-texts.net.
    # ═══════════════════════════════════════════════════════════════
    "kkh",  # sakkhi (sākṣin→sakkhi)
    "ggh",  # (raro en corpus canónico)
    "cch",  # icchā, micchā (mithyā→micchā)
    "jjh",  # (raro)
    "ṭṭh",  # kaṭṭha, diṭṭhi
    "ḍḍh",  # (raro)
    "tth",  # attha (artha→attha), satthi (sakthī→satthi)
    "ddh",  # buddha, laddha (labdha→laddha)
    "pph",  # (raro)
    "bbh",  # pabbhāra (prāgbhāra→pabbhāra)
    # ═══════════════════════════════════════════════════════════════
    # (c) NASAL + STOP HOMORGÁNICO
    # Regla estricta: nasal y stop deben ser del mismo punto de
    # articulación. Fuente: Geiger §40; Bomhard §1.6.
    # ═══════════════════════════════════════════════════════════════
    # Nasal velar + stop velar
    "ṅk",  # saṅka, aṅka
    "ṅkh",  # saṅkha (śaṅkha→saṅkha)
    "ṅg",  # saṅgha, aṅga
    "ṅgh",  # saṅghāṭi
    # Nasal palatal + stop palatal
    "ñc",  # pañca, añca
    "ñch",  # (raro)
    "ñj",  # añjali, pañja
    "ñjh",  # (raro)
    # Nasal retroflexa + stop retroflexa
    "ṇṭ",  # kaṇṭha, paṇṭha
    "ṇṭh",  # kaṇṭhaja
    "ṇḍ",  # maṇḍala, kaṇḍa
    "ṇḍh",  # (raro)
    # Nasal dental + stop dental
    "nt",  # santa, anta, vanta
    "nth",  # pantha (raro)
    "nd",  # nanda, inda (indra→inda)
    "ndh",  # gandha, bandha
    # Nasal labial + stop labial
    "mp",  # kampa, sampa
    "mb",  # ambā, kambala
    # "mph", "mbh": no confirmados en corpus canónico — omitidos
    # ═══════════════════════════════════════════════════════════════
    # (d) NASAL + h
    # Proceso: sibilante sánscrita ante nasal → nasal + h en Pali.
    # ṣṇ→ṇh, sn→nh, sm→mh. Fuente: ancient-buddhist-texts.net.
    # ḷh: de retroflexa histórica. Fuente: corpus (gaḷha, muḷha).
    # ═══════════════════════════════════════════════════════════════
    "ṇh",  # gaṇhāti (gṛhṇāti→gaṇhāti)
    "nh",  # sāyanha (de raíces con -sn-)
    "mh",  # tumha (yuṣma→tumha), imamhā (imasmā→imamhā)
    "ḷh",  # gaḷha (gāḍha→gaḷha), muḷha (mūḍha→muḷha)
    # ═══════════════════════════════════════════════════════════════
    # (e) CLUSTERS HETEROGÉNEOS SUPERVIVIENTES
    # Solo los atestiguados con evidencia directa.
    # ═══════════════════════════════════════════════════════════════
    # Stop + v (corpus canónico directo)
    "kv",  # kvaci (kvacit→kvaci)
    "tv",  # tvaṃ (tvam→tvaṃ)
    "dv",  # dvāra, dve, dvīpa
    # Semivocal v + vocal (sandhi u/o → v, Kaccāyana §18)
    # Aparecen en sandhi externo: kho+assa=khvassa, su+ākhyāto=svākhyāto
    "sv",  # svākhyāto (su+ākhyāto, Ka); svāgata (su+āgata)
    "khv",  # khvassa (kho+assa, Ka §18) — ÚNICO caso de aspirada inicial
    # justificado: no es cluster interno sino sandhi de palabra
    # Líquida r superviviente (formas léxicas, no regla general)
    # Bomhard: "r following another consonant is GENERALLY assimilated,
    # but there are several examples where [it survives]."
    "tr",  # tatra, atra — Kaccāyana analiza "tr" como conjunct explícito
    "br",  # brahma, brāhmaṇa — no asimilado en estas formas
    # Clusters de sandhi vi- + vocal (Kaccāyana §21, §35)
    # i/ī ante vocal → y; resultado: by- o vy- según tradición textual.
    # by-: tradición birmana/Rūpasiddhi (ByaṃjanaṃRū = Vi aṃjanaṃ)
    # vy-: tradición cingalesa/Kaccāyana (VyaggaṃKa = Vi aggaṃ)
    # Ambas son variantes del mismo fenómeno, no fonemas distintos.
    "by",  # byaṃjana, byākata (vi + aṃjana / vi + ākata)
    "vy",  # vyaggaṃ, vyākaraṇaṃ (vi + aggaṃ / vi + ākaraṇaṃ)
}


# ── TABLA DE DECISIONES ──────────────────────────────────────────────
#
# INCLUIDO          RAZÓN
# ────────────────────────────────────────────────────────────────────
# ḷh                Atestiguado: gaḷha, muḷha
# mh                Atestiguado: tumha, imamhā
# sv                Atestiguado en Ka: svākhyāto < su+ākhyāto
# tr                Ka analiza "tr" explícitamente como conjunct
# br                Atestiguado: brahma, brāhmaṇa
# by / vy           Ka §21/35: sandhi vi- + vocal, dos variantes textuales
# khv               Ka §18: sandhi kho+assa=khvassa (único caso documentado)
#
# EXCLUIDO          RAZÓN
# ────────────────────────────────────────────────────────────────────
# cv, gv, jv...     No atestiguados; proyección del sánscrito
# kr, gr, pr...     Asimilados en Pali (Bomhard §1.6)
# khy, ghy...       Aspiradas no inician cluster (regla general)
# yh, rh, lh, sh    No atestiguados en corpus canónico
# mph, mbh          No confirmados en corpus canónico
# ʼ (avagraha)      No es fonema Pali estándar


# ══════════════════════════════════════════════════════════════════════
# (e) CLUSTERS ATESTIGUADOS, AÑADIDOS POR MEDICIÓN SOBRE EL CORPUS
# ══════════════════════════════════════════════════════════════════════
# Origen: se recorrieron las **40.907 palabras distintas** de las dos ediciones completas del
# Aṅguttara —PTS (BD, libros 17-21) y CST/VRI (`s040*m*.mul.xml`)— y se recogió todo grupo
# consonántico que la tabla anterior rechazaba. Salieron 54 grupos distintos en 2.775 posiciones.
# Los de abajo están atestiguados en el canon y su exclusión era un falso negativo: `tasmā`,
# `brāhmaṇo`, `indriya`, `kalyāṇa`, `mayhaṃ`, `jivhā` y `saṃyojana` son pali de manual.
#
# Tres de ellos contradicen expresamente la lista de EXCLUIDOS de arriba, y con el corpus delante:
#   · `yh`  — «no atestiguado» pero está en `mayhaṃ` (72 posiciones) y `ḍayhati`
#   · `mbh` / `mph` — «no confirmados» pero están en `ārambha` (237) y `samphassa` (60)
CLUSTERS_ATESTIGUADOS = {
    # niggahīta + continua/semivocal: el CST la CONSERVA aquí (no hay nasal homorgánica que valga)
    "ṃs",   # paṃsukūlika, vīmaṃsā, evaṃsaññī        (545)
    "ṃv",   # saṃvattati, saṃvāsa                     (340)
    "ṃy",   # saṃyojana, saṃyama, visaṃyutta          (175)
    "ṃh",   # saṃharati, upasaṃharati                  (41)
    "ṃr",   # kathaṃrūpa                                (6)
    # heterogéneos supervivientes
    "sm",   # tasmā, imasmiṃ, lokasmiṃ                (280)
    "hm",   # brahma, brāhmaṇa                        (253)
    "dr",   # indriya, saddhindriya                   (136)
    "ly",   # kalyāṇa, kalyāṇamitta                    (97)
    "yh",   # mayhaṃ, ḍayhati, pariḍayhamāna           (72)
    "nv",   # anvāsavati, anvaddhamāsaṃ                (32)
    "vh",   # jivhā, bavhābādha                        (21)
    "ky",   # sakya, sakyaputta                        (19)
    "ty",   # tyāssa, tyāhaṃ                           (12)
    "sn",   # sneha, kāmasneha                         (11)
    "gy",   # ārogya, ārogyamada                       (10)
    "my",   # kāmyatā, myāyaṃ                           (9)
    "gr",   # nigrodha                                  (8)
    "st",   # uddhasta, viddhasta                       (7)
    "khy",  # svākhyāta, saṅkhyā, asaṅkhyeyya           (5)
    "ṇy",   # ānaṇya                                    (6)
    "sy",   # ālasya, syā (marca de variante del CST)   (5)
    "hv",   # bahvābādha                                (2)
    "yv",   # yvāyaṃ                                    (2)
    "pl",   # plavati, uplavati                         (2)
    "kl",   # cittaklesa                                (1)
    "sp",   # vanaspati                                 (1)
    "mv",   # piyaṃvadā                                 (1)
    "kr",   # kriyavāda                                 (1)
    "tn",   # ratna    — sánscritismo de verso, en el CST
    "dm",   # padma    — idem
    # secuencias de tres: nasal + oclusiva aspirada
    "mbh",  # ārambha, jambhikā                       (237)
    "mph",  # samphassa, samphappalāpa                 (60)
}

# ══════════════════════════════════════════════════════════════════════
# (f) VARIANTE ORTOGRÁFICA: niggahīta ANTE OCLUSIVA
# ══════════════════════════════════════════════════════════════════════
# La norma pide nasal homorgánica (`saṅkhāra`, `sañjānāti`), pero **las dos ediciones escriben
# también la niggahīta** en ese contexto: `saṃkhaṃ`, `evaṃgotto`, `evaṃdiṭṭhi`, `kiṃphalo`. Es la
# inconsistencia conocida de la convención VRI, y aparece igual en el impreso de PTS, así que no
# es un error de una edición sino una vacilación compartida.
#
# Se aceptan como pali válido —lo son— pero van en un conjunto APARTE porque no son equivalentes
# a los de (e): éstos SÍ se reducen, y `pali_norm.normaliza()` los reduce (`ṃ`+velar → `ṅ`,
# `ṃ`+palatal → `ñ`). Tenerlos separados permite preguntar «¿es pali válido?» y «¿está en la
# convención normalizada?» por separado, que son dos preguntas distintas.
CLUSTERS_NIGGAHITA_VARIANTE = {
    "ṃk", "ṃkh", "ṃg", "ṃgh",      # velares:   saṃkhaṃ, evaṃgotto, saṃghāṭi
    "ṃc", "ṃj",                     # palatales: evaṃcitto, anusaṃjagghati
    "ṃṭ",                           # retroflejas
    "ṃt", "ṃd", "ṃdh",              # dentales:  vanaṃtaṃ, evaṃdhammo
    "ṃp", "ṃph", "ṃb", "ṃbh",       # labiales:  saṃpassa, kiṃphalo, saṃbojjhaṅga
    "ṃm", "ṃn",                     # nasales:   evaṃmahā, evaṃnāmo
}

VALID_CLUSTERS = VALID_CLUSTERS | CLUSTERS_ATESTIGUADOS | CLUSTERS_NIGGAHITA_VARIANTE

# ⚠️ NO se añaden `cl`, `lv`, `cv` aunque el barrido los encontró: son los NUMERALES ROMANOS de
# los marcadores de PTS (`cli`, `xlv`, `xcv`) colándose por el filtro de palabras. No son pali, y
# meterlos en la tabla habría hecho válido cualquier disparate que los contuviera.


def _tokenize(word):
    """Separa una palabra Pali en consonantes y vocales."""
    tokens = []
    i = 0
    while i < len(word):
        # Intentar dígrafo consonántico (kh, gh, ch, jh, ṭh, ḍh, th, dh, ph, bh)
        matched = False
        for dg in [
            "kh",
            "gh",
            "ch",
            "jh",
            "ṭh",
            "ḍh",
            "th",
            "dh",
            "ph",
            "bh",
            "ṅh",
            "ñh",
            "ṇh",
            "mh",
            "ḷh",
        ]:
            if word[i:].startswith(dg):
                tokens.append(("C", dg))
                i += len(dg)
                matched = True
                break
        if matched:
            continue

        c = word[i]
        if c in PALI_CONSONANTS or c == NIGGAHITA:
            tokens.append(("C", c))
        elif c in PALI_VOWELS:
            tokens.append(("V", c))
        else:
            tokens.append(("?", c))
        i += 1
    return tokens


def has_triple_consonant(word):
    """Regla 1: ¿Hay 3+ consonantes seguidas?"""
    tokens = _tokenize(word)
    cons_count = 0
    for typ, val in tokens:
        if typ == "C":
            cons_count += 1
            if cons_count >= 3:
                return True
        else:
            cons_count = 0
    return False


def has_consecutive_vowels(word):
    """Regla 2: ¿Hay vocales consecutivas?"""
    tokens = _tokenize(word)
    for i in range(len(tokens) - 1):
        if tokens[i][0] == "V" and tokens[i + 1][0] == "V":
            return True
    return False


def ends_in_consonant(word):
    """Regla 3: ¿Termina en consonante (que no sea ṃ)?"""
    if not word:
        return False
    last = word[-1]
    if last == NIGGAHITA:
        return False
    # Verificar si el último carácter es consonante
    tokens = _tokenize(word)
    if tokens and tokens[-1][0] == "C":
        return True
    return False


def has_invalid_cluster(word):
    """Regla 4: ¿Hay clusters de consonantes no válidos en Pali?"""
    # Buscar secuencias de 2 consonantes que no estén en VALID_CLUSTERS
    tokens = _tokenize(word)
    for i in range(len(tokens) - 1):
        if tokens[i][0] == "C" and tokens[i + 1][0] == "C":
            cluster = tokens[i][1] + tokens[i + 1][1]
            if cluster not in VALID_CLUSTERS:
                return True
    return False


def is_valid_pali(word):
    """Aplica todas las reglas. Retorna True si la palabra es Pali válido."""
    if has_triple_consonant(word):
        return False
    if has_consecutive_vowels(word):
        return False
    if ends_in_consonant(word):
        return False
    if has_invalid_cluster(word):
        return False
    return True


# ─── Test ───
if __name__ == "__main__":
    tests = [
        ("sukha", True),
        ("sukhā", True),
        ("dukkha", True),
        ("dukkkhā", False),  # triple consonante
        ("vedanā", True),
        ("vedana", True),
        ("vedanaa", False),  # vocales consecutivas
        ("bhikkhu", True),
        ("bhikkhus", False),  # termina en consonante (s)
        ("dhammaṃ", True),
        ("dhammam", False),  # termina en m (no ṃ)
        ("aā", False),  # vocales consecutivas
        ("buddha", True),
        ("buddhha", False),  # triple? ddh+h = ddhh — sí, 4 consonantes
        ("kamma", True),
        ("kammma", False),  # triple m
        ("cakkhu", True),
        ("cakkhhu", False),  # triple
        ("phasso", True),
        ("phassso", False),  # triple
        ("ariya", True),
        ("ariyā", True),
        ("sammā", True),
        ("micchā", True),
        ("paṭicca", True),
        ("paṭiccā", True),
    ]

    for word, expected in tests:
        result = is_valid_pali(word)
        ok = "✓" if result == expected else f"✗ (esperado: {expected})"
        print(f"  {word:20s} → {'válido' if result else 'inválido':8s} {ok}")

    print(f"\nReglas cargadas: {len(VALID_CLUSTERS)} clusters válidos")
