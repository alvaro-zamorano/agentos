"""
verifier.py — El antídoto anti-abandono.

El loop NO decide solo que terminó. Este verificador comprueba cada criterio de la
Definition-of-Done contra evidencia OBJETIVA. Sin verde aquí, el grafo no cierra.

Tipos de verificación:
  - file_exists        : ¿existe la ruta?
  - http_status        : ¿la URL devuelve el status esperado?
  - command_exit_zero  : ¿el comando sale con código 0?
  - file_contains      : ¿el fichero contiene el substring esperado?
  - agent_judgment     : juicio de un subagente FRESCO (contexto limpio) contra una rúbrica.
"""
from __future__ import annotations
import os, subprocess, urllib.request, time
from dataclasses import dataclass
from .engine import run_agent

MACHINE_TYPES = {"file_exists", "http_status", "command_exit_zero", "file_contains"}


def _deploy_url(cwd: str):
    """URL REAL desplegada: cualquier *URL*.txt del workspace (a cualquier profundidad).
    Lección aval-landing: verificar una URL ASUMIDA puede dar verde contra el sitio de
    OTRO. El planner escribe DEPLOY_URL.txt; la DoD usa $DEPLOY_URL y aquí se resuelve."""
    import glob as _g
    names = ("DEPLOYED_URL.txt", "DEPLOY_URL.txt", "URL.txt", "_URL.txt",
             "deployed_url.txt", "deploy_url.txt", "url.txt")
    cands = []
    for n in names:
        cands += _g.glob(os.path.join(cwd, n)) + _g.glob(os.path.join(cwd, "**", n), recursive=True)
    for p in sorted(set(cands)):
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith("http"):
                    return line
        except Exception:
            pass
    return None


def _resolve_target(target: str, cwd: str):
    """Sustituye $DEPLOY_URL por la URL real del workspace. ('' si no hay URL aún)."""
    if "$DEPLOY_URL" not in (target or ""):
        return target, None
    url = _deploy_url(cwd)
    if not url:
        return None, "sin DEPLOY_URL.txt en el workspace (el agente aún no desplegó o no escribió la URL real)"
    return target.replace("$DEPLOY_URL", url), None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Prueba de propiedad SIN seguir redirects (lección ACME/Google: un redirect
    cross-domain permitiría apuntar el check a un host ajeno)."""
    def redirect_request(self, *a, **k):
        return None


def _ownership_check(cwd: str) -> "CheckResult | None":
    """PRUEBA DE PROPIEDAD (v1.2, estilo ACME HTTP-01): el runner generó un nonce en
    <ws>/_PROOF_NONCE.txt; el sitio desplegado debe servirlo EXACTO en
    $DEPLOY_URL/.well-known/agentos-proof.txt. Cierra la clase de falso positivo
    'URL asumida que resulta ser de otro' (caso aval-TMS): el nonce es de esta misión
    y no puede existir en un sitio que el agente no controla. Autoritativo.
    Devuelve None si la misión no usa deploy (sin nonce o sin DEPLOY_URL.txt)."""
    try:
        nonce = open(os.path.join(cwd, "_PROOF_NONCE.txt"), encoding="utf-8").read().strip()
    except Exception:
        return None
    if not nonce:
        return None
    base = _deploy_url(cwd)
    if not base:
        return None
    proof_url = base.rstrip("/") + "/.well-known/agentos-proof.txt"
    opener = urllib.request.build_opener(_NoRedirect)
    last = ""
    for attempt in range(3):
        try:
            req = urllib.request.Request(proof_url, headers={"User-Agent": "agentos-verifier"})
            with opener.open(req, timeout=20) as r:
                body = r.read(4096).decode("utf-8", "replace").strip()
            if body == nonce:
                return CheckResult("_ownership", True,
                                   f"propiedad probada: {proof_url} sirve el nonce de esta misión")
            last = f"{proof_url} sirve otro contenido ({body[:40]!r}) — ese sitio NO es el nuestro o falta publicar el nonce"
        except Exception as e:
            last = f"{proof_url} -> {e} (¿olvidaste publicar .well-known/agentos-proof.txt con el contenido de _PROOF_NONCE.txt?)"
        if attempt < 2:
            time.sleep(6)
    return CheckResult("_ownership", False, last)


@dataclass
class CheckResult:
    dod_id: str
    passed: bool
    evidence: str


def _file_exists(target: str, cwd: str) -> CheckResult:
    p = os.path.join(cwd, target) if not os.path.isabs(target) else target
    ok = os.path.isfile(p)
    return CheckResult("", ok, f"file_exists {p} -> {ok}")


def _http_status(target: str, expected: str) -> CheckResult:
    # Reintentos: un deploy recién hecho (Vercel) puede tardar en propagar -> no fallar
    # a la primera. 3 intentos con backoff antes de dar el check por fallido.
    last = ""
    for attempt in range(3):
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "agentos-verifier"})
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
            if str(code) == str(expected or 200):
                return CheckResult("", True, f"GET {target} -> {code}" + (f" (intento {attempt+1})" if attempt else ""))
            last = f"GET {target} -> {code} (esperado {expected or 200})"
        except Exception as e:
            last = f"GET {target} -> ERROR {e}"
        if attempt < 2:
            time.sleep(6)
    return CheckResult("", False, last + " (tras 3 intentos)")


def _command_exit_zero(target: str, cwd: str) -> CheckResult:
    try:
        r = subprocess.run(target, shell=True, cwd=cwd, capture_output=True, timeout=120)
        ok = r.returncode == 0
        return CheckResult("", ok, f"$ {target} -> exit {r.returncode}")
    except Exception as e:
        return CheckResult("", False, f"$ {target} -> ERROR {e}")


def _file_contains(target: str, expected: str, cwd: str) -> CheckResult:
    p = os.path.join(cwd, target) if not os.path.isabs(target) else target
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        ok = (expected or "") in content
        return CheckResult("", ok, f"file_contains {p} ~ {expected!r} -> {ok}")
    except Exception as e:
        return CheckResult("", False, f"file_contains {p} -> ERROR {e}")


async def _agent_judgment(rubric: str, cwd: str, objective: str) -> CheckResult:
    """Subagente fresco: lee el workspace y juzga contra la rúbrica. Devuelve PASS/FAIL."""
    prompt = (
        "Eres un VERIFICADOR independiente y estricto. No construyas nada, solo juzga.\n"
        f"Objetivo de la misión: {objective}\n\n"
        f"Rúbrica de aceptación:\n{rubric}\n\n"
        "Inspecciona los ficheros relevantes del directorio de trabajo. Luego responde "
        "EXACTAMENTE con una línea que empiece por 'PASS:' o 'FAIL:' seguida de la razón. "
        "Sé escéptico: si hay cifras sin fuente o afirmaciones vagas, es FAIL."
    )
    res = await run_agent(
        prompt,
        system_prompt="Verificador escéptico e independiente. Evidencia antes que afirmaciones. Solo lectura.",
        cwd=cwd,
        allowed_tools=["Read", "Glob", "Grep"],   # READ-ONLY: el juez NO toca artefactos/tests (anti reward-hacking)
        max_turns=10,
        permission_mode="default",
        model="sonnet",                            # v1.2: el juez es ASESOR -> sonnet basta y
    )                                              # ahorra cuota opus (research 2026-07-02)
    text = res.text.strip()
    passed = text.upper().lstrip().startswith("PASS")
    return CheckResult("", passed, text[:500])


async def verify_dod(dod: list[dict], cwd: str, objective: str) -> tuple[bool, list[CheckResult]]:
    """Comprueba la DoD. CLAVE: los checks de MÁQUINA son la puerta (autoritativos); el
    `agent_judgment` es ASESOR — informa calidad pero NO bloquea el cierre. Antes el juez
    bloqueaba como un check duro, y como la calidad es subjetiva las misiones daban vueltas
    infinitas (aval-v2 a 8/8 con el sitio vivo, aval-landing, tetris…). Ahora: si lo de
    máquina pasa, la misión cierra; el juez solo se ejecuta entonces (una vez, no en cada
    vuelta -> ni loops ni gasto de opus runaway), y su veredicto queda como nota."""
    results: list[CheckResult] = []
    judgments: list[dict] = []
    # PROPIEDAD (autoritativa): solo aplica si la misión desplegó ($DEPLOY_URL en uso)
    uses_deploy = any("$DEPLOY_URL" in str(i.get("verify", {}).get("target", "")) for i in dod)
    if uses_deploy:
        own = _ownership_check(cwd)
        if own is not None:
            results.append(own)
    for item in dod:
        t = item["verify"]["type"]
        if t == "agent_judgment":
            judgments.append(item); continue
        v = item["verify"]
        tgt, terr = _resolve_target(v.get("target", ""), cwd)
        if terr:
            r = CheckResult("", False, f"$DEPLOY_URL sin resolver: {terr}")
        elif t == "file_exists":
            r = _file_exists(tgt, cwd)
        elif t == "http_status":
            r = _http_status(tgt, v.get("expected", "200"))
        elif t == "command_exit_zero":
            r = _command_exit_zero(tgt, cwd)
        elif t == "file_contains":
            r = _file_contains(tgt, v.get("expected", ""), cwd)
        else:
            r = CheckResult("", False, f"tipo de verificación desconocido: {t}")
        r.dod_id = item["id"]
        results.append(r)

    machine_ok = all(r.passed for r in results)   # <- la PUERTA real

    # El juez solo cuando lo de máquina ya pasa (no malgastar opus en cada vuelta) y NUNCA bloquea.
    for item in judgments:
        if machine_ok:
            r = await _agent_judgment(item["verify"].get("rubric", ""), cwd, objective)
            r.evidence = "(asesor · no bloquea) " + r.evidence
        else:
            r = CheckResult("", False, "(asesor) sin evaluar: faltan checks de máquina")
        r.dod_id = item["id"]
        results.append(r)

    return machine_ok, results   # el juicio NO afecta a machine_ok
