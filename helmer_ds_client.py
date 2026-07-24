#!/usr/bin/env python3
"""Cliente DeepSeek endurecido para Helmer (PTS↔CST).

Dos capas de validación algorítmica:
  1. validate_request()  — ANTES de enviar. Si falla → aborta (no toca la red).
  2. validate_response() — ANTES de integrar. Si falla → descarta (no propaga al núcleo).

Más: manejo de errores de red/API, timeout, reintentos con backoff, y una batería
de pruebas controladas (`--selftest`): conectividad, autenticación, formato de
request/response, manejo de errores y consistencia de salida (temperature=0).

Uso:
    python3 helmer_ds_client.py --selftest      # pruebas offline + (si hay key) live
    from helmer_ds_client import HelmerDSClient  # integración
"""
import json, os, re, sys, time, unicodedata
from dataclasses import dataclass, field

from helmer_ptscst import SYS  # system prompt canónico (idéntico al pipeline)

MODEL = 'deepseek-v4-flash'
BASE_URL = 'https://api.deepseek.com'
RESP_FMT = {'type': 'json_object'}

# --- límites de la capa de validación de ENTRADA ---
MIN_USER_CHARS = 20
MAX_USER_CHARS = 8000        # cota dura del payload de usuario
MAX_TOTAL_CHARS = 12000      # system + user
REQUIRED_MARKERS = ('PTS:', 'CST:')
MIN_SEG_CHARS = 10           # contenido mínimo tras cada marcador (campo obligatorio)

# --- límites de la capa de validación de SALIDA ---
ALLOWED_VERDICTS = {'APPROVE', 'REJECT'}
ALLOWED_KEYS = {'verdict', 'reason'}
MAX_REASON_CHARS = 300


# ───────────────────────── utilidades ─────────────────────────
def _utf8_ok(s: str):
    """UTF-8 válido, sin surrogates sueltos ni U+FFFD (encoding roto)."""
    try:
        s.encode('utf-8')
    except UnicodeEncodeError:
        return False, 'surrogate/encoding inválido'
    if '�' in s:
        return False, 'contiene U+FFFD (replacement char)'
    return True, ''

def _has_ctrl(s: str):
    """Caracteres de control salvo \\n \\t → anomalía."""
    return any(unicodedata.category(c) == 'Cc' and c not in '\n\t' for c in s)


# ───────────────── capa 1: validación de ENTRADA ─────────────────
def validate_request(payload: dict):
    """Devuelve (ok: bool, errors: list[str]). Si no ok → NO enviar."""
    e = []
    if not isinstance(payload, dict):
        return False, ['payload no es dict']

    # campos obligatorios y sus valores esperados
    if payload.get('model') != MODEL:
        e.append(f'model != {MODEL!r} (got {payload.get("model")!r})')
    if payload.get('temperature') != 0:
        e.append('temperature debe ser 0 (determinismo)')
    if payload.get('response_format') != RESP_FMT:
        e.append(f'response_format debe ser {RESP_FMT}')

    msgs = payload.get('messages')
    if not isinstance(msgs, list) or len(msgs) != 2:
        return False, e + ['messages debe ser lista de 2 (system,user)']
    roles = [m.get('role') for m in msgs]
    if roles != ['system', 'user']:
        e.append(f'roles deben ser [system,user] (got {roles})')

    sys_c = msgs[0].get('content', '')
    usr_c = msgs[1].get('content', '')
    if not isinstance(sys_c, str) or not isinstance(usr_c, str):
        return False, e + ['contents deben ser str']
    if sys_c != SYS:
        e.append('system prompt no coincide con SYS canónico')

    # estructura / longitud / encoding del mensaje de usuario
    n = len(usr_c)
    if n < MIN_USER_CHARS:
        e.append(f'user demasiado corto ({n}<{MIN_USER_CHARS})')
    if n > MAX_USER_CHARS:
        e.append(f'user excede cota ({n}>{MAX_USER_CHARS})')
    if len(sys_c) + n > MAX_TOTAL_CHARS:
        e.append(f'total excede cota ({len(sys_c)+n}>{MAX_TOTAL_CHARS})')
    ok, why = _utf8_ok(usr_c)
    if not ok:
        e.append(f'user encoding: {why}')
    if _has_ctrl(usr_c):
        e.append('user contiene caracteres de control')
    for mk in REQUIRED_MARKERS:
        if mk not in usr_c:
            e.append(f'falta marcador obligatorio {mk!r}')

    # campos obligatorios NO vacíos: el texto tras PTS:/CST: debe ser sustantivo
    m_pts = re.search(r'PTS:\s*(.*?)\s*(?:\bCST:|\Z)', usr_c, re.S)
    m_cst = re.search(r'CST:\s*(.*?)\s*(?:\bCollateX|\Z)', usr_c, re.S)
    if not m_pts or len(m_pts.group(1).strip()) < MIN_SEG_CHARS:
        e.append(f'campo PTS vacío o < {MIN_SEG_CHARS} chars')
    if not m_cst or len(m_cst.group(1).strip()) < MIN_SEG_CHARS:
        e.append(f'campo CST vacío o < {MIN_SEG_CHARS} chars')

    return (len(e) == 0), e


# ───────────────── capa 2: validación de SALIDA ─────────────────
def validate_response(raw: str):
    """Devuelve (ok, cleaned|None, errors). Si no ok → descartar, no propagar."""
    e = []
    if not isinstance(raw, str) or not raw.strip():
        return False, None, ['respuesta vacía o no-str']
    ok, why = _utf8_ok(raw)
    if not ok:
        return False, None, [f'encoding: {why}']
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as ex:
        return False, None, [f'JSON inválido: {ex}']
    if not isinstance(obj, dict):
        return False, None, ['no es objeto JSON']

    extra = set(obj) - ALLOWED_KEYS
    if extra:
        e.append(f'claves inesperadas: {sorted(extra)}')
    v = obj.get('verdict')
    if v not in ALLOWED_VERDICTS:
        e.append(f'verdict inválido: {v!r} (permitidos {sorted(ALLOWED_VERDICTS)})')
    r = obj.get('reason')
    if not isinstance(r, str):
        e.append('reason ausente o no-str')
    else:
        if not (1 <= len(r) <= MAX_REASON_CHARS):
            e.append(f'reason longitud fuera de rango (1..{MAX_REASON_CHARS})')
        if _has_ctrl(r):
            e.append('reason con caracteres de control')
        # anomalías: reason que solo repite el verdict, o parece eco del prompt
        if isinstance(v, str) and r.strip().upper() == v:
            e.append('reason == verdict (anómalo)')
        if re.search(r'(system|assistant|role"\s*:)', r, re.I):
            e.append('reason parece eco de prompt/estructura (anómalo)')

    if e:
        return False, None, e
    # salida saneada: solo las claves permitidas
    return True, {'verdict': v, 'reason': r}, []


# ───────────────── constructor de payload Helmer ─────────────────
def build_payload(pts: str, cst: str, variant_lines=None) -> dict:
    body = ['PTS:', pts[:1200], '', 'CST:', cst[:1200], '', 'CollateX (PTS|CST|DPD):']
    for line in (variant_lines or []):
        body.append('  ' + line)
    return {
        'model': MODEL, 'temperature': 0, 'response_format': RESP_FMT,
        'messages': [
            {'role': 'system', 'content': SYS},
            {'role': 'user', 'content': '\n'.join(body)},
        ],
    }


# ───────────────────────── cliente ─────────────────────────
@dataclass
class Result:
    ok: bool
    verdict: str = None
    reason: str = None
    stage: str = ''            # 'input'|'network'|'output'|'ok'
    errors: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


class HelmerDSClient:
    def __init__(self, api_key=None, timeout=30, max_retries=3):
        from openai import OpenAI
        self.timeout = timeout
        self.max_retries = max_retries
        self._cli = OpenAI(api_key=api_key or os.environ['DEEPSEEK_API_KEY'],
                           base_url=BASE_URL, timeout=timeout, max_retries=0)

    def call(self, payload: dict) -> Result:
        # capa 1: si la entrada es inválida, abortar sin tocar la red
        ok, errs = validate_request(payload)
        if not ok:
            return Result(False, stage='input', errors=errs)

        import openai
        last = None
        for attempt in range(self.max_retries):
            try:
                r = self._cli.chat.completions.create(**payload)
                raw = r.choices[0].message.content
                usage = getattr(r, 'usage', None)
                # capa 2: validar antes de integrar
                vok, cleaned, verrs = validate_response(raw)
                if not vok:
                    return Result(False, stage='output', errors=verrs,
                                  meta={'raw': (raw or '')[:200]})
                return Result(True, cleaned['verdict'], cleaned['reason'], 'ok',
                              meta={'attempts': attempt + 1,
                                    'in': getattr(usage, 'prompt_tokens', None),
                                    'out': getattr(usage, 'completion_tokens', None)})
            except (openai.APITimeoutError, openai.APIConnectionError,
                    openai.RateLimitError, openai.InternalServerError) as ex:
                last = f'{type(ex).__name__}: {str(ex)[:80]}'
                time.sleep(min(2 ** attempt, 8))            # backoff
            except openai.APIStatusError as ex:             # 4xx no reintentables
                return Result(False, stage='network',
                              errors=[f'{type(ex).__name__}: {str(ex)[:80]}'])
            except Exception as ex:
                return Result(False, stage='network',
                              errors=[f'inesperado {type(ex).__name__}: {str(ex)[:80]}'])
        return Result(False, stage='network', errors=[f'agotados reintentos: {last}'])


# ───────────────────────── pruebas controladas ─────────────────────────
def _p(name, ok, detail=''):
    print(f'  [{"PASS" if ok else "FAIL"}] {name}' + (f'  — {detail}' if detail else ''))
    return ok

def selftest():
    print('=' * 78)
    print('PRUEBAS CONTROLADAS — cliente DeepSeek endurecido')
    print('=' * 78)
    allok = True

    # ---- OFFLINE: capa de validación de ENTRADA ----
    print('\n[1] Validación de ENTRADA (offline):')
    good = build_payload('evam me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ',
                         'evaṃ me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ',
                         ['"a" | "b" | ortho'])
    allok &= _p('payload válido acepta', validate_request(good)[0])
    bad_variants = {
        'model erróneo': {**good, 'model': 'gpt-4'},
        'temperature≠0': {**good, 'temperature': 0.7},
        'sin response_format': {k: v for k, v in good.items() if k != 'response_format'},
        'user vacío': build_payload('', ''),
        'sin marcador PTS/CST': {**good, 'messages': [good['messages'][0],
                                 {'role': 'user', 'content': 'texto sin marcadores obligatorios aquí'}]},
        'user con control chars': {**good, 'messages': [good['messages'][0],
                                   {'role': 'user', 'content': 'PTS:\x00\nCST: x'}]},
    }
    for name, bad in bad_variants.items():
        allok &= _p(f'rechaza: {name}', validate_request(bad)[0] is False)

    # ---- OFFLINE: capa de validación de SALIDA ----
    print('\n[2] Validación de SALIDA (offline):')
    allok &= _p('JSON válido acepta',
                validate_response('{"verdict":"APPROVE","reason":"core matches"}')[0])
    bad_out = {
        'JSON roto': '{"verdict":"APPROVE",',
        'no-objeto': '"APPROVE"',
        'verdict inválido': '{"verdict":"MAYBE","reason":"x"}',
        'falta reason': '{"verdict":"APPROVE"}',
        'reason vacío': '{"verdict":"REJECT","reason":""}',
        'clave extra': '{"verdict":"APPROVE","reason":"x","evil":1}',
        'reason=verdict': '{"verdict":"APPROVE","reason":"APPROVE"}',
        'eco de prompt': '{"verdict":"APPROVE","reason":"role: system you are"}',
        'vacío': '',
    }
    for name, raw in bad_out.items():
        allok &= _p(f'descarta: {name}', validate_response(raw)[0] is False)

    # ---- LIVE (requiere DEEPSEEK_API_KEY) ----
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print('\n[3] LIVE: DEEPSEEK_API_KEY ausente — pruebas de red omitidas.')
        print('\n' + '=' * 78)
        print('RESULTADO OFFLINE:', 'TODO PASA ✓' if allok else 'HAY FALLOS ✗')
        return allok

    print('\n[3] LIVE contra api.deepseek.com:')
    cli = HelmerDSClient()

    # conectividad + auth + formato: un par claramente idéntico → APPROVE
    same = build_payload('evam me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ viharati jetavane',
                         'evaṃ me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ viharati jetavane',
                         ['"evam" | "evaṃ" | ortho'])
    r1 = cli.call(same)
    allok &= _p('conectividad+auth+formato (verdict válido)', r1.ok,
                f'{r1.verdict} / {r1.reason[:40] if r1.reason else r1.errors}'
                + (f'  [{r1.meta.get("in")}→{r1.meta.get("out")} tok]' if r1.ok else ''))

    # manejo de errores: modelo inexistente → error de API capturado, sin crash.
    # Llamada directa al SDK (saltándonos validate_request, que abortaría antes).
    import openai
    err_caught = False
    try:
        cli._cli.chat.completions.create(
            model='modelo-inexistente-xyz', temperature=0,
            response_format=RESP_FMT, messages=same['messages'])
    except openai.APIStatusError:
        err_caught = True
    except Exception:
        err_caught = True
    allok &= _p('manejo de error de API (modelo inválido capturado)', err_caught)

    # la capa de entrada aborta ANTES de red con payload inválido
    r_abort = cli.call({**same, 'temperature': 0.9})
    allok &= _p('capa entrada aborta sin tocar red', (not r_abort.ok) and r_abort.stage == 'input',
                f'stage={r_abort.stage}')

    # consistencia de salida: mismo input dos veces (temp=0) → mismo verdict
    r2 = cli.call(same)
    allok &= _p('consistencia (verdict estable temp=0)',
                r1.ok and r2.ok and r1.verdict == r2.verdict,
                f'{r1.verdict} == {r2.verdict}' if (r1.ok and r2.ok) else 'no evaluable')

    print('\n' + '=' * 78)
    print('RESULTADO:', 'TODO PASA ✓' if allok else 'HAY FALLOS ✗')
    return allok


if __name__ == '__main__':
    if '--selftest' in sys.argv or len(sys.argv) == 1:
        sys.exit(0 if selftest() else 1)
