#!/usr/bin/env python3
"""
watcher.py — El puente + lanzador. Vigila missions/inbox/, arranca el runner para
cada misión nueva, y RETOMA las que quedaron en pausa por límite de uso del plan.

EL BRIDGE (cómo cruza una misión desde un chat de Claude.ai al Mac):
  - REPO_SYNC="local" (por defecto): algo deja el yaml en missions/inbox/. En Cowork,
    cuando dices "continúalo solo", Claude escribe el mission.yaml (ya validado) DIRECTO
    en ~/Desktop/os/agent-os/missions/inbox/. Cero git, cero acoplamiento. Es el bridge.
  - REPO_SYNC="git" + REPO_DIR: para chats de Claude.ai SIN acceso al Mac. El watcher
    hace `git pull` del repo cada ciclo y copia los yaml de missions/inbox/ a la inbox
    local. (Usa credenciales de solo-lectura propias; NO el token del pipeline de artefactos.)

ORQUESTACIÓN:
  - Serie con prioridad: una misión a la vez; mayor `priority` en el yaml salta la cola.
  - Retoma pausadas: si una misión se pausó por rate-limit del plan (runner exit 75),
    queda en active/ con _PAUSED.json; el watcher la reintenta tras PAUSE_BACKOFF.
  - Coste: el SDK consume de tu cuota Max compartida -> serie protege tu Claude interactivo.
"""
from __future__ import annotations
import os, sys, time, json, subprocess, shutil, glob, urllib.request, sqlite3
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../agent-os
sys.path.insert(0, ROOT)  # para 'from orchestrator import gates' al correr como script


def _load_env_fallback() -> None:
    """RESILIENCIA .env: si el shell del plist no pudo hacer `source .env` (p.ej. TCC de
    macOS bloqueando ~/Desktop a launchd), el watcher lo carga él mismo desde ROOT/.env.
    No pisa variables ya presentes en el entorno. Sin esto, un fallo de source dejaba el
    daemon en bucle de reinicio silencioso (visto: 'bash: .env: Operation not permitted')."""
    path = os.path.join(ROOT, ".env")
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return
    loaded = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
            loaded += 1
    if loaded:
        print(f"[watcher] .env cargado por fallback interno ({loaded} variables)")


_load_env_fallback()  # ANTES de leer config del módulo (POLL, REPO_SYNC, etc.)
INBOX = os.path.join(ROOT, "missions", "inbox")
ACTIVE = os.path.join(ROOT, "missions", "active")
PROCESSED = os.path.join(ROOT, "missions", "_processed")
HELD = os.path.join(ROOT, "missions", "_held")          # misiones en hold desde el dashboard
CHECKPOINT_DB = os.path.join(ROOT, "state", "checkpoints.sqlite")
DONE_LEDGER = os.path.join(ROOT, "state", "done_ids.txt")  # idempotencia: id -> ya ejecutada


def _load_done() -> set:
    try:
        return set(x.strip() for x in open(DONE_LEDGER, encoding="utf-8") if x.strip())
    except Exception:
        return set()


def _mark_done(mid: str) -> None:
    """Registra que una misión ya corrió (idempotencia): no se re-ejecuta aunque su yaml
    reaparezca en el inbox (p.ej. tras un re-sync). El retry explícito la des-registra."""
    try:
        os.makedirs(os.path.dirname(DONE_LEDGER), exist_ok=True)
        if mid not in _load_done():
            with open(DONE_LEDGER, "a", encoding="utf-8") as f:
                f.write(mid + "\n")
    except Exception:
        pass


def _unmark_done(mid: str) -> None:
    s = _load_done(); s.discard(mid)
    try:
        with open(DONE_LEDGER, "w", encoding="utf-8") as f:
            f.write("".join(x + "\n" for x in sorted(s)))
    except Exception:
        pass


def _seed_ledger_from_history() -> None:
    """Al arrancar, marca como 'hechas' las misiones que ya están en _processed/ o done/.
    Idempotencia retroactiva: un re-sync que reañada esos yaml NO las re-ejecuta."""
    try:
        for y in glob.glob(os.path.join(PROCESSED, "*.yaml")):
            _mark_done(os.path.basename(y)[:-5])
        donedir = os.path.join(ROOT, "missions", "done")
        if os.path.isdir(donedir):
            for d in os.listdir(donedir):
                if os.path.isdir(os.path.join(donedir, d)):
                    _mark_done(d)
    except Exception:
        pass

def _version() -> str:
    try:
        return open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    except Exception:
        return "1.0"


REJECTED_LEDGER = os.path.join(ROOT, "state", "rejected_ids.txt")


def _load_rejected() -> set:
    try:
        return set(x.strip() for x in open(REJECTED_LEDGER, encoding="utf-8") if x.strip())
    except Exception:
        return set()


def _mark_rejected(mid: str) -> None:
    """Una misión rechazada por validación no se re-descarga ni re-notifica cada ciclo."""
    try:
        os.makedirs(os.path.dirname(REJECTED_LEDGER), exist_ok=True)
        if mid not in _load_rejected():
            with open(REJECTED_LEDGER, "a", encoding="utf-8") as f:
                f.write(mid + "\n")
    except Exception:
        pass


POLL = int(os.environ.get("WATCHER_POLL_SECONDS", "120"))
SELF_UPDATE = os.environ.get("SELF_UPDATE", "0") == "1"   # auto-recarga de código
SELF_UPDATE_SRC = os.path.expanduser(os.environ.get("SELF_UPDATE_SRC", "~/Desktop/os/agent-os"))
PAUSE_BACKOFF = int(os.environ.get("PAUSE_BACKOFF_SECONDS", "900"))  # 15 min: ventana de rate-limit
REPO_SYNC = os.environ.get("REPO_SYNC", "local")   # github_api | git | local
REPO_DIR = os.environ.get("REPO_DIR", "")
REPO_URL = os.environ.get("REPO_URL", "")          # solo modo git: auto-clona en REPO_DIR
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")    # modo github_api: "owner/repo"
MISSIONS_PATH = os.environ.get("MISSIONS_PATH", "missions/inbox")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # PAT con contents:read sobre el repo
# OBS-02: al terminar una misión, mover su yaml de missions/inbox a missions/_processed
# EN EL REPO (limpieza autorizada por Álvaro 2026-07-01, SOLO rutas bajo missions/).
REPO_MARK_PROCESSED = os.environ.get("REPO_MARK_PROCESSED", "1") == "1"
# F6 (2026-07-10): con la ventana de cuota cargada, NO arrancar misiones no urgentes
# (priority < QUOTA_DEFER_MIN_PRIORITY). Protege tu Claude interactivo: kit-bitacora
# corrió entera al 79-80% de la ventana en horario de trabajo.
QUOTA_DEFER_THRESHOLD = float(os.environ.get("QUOTA_DEFER_THRESHOLD", "0.85"))
QUOTA_DEFER_MIN_PRIORITY = int(os.environ.get("QUOTA_DEFER_MIN_PRIORITY", "10"))
QUOTA_STALE_SECONDS = int(os.environ.get("QUOTA_STALE_SECONDS", "1800"))  # foto >30min = ignorar


def _queue_note() -> str:
    """Snapshot JSON de la cola para el heartbeat -> el dashboard ve QUÉ hay pendiente
    (v1.1; antes el estado runtime era invisible desde fuera y engañaba a los auditores)."""
    try:
        q = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(INBOX, "*.yaml")))
        paused_ids = sorted(os.path.basename(os.path.dirname(p))
                            for p in glob.glob(os.path.join(ACTIVE, "*", "_PAUSED.json")))
        held_ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HELD, "*.yaml")))
        paused, held = len(paused_ids), len(held_ids)
        done_dir = os.path.join(ROOT, "missions", "done")
        last_done = ""
        if os.path.isdir(done_dir):
            ds = sorted((d for d in os.listdir(done_dir)
                         if os.path.isdir(os.path.join(done_dir, d))),
                        key=lambda d: os.path.getmtime(os.path.join(done_dir, d)))
            last_done = ds[-1] if ds else ""
        return json.dumps({"v": _version(), "cli": _CLI_VER, "queue": q[:10], "queued": len(q),
                           "paused": paused, "held": held,
                           "paused_ids": paused_ids[:5], "held_ids": held_ids[:5],
                           "last_done": last_done},
                          ensure_ascii=False)
    except Exception:
        return ""


def _gh_api(method: str, path: str, body: dict = None):
    """Llamada mínima a la API de GitHub (contents). Lanza si no hay token."""
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(body).encode() if body is not None else None, method=method,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "agentos-watcher",
                 "Authorization": f"Bearer {GITHUB_TOKEN}",
                 **({"Content-Type": "application/json"} if body is not None else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def _repo_archive_processed(name: str) -> None:
    """Mueve missions/inbox/<name> -> missions/_processed/<name> EN EL REPO puente.
    GUARDAS DURAS: solo con flag activo, solo modo github_api, y SOLO rutas que empiecen
    por missions/ (jamás toca artifacts/, posts/, etc.). Best effort: si falla, el ledger
    local de idempotencia sigue protegiendo; solo queda 'ruido' en el inbox remoto."""
    if not (REPO_MARK_PROCESSED and REPO_SYNC == "github_api" and GITHUB_REPO and GITHUB_TOKEN):
        return
    src = f"{MISSIONS_PATH}/{name}"
    dst = f"missions/_processed/{name}"
    if not (src.startswith("missions/") and dst.startswith("missions/")):
        return  # fuera de missions/ ni tocarlo
    try:
        cur = _gh_api("GET", f"/repos/{GITHUB_REPO}/contents/{src}")
        sha, content = cur.get("sha"), cur.get("content", "")
        if not sha:
            return
        _gh_api("PUT", f"/repos/{GITHUB_REPO}/contents/{dst}",
                {"message": f"agentos: processed {name}", "content": content.replace("\n", "")})
        _gh_api("DELETE", f"/repos/{GITHUB_REPO}/contents/{src}",
                {"message": f"agentos: clear inbox {name}", "sha": sha})
        print(f"[watcher] repo: {name} -> _processed/ (inbox remoto limpio)")
    except Exception as e:
        print(f"[watcher] repo archive {name} falló (no crítico): {e}")


def _seen(name: str) -> bool:
    """¿Ya conocemos esta misión? (en inbox/active/_processed o ya terminada en done)."""
    for d in (INBOX, ACTIVE, PROCESSED):
        if os.path.exists(os.path.join(d, name)):
            return True
    did = name[:-5] if name.endswith(".yaml") else name
    return os.path.isdir(os.path.join(ROOT, "missions", "done", did))


def _accept_mission(name: str, content: str, via: str) -> None:
    """Valida (misma barrera que el runner) y, si pasa, escribe la misión en la inbox local."""
    try:
        from orchestrator.runner import validate_mission
        validate_mission(yaml.safe_load(content))
    except Exception as e:
        print(f"[watcher] misión RECHAZADA ({name}): {e}")
        _mark_rejected(name[:-5] if name.endswith(".yaml") else name)
        try:
            from orchestrator import gates
            gates.notify(f"❌ Misión de claude.ai rechazada ({name}): {str(e)[:160]}\n"
                         f"(No se reintentará; corrige el yaml y súbelo con OTRO id.)")
        except Exception:
            pass
        return
    with open(os.path.join(INBOX, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[watcher] misión recibida ({via}): {name}")
    try:
        from orchestrator import gates
        gates.notify(f"📥 Misión recibida de claude.ai: {name[:-5]}")
    except Exception:
        pass


def _sync_github_api() -> None:
    """BRIDGE por API de GitHub (SIN clon, SIN auth de git): lista <repo>/<MISSIONS_PATH>
    y descarga los .yaml nuevos usando GITHUB_TOKEN (PAT contents:read). El más simple."""
    if not GITHUB_REPO:
        return
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agentos-watcher"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{MISSIONS_PATH}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            items = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[watcher] github API list falló: {e}")
        return
    done_ids = _load_done(); rejected = _load_rejected()
    for it in (items if isinstance(items, list) else []):
        name = it.get("name", "")
        if it.get("type") != "file" or not name.endswith(".yaml") or _seen(name):
            continue
        mid = name[:-5]
        if mid in rejected:
            continue   # rechazada antes: no re-descargar ni re-spamear
        if mid in done_ids:
            # ya ejecutada y el yaml sigue en el inbox remoto -> archívalo allí y no bajes nada
            _repo_archive_processed(name)
            continue
        try:
            with urllib.request.urlopen(urllib.request.Request(it["download_url"], headers=headers), timeout=30) as r:
                content = r.read().decode("utf-8")
        except Exception as e:
            print(f"[watcher] descarga {name} falló: {e}")
            continue
        _accept_mission(name, content, "API")


def _sync_repo() -> None:
    """Dispatcher del bridge según REPO_SYNC: github_api (recomendado) | git | local."""
    if REPO_SYNC == "github_api":
        _sync_github_api()
    elif REPO_SYNC == "git":
        _sync_git()
    # local: nada (Cowork u otro proceso deja el yaml en la inbox)


def _sync_git() -> None:
    """BRIDGE GIT (alternativa pesada): clona/pull el repo + valida + copia a inbox."""
    if not REPO_DIR:
        return
    # git NUNCA debe pedir credenciales interactivas en el daemon (colgaría). Falla rápido.
    genv = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"}
    # auto-clonado: si REPO_DIR no es un repo y tenemos REPO_URL, clónalo (sin pasos manuales)
    if not os.path.isdir(os.path.join(REPO_DIR, ".git")):
        if not REPO_URL:
            return
        try:
            print(f"[watcher] clonando {REPO_URL} -> {REPO_DIR}")
            os.makedirs(os.path.dirname(REPO_DIR) or ".", exist_ok=True)
            r = subprocess.run(["git", "clone", "--depth", "1", REPO_URL, REPO_DIR],
                               check=False, timeout=300, capture_output=True, text=True, env=genv)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip()[:200])
        except Exception as e:
            print(f"[watcher] clone falló: {e}")
            try:
                from orchestrator import gates
                gates.notify(f"⚠️ No pude clonar el repo puente ({REPO_URL}). "
                             f"Revisa la auth de git en el Mac (gh auth login / SSH). El bridge "
                             f"local y Telegram siguen funcionando.")
            except Exception:
                pass
            return
    try:
        subprocess.run(["git", "-C", REPO_DIR, "pull", "--quiet"],
                       check=False, timeout=120, env=genv)
    except Exception as e:
        print(f"[watcher] git pull falló: {e}"); return
    src = os.path.join(REPO_DIR, "missions", "inbox")
    if not os.path.isdir(src):
        return
    for y in sorted(glob.glob(os.path.join(src, "*.yaml"))):
        name = os.path.basename(y)
        if _seen(name):
            continue
        try:
            from orchestrator.runner import validate_mission
            m = yaml.safe_load(open(y, "r", encoding="utf-8"))
            validate_mission(m)               # rechaza DoD sin check de máquina (no falseable)
        except Exception as e:
            print(f"[watcher] misión de repo RECHAZADA ({name}): {e}")
            try:
                from orchestrator import gates
                gates.notify(f"❌ Misión de claude.ai rechazada ({name}): {str(e)[:160]}")
            except Exception:
                pass
            continue
        shutil.copy2(y, INBOX)
        print(f"[watcher] misión recibida de repo: {name}")
        try:
            from orchestrator import gates
            gates.notify(f"📥 Misión recibida de claude.ai: {name[:-5]}")
        except Exception:
            pass


def _recover_orphans() -> None:
    """AUTO-RECUPERACIÓN al arrancar: una misión en active/ SIN _PAUSED.json y SIN
    _WAITING_GATE quedó huérfana (el daemon murió o fue matado mientras la corría).
    Antes esto dejaba un fantasma 'active' para siempre que bloqueaba la percepción del
    sistema. Ahora la abandonamos limpio y avisamos, para que el daemon siga sano."""
    for yaml_path in glob.glob(os.path.join(ACTIVE, "*.yaml")):
        mid = os.path.basename(yaml_path)[:-5]
        ws = os.path.join(ACTIVE, mid)
        if os.path.isfile(os.path.join(ws, "_PAUSED.json")):
            continue   # pausada legítima por rate-limit -> la retoma _next_paused()
        if os.path.isfile(os.path.join(ws, "_WAITING_GATE")):
            continue   # esperaba GO/NO; la dejamos para que se reanude
        try:
            shutil.move(yaml_path, os.path.join(PROCESSED, os.path.basename(yaml_path)))
        except Exception:
            pass
        print(f"[watcher] huérfana recuperada (abandonada tras reinicio): {mid}")
        try:
            from orchestrator import gates, metrics
            gates.notify(f"♻️ Al arrancar encontré la misión '{mid}' a medias (el daemon se "
                         f"reinició mientras corría). La he abandonado para no bloquear; "
                         f"si la quieres, vuelve a lanzarla.")
            metrics.push_mission(mid, mid, "aborted", False, note="huérfana tras reinicio del daemon")
        except Exception:
            pass


def _priority(yaml_path: str) -> int:
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return int((yaml.safe_load(f) or {}).get("priority", 0))
    except Exception:
        return 0


def _next_paused() -> str | None:
    """Una misión pausada (active/<id>/_PAUSED.json) cuyo backoff ya pasó -> retomar."""
    now = time.time()
    best = None
    for marker in glob.glob(os.path.join(ACTIVE, "*", "_PAUSED.json")):
        mid = os.path.basename(os.path.dirname(marker))
        yaml_path = os.path.join(ACTIVE, mid + ".yaml")
        if not os.path.isfile(yaml_path):
            continue
        try:
            pj = json.load(open(marker, encoding="utf-8"))
            ts = pj.get("ts", 0)
            reset_at = float(pj.get("reset_at", 0) or 0)
        except Exception:
            ts, reset_at = 0, 0
        # v1.2: si el SDK nos dio el reset exacto de la ventana, esperar hasta ese
        # momento (+60s de margen) en vez de martillear cada PAUSE_BACKOFF.
        if reset_at and now < reset_at + 60:
            continue
        if now - ts >= PAUSE_BACKOFF:
            # prioriza la pausada de mayor priority
            if best is None or _priority(yaml_path) > _priority(best):
                best = yaml_path
    return best


def _next_gate() -> str | None:
    """GATE NO-BLOQUEANTE (v1.3): misión en active/ con _GATE_PENDING cuya decisión YA
    llegó -> relanzarla (el runner reanuda desde el checkpoint e inyecta el GO/NO).
    Mientras no haya decisión, el daemon sigue con otras misiones sin bloquearse."""
    for marker in glob.glob(os.path.join(ACTIVE, "*", "_GATE_PENDING.json")):
        mid = os.path.basename(os.path.dirname(marker))
        yaml_path = os.path.join(ACTIVE, mid + ".yaml")
        if not os.path.isfile(yaml_path):
            continue
        try:
            from orchestrator import gates
            if gates.poll_decision(mid) is not None:
                return yaml_path   # hay GO/NO esperando -> relanzar y reanudar
        except Exception:
            pass
    return None


def _quota_hot() -> str:
    """F6: '' si se puede arrancar; si no, el motivo del defer. Lee state/quota.json
    (lo escribe engine con cada RateLimitEvent). Foto vieja o reset ya pasado -> frío."""
    try:
        q = json.load(open(os.path.join(ROOT, "state", "quota.json"), encoding="utf-8"))
    except Exception:
        return ""
    now = time.time()
    if now - float(q.get("ts", 0)) > QUOTA_STALE_SECONDS:
        return ""
    reset_at = float(q.get("reset_at", 0) or 0)
    if reset_at and now > reset_at:
        return ""
    util = float(q.get("utilization", 0) or 0)
    if util >= QUOTA_DEFER_THRESHOLD:
        extra = f" (reset {time.strftime('%H:%M', time.localtime(reset_at))})" if reset_at else ""
        return f"ventana de cuota al {util:.0%}{extra}"
    return ""


def _claim_next_inbox() -> str | None:
    os.makedirs(INBOX, exist_ok=True); os.makedirs(ACTIVE, exist_ok=True); os.makedirs(PROCESSED, exist_ok=True)
    candidates = glob.glob(os.path.join(INBOX, "*.yaml"))
    if not candidates:
        return None
    # mayor prioridad primero; a igualdad, por nombre (fecha en el slug -> FIFO)
    candidates.sort(key=lambda p: (-_priority(p), os.path.basename(p)))
    done = _load_done()
    hot = _quota_hot()
    for src in candidates:
        mid = os.path.basename(src)[:-5]
        # F6: cuota caliente -> las misiones no urgentes esperan en el inbox (las
        # priority >= QUOTA_DEFER_MIN_PRIORITY, p.ej. auto-retries, sí pasan).
        if hot and _priority(src) < QUOTA_DEFER_MIN_PRIORITY:
            global _LAST_QUOTA_NOTICE
            if time.time() - _LAST_QUOTA_NOTICE > 1800:
                _LAST_QUOTA_NOTICE = time.time()
                print(f"[watcher] defer por cuota: {mid} espera ({hot})")
                try:
                    from orchestrator import control
                    control.push_log("system", "quota", f"defer: {mid} espera — {hot}")
                except Exception:
                    pass
            continue
        if mid in done:
            # IDEMPOTENCIA: ya ejecutada -> sácala del inbox SIN re-correr (evita el
            # 're-arranque' de misiones viejas que reaparecen tras un re-sync).
            try:
                shutil.move(src, os.path.join(PROCESSED, os.path.basename(src)))
            except Exception:
                try: os.remove(src)
                except Exception: pass
            continue
        dst = os.path.join(ACTIVE, os.path.basename(src))
        shutil.move(src, dst)  # claim atómico: salir de inbox
        return dst
    return None


def _clear_checkpoint(mid: str) -> None:
    """Borra el checkpoint del thread para que un retry empiece de CERO (no reanude)."""
    try:
        con = sqlite3.connect(CHECKPOINT_DB)
        for t in ("writes", "checkpoint_blobs", "checkpoints"):
            try: con.execute(f"DELETE FROM {t} WHERE thread_id=?", (mid,))
            except Exception: pass
        con.commit(); con.close()
    except Exception:
        pass


def _find_yaml(mid: str):
    for base in (INBOX, ACTIVE, PROCESSED, HELD):
        p = os.path.join(base, mid + ".yaml")
        if os.path.isfile(p):
            return p
    return None


def _apply_command(cmd: dict) -> str:
    """Ejecuta un comando del dashboard que NO sea 'abortar la misión en curso'
    (eso lo hace _run en caliente). Devuelve texto de resultado."""
    from orchestrator import metrics, control
    act = cmd.get("action", ""); mid = (cmd.get("mission_id") or "").strip()
    args = cmd.get("args") or {}
    if act in ("freeze", "unfreeze"):
        control.set_frozen(act == "freeze")
        return f"daemon {'congelado' if act=='freeze' else 'descongelado'}"
    if act == "priority" and mid:
        p = os.path.join(INBOX, mid + ".yaml")
        if os.path.isfile(p):
            m = yaml.safe_load(open(p, encoding="utf-8")) or {}
            m["priority"] = int(args.get("priority", 100))
            yaml.safe_dump(m, open(p, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
            return f"prioridad {mid} -> {m['priority']}"
        return f"{mid} no está en cola"
    if act in ("hold", "unhold") and mid:
        src = os.path.join(INBOX if act == "hold" else HELD, mid + ".yaml")
        dstdir = HELD if act == "hold" else INBOX
        if os.path.isfile(src):
            os.makedirs(dstdir, exist_ok=True)
            shutil.move(src, os.path.join(dstdir, mid + ".yaml"))
            return f"{mid} {'en hold' if act=='hold' else 'reanudada'}"
        return f"{mid} no disponible para {act}"
    if act == "enqueue":
        # v1.2 (dashboard v3): crear una misión desde el navegador. El yaml viene en
        # args.yaml, pasa por la MISMA validación que el resto (DoD de máquina
        # obligatoria) y cae en la inbox local. Protegido por la contraseña del canal.
        raw = (args or {}).get("yaml", "")
        try:
            m = yaml.safe_load(raw)
            from orchestrator.runner import validate_mission
            validate_mission(m)
            nid = str(m.get("id", "")).strip()
            if not nid:
                return "enqueue: falta id"
            if _seen(nid + ".yaml") or nid in _load_done():
                return f"enqueue: {nid} ya existe o ya se ejecutó (usa retry)"
            os.makedirs(INBOX, exist_ok=True)
            with open(os.path.join(INBOX, nid + ".yaml"), "w", encoding="utf-8") as f:
                f.write(raw)
            try:
                from orchestrator import gates
                gates.notify(f"📥 Misión encolada desde el dashboard: {nid}")
            except Exception:
                pass
            return f"enqueue: {nid} encolada"
        except Exception as e:
            return f"enqueue: yaml inválido — {str(e)[:200]}"
    if act == "retry" and mid:
        y = _find_yaml(mid)
        if not y:
            return f"sin yaml para reintentar {mid}"
        _unmark_done(mid)   # permite que vuelva a correr (anula la idempotencia para este id)
        _clear_checkpoint(mid)
        for d in (os.path.join(ACTIVE, mid), os.path.join(ROOT, "missions", "done", mid)):
            if os.path.isdir(d):
                try: shutil.rmtree(d)
                except Exception: pass
        os.makedirs(INBOX, exist_ok=True)
        shutil.move(y, os.path.join(INBOX, mid + ".yaml"))
        return f"{mid} reencolada de cero"
    if act == "abort" and mid:
        y = _find_yaml(mid)
        if y:
            os.makedirs(PROCESSED, exist_ok=True)
            shutil.move(y, os.path.join(PROCESSED, mid + ".yaml"))
        d = os.path.join(ACTIVE, mid)
        if os.path.isdir(d):
            try: shutil.rmtree(d)
            except Exception: pass
        metrics.push_mission(mid, mid, "aborted", False, note="abortada desde el dashboard")
        return f"{mid} abortada"
    return f"acción ignorada: {act}"


def _consume_commands(active_mid: str = None) -> bool:
    """Aplica comandos pendientes del dashboard. Devuelve True si hay que MATAR la misión
    en curso (abort de active_mid). approve/reject_gate se dejan para el runner (gates.py)."""
    try:
        from orchestrator import control
        cmds = control.fetch_pending_commands()
    except Exception:
        return False
    kill = False
    for cmd in cmds:
        act = cmd.get("action"); mid = (cmd.get("mission_id") or "").strip()
        if act in ("approve_gate", "reject_gate"):
            continue  # los consume el runner mientras espera el gate
        if act == "abort" and mid and mid == active_mid:
            kill = True
        else:
            try:
                print(f"[watcher] cmd {act} {mid}: {_apply_command(cmd)}")
            except Exception as e:
                print(f"[watcher] cmd {act} error: {e}")
        try:
            control.finish_command(cmd["id"])
        except Exception:
            pass
    return kill


def _run(mission_path: str) -> int:
    print(f"[watcher] lanzando misión: {mission_path}")
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)  # forzar plan, no API key
    try:
        from orchestrator import gates
        gates.notify(f"▶️ Ejecutando misión: {os.path.basename(mission_path)[:-5]}")
    except Exception:
        pass
    # BACKSTOP DE AUTONOMÍA: ninguna misión puede bloquear el daemon para siempre.
    # Lanzamos el runner como subproceso y lo vigilamos: si lleva demasiado tiempo SIN
    # avanzar y NO está esperando un gate (marca _WAITING_GATE), lo matamos y seguimos.
    timeout_s = int(os.environ.get("WATCHER_RUNNER_TIMEOUT_SECONDS", "7200"))  # 2h
    mid = os.path.basename(mission_path)[:-5]
    gate_marker = os.path.join(ACTIVE, mid, "_WAITING_GATE")
    proc = subprocess.Popen(
        [sys.executable, "-m", "orchestrator.runner", mission_path],
        cwd=ROOT, env=env)
    start = time.time()
    killed = False
    kill_reason = None
    while True:
        try:
            rc = proc.wait(timeout=15)
            break
        except subprocess.TimeoutExpired:
            at_gate = os.path.exists(gate_marker)
            if at_gate:
                start = time.time()   # esperando humano (gate): no es cuelgue, reinicia el reloj
            elif time.time() - start > timeout_s:
                kill_reason = "timeout"
            # comandos del dashboard (abortar ESTA misión en caliente)
            try:
                if _consume_commands(mid):
                    kill_reason = "abort"
            except Exception:
                pass
            # latido para el panel de sistema (Supabase) + fichero local
            _touch_heartbeat()
            try:
                from orchestrator import control
                control.push_heartbeat("waiting_gate" if at_gate else "running",
                                       active_mission=mid, frozen=control.is_frozen(),
                                       note=_queue_note())
            except Exception:
                pass
            if kill_reason:
                proc.kill()
                try:
                    proc.wait(timeout=10)
                except Exception:
                    pass
                killed = True
                rc = 124
                break
    if killed:
        from orchestrator import gates, metrics
        if kill_reason == "abort":
            print(f"[watcher] misión {mid} abortada desde el dashboard")
            note = "abortada desde el dashboard"
            msg = f"🛑 Misión {mid} abortada desde el dashboard. Sigo con la siguiente."
        else:
            print(f"[watcher] misión {mid} colgada >{timeout_s//60}min; matada")
            note = f"timeout watcher >{timeout_s//60}min"
            msg = (f"⏱️ Misión {mid} colgada >{timeout_s//60} min sin avanzar. "
                   f"La maté y sigo con la siguiente.")
        try: gates.notify(msg)
        except Exception: pass
        try: metrics.push_mission(mid, mid, "aborted", False, note=note)
        except Exception: pass
    if rc == 75:
        # PAUSADA por rate-limit: dejar el yaml en active/, retomar tras backoff.
        print(f"[watcher] misión pausada (límite de uso); reintento en ~{PAUSE_BACKOFF}s")
        return rc
    if rc == 76:
        # GATE NO-BLOQUEANTE (v1.3): el runner liberó el proceso mientras espera GO/NO.
        # Dejar el yaml en active/; _next_gate() la relanza en cuanto llegue la decisión.
        # El daemon queda LIBRE para procesar otras misiones mientras tanto.
        print(f"[watcher] misión {mid} en gate; proceso liberado, espero decisión humana")
        return rc
    # terminada (done/aborted): el runner ya movió el workspace a done/
    try:
        shutil.move(mission_path, os.path.join(PROCESSED, os.path.basename(mission_path)))
    except Exception:
        pass
    _mark_done(mid)   # idempotencia: corre UNA vez; no re-arranca si el yaml reaparece
    if not _maybe_auto_retry(mid):
        _repo_archive_processed(mid + ".yaml")   # inbox remoto limpio (OBS-02)
    return rc


def _assets_summary(ws: str, max_chars: int = 900) -> str:
    """F4 (2026-07-10): inventario de lo que el intento 1 DEJÓ HECHO (ficheros y URLs),
    para que el intento 2 no re-descubra/re-suba lo que ya existe (kit-bitacora attempt 2
    re-encontró credenciales y re-subió vídeos que ya estaban en Cloudinary)."""
    lines = []
    try:
        urls = []
        for base, _dirs, files in os.walk(ws):
            for fn in files:
                p = os.path.join(base, fn)
                rel = os.path.relpath(p, ws)
                if rel.startswith(("_LOG", "_RESULT", "_POSTMORTEM")):
                    continue
                try:
                    size = os.path.getsize(p)
                except Exception:
                    size = 0
                lines.append(f"- {rel} ({size}B)")
                if "URL" in fn.upper() and fn.lower().endswith(".txt") and size < 4096:
                    try:
                        for l in open(p, encoding="utf-8", errors="ignore"):
                            l = l.strip()
                            if l.startswith("http"):
                                urls.append(f"  -> {rel}: {l}")
                    except Exception:
                        pass
            if len(lines) > 60:
                break
        out = "FICHEROS YA CREADOS POR EL INTENTO 1 (en done/<id>-attempt1; NO los rehagas,\n"               "reutiliza sus resultados — URLs subidas, deploys hechos, credenciales ya localizadas):\n"
        out += "\n".join(lines[:60] + urls)
        return out[:max_chars]
    except Exception:
        return ""


def _maybe_auto_retry(mid: str) -> bool:
    """AUT-01 (Reflexion): si el runner dejó retry_requested en done/<mid>/_RESULT.json y
    fue el intento 1, re-encola el intento 2 con el post-mortem inyectado y contexto
    FRESCO (checkpoint limpio). El workspace del intento 1 se conserva como -attempt1."""
    dest = os.path.join(ROOT, "missions", "done", mid)
    try:
        res = json.load(open(os.path.join(dest, "_RESULT.json"), encoding="utf-8"))
    except Exception:
        return False
    if not (res.get("retry_requested") and int(res.get("attempt", 1)) < 2):
        return False
    try:
        pm = {}
        try:
            pm = json.load(open(os.path.join(dest, "_POSTMORTEM.json"), encoding="utf-8"))
        except Exception:
            pass
        ypath = os.path.join(PROCESSED, mid + ".yaml")
        if not os.path.isfile(ypath):
            return False
        m = yaml.safe_load(open(ypath, encoding="utf-8")) or {}
        m["attempt"] = 2
        assets = _assets_summary(dest)
        m["retry_notes"] = ((f"Causa raíz intento 1: {pm.get('root_cause','?')}\n"
                             f"Evitar: {pm.get('avoid','?')}\n"
                             f"Estrategia revisada: {pm.get('new_strategy','?')}")[:1600]
                            + (("\n\n" + assets) if assets else ""))
        try:
            if assets:
                with open(os.path.join(dest, "_ASSETS.md"), "w", encoding="utf-8") as f:
                    f.write(assets + "\n")
        except Exception:
            pass
        m["priority"] = max(int(m.get("priority", 0) or 0), 10)  # el retry no espera a la cola
        # conservar evidencia del intento 1 y dejar el terreno limpio para el 2
        arch = dest + "-attempt1"
        if os.path.isdir(arch):
            shutil.rmtree(arch)
        shutil.move(dest, arch)
        _unmark_done(mid)
        _clear_checkpoint(mid)
        os.makedirs(INBOX, exist_ok=True)
        yaml.safe_dump(m, open(os.path.join(INBOX, mid + ".yaml"), "w", encoding="utf-8"),
                       allow_unicode=True, sort_keys=False)
        try:
            os.remove(ypath)
        except Exception:
            pass
        print(f"[watcher] auto-retry: {mid} re-encolada (intento 2, estrategia revisada)")
        return True
    except Exception as e:
        print(f"[watcher] auto-retry {mid} falló (queda como DETENIDA): {e}")
        return False


def _process_commands() -> bool:
    """Atiende un '/idea ...' de Telegram cuando el watcher está OCIOSO: lo destila en
    misión (dispatcher) y lo encola. Solo cuando no hay misión corriendo, para no chocar
    con el polling de gates del runner."""
    try:
        from orchestrator import gates
        idea = gates.next_command(timeout=2)
    except Exception as e:
        print(f"[watcher] telegram poll error: {e}")
        return False
    if not idea:
        return False
    print(f"[watcher] /idea recibida: {idea[:80]}")
    try:
        gates.notify(f"💡 Idea recibida, destilando en misión…\n«{idea[:200]}»")
        from dispatcher import handle_idea
        msg = handle_idea(idea)
    except Exception as e:
        msg = f"❌ No pude convertir la idea en misión válida: {e}"
    try:
        gates.notify(msg)
    except Exception:
        pass
    return True


def _touch_heartbeat() -> None:
    """Escribe state/watcher_heartbeat.txt cada ciclo: liveness LOCAL comprobable
    (lo usa el check 'heartbeat-fresh' y sirve aunque Supabase no esté disponible)."""
    try:
        os.makedirs(os.path.join(ROOT, "state"), exist_ok=True)
        with open(os.path.join(ROOT, "state", "watcher_heartbeat.txt"), "w") as f:
            f.write(f"{int(time.time())} {time.strftime('%Y-%m-%dT%H:%M:%S')} pid={os.getpid()}\n")
    except Exception:
        pass


def _self_update() -> None:
    """AUTO-RECARGA (solo si SELF_UPDATE=1 y el daemon está IDLE): sincroniza el CÓDIGO desde
    SELF_UPDATE_SRC (sin tocar state/missions/.venv/.git) y, si cambió algún .py, se RE-LANZA
    para cargarlo — así no hace falta `deploy_runtime.sh` a mano. Si la fuente está en ~/Desktop,
    el proceso necesita Acceso a Disco Completo (TCC). Valida que compila antes de recargar."""
    if not SELF_UPDATE:
        return
    # guarda de seguridad: la fuente debe ser un árbol AgentOS válido (evita un --delete fatal)
    if not os.path.isfile(os.path.join(SELF_UPDATE_SRC, "bin", "watcher.py")):
        return
    # CIRUGÍA EN CURSO: si la fuente tiene _SYNC_HOLD, alguien (Cowork) está editando
    # varios ficheros interdependientes. NO sincronizar hasta que lo retire -> el deploy
    # entra ATÓMICO (todo el set a la vez), nunca un estado a medias.
    if os.path.isfile(os.path.join(SELF_UPDATE_SRC, "_SYNC_HOLD")):
        return
    try:
        r = subprocess.run(
            ["rsync", "-ai", "--delete",   # -a preserva mtimes -> no re-transfiere lo igual (sin bucle)
             "--exclude", ".venv", "--exclude", ".git", "--exclude", "state",
             "--exclude", "missions", "--exclude", "__pycache__", "--exclude", "*.pyc",
             SELF_UPDATE_SRC.rstrip("/") + "/", ROOT + "/"],
            capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"[watcher] self-update: rsync falló ({e})"); return
    changed = [l for l in (r.stdout or "").splitlines()
               if l.strip() and (l.strip().endswith(".py") or "requirements.txt" in l)]
    if not changed:
        return
    print(f"[watcher] self-update: {len(changed)} fichero(s) de código cambiaron")
    # NO recargar en un estado roto: comprobar que el código nuevo compila
    core = [os.path.join(ROOT, p) for p in
            ("bin/watcher.py", "orchestrator/graph.py", "orchestrator/runner.py",
             "orchestrator/engine.py", "orchestrator/control.py", "orchestrator/metrics.py",
             "orchestrator/gates.py", "orchestrator/verifier.py")]
    chk = subprocess.run([sys.executable, "-m", "py_compile", *[c for c in core if os.path.isfile(c)]],
                         capture_output=True, text=True)
    if chk.returncode != 0:
        print(f"[watcher] self-update: código nuevo NO compila, no recargo:\n{chk.stderr[:300]}")
        return
    if any("requirements.txt" in l for l in changed):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                            os.path.join(ROOT, "requirements.txt")], timeout=300)
        except Exception:
            pass
    try:
        from orchestrator import gates
        gates.notify(f"🔄 AgentOS se auto-actualizó ({len(changed)} ficheros) y se recarga.")
    except Exception:
        pass
    print("[watcher] self-update: recargando proceso con el código nuevo…")
    os.execv(sys.executable, [sys.executable, os.path.join(ROOT, "bin", "watcher.py")])


_LAST_CONSOLIDATE = 0.0
_LAST_QUOTA_NOTICE = 0.0


def _maybe_consolidate_lessons() -> None:
    """CONSOLIDADOR de memoria (v1.3, patrón sleep-time): 1x cada 24h, cuando el daemon
    está OCIOSO, poda duplicados y exceso de lecciones. Solo aquí se edita la memoria en
    bloque (las misiones solo AÑADEN) -> nada corrompe las lecciones a mitad de misión."""
    global _LAST_CONSOLIDATE
    if time.time() - _LAST_CONSOLIDATE < 86400:
        return
    _LAST_CONSOLIDATE = time.time()
    try:
        from orchestrator import lessons, control
        r = lessons.consolidate()
        if r.get("removed"):
            control.push_log("system", "lesson",
                             f"consolidación de memoria: {r['before']}→{r['after']} lecciones "
                             f"({r['removed']} podadas)")
            print(f"[watcher] lecciones consolidadas: {r}")
    except Exception as e:
        print(f"[watcher] consolidación falló (no crítico): {e}")


def _rotate_logs() -> None:
    """OBS-03: logs del watcher >5MB rotan a .1 (copytruncate: launchd mantiene el fd)."""
    for n in ("watcher.out.log", "watcher.err.log"):
        p = os.path.join(ROOT, "state", n)
        try:
            if os.path.isfile(p) and os.path.getsize(p) > 5 * 1024 * 1024:
                shutil.copy2(p, p + ".1")
                open(p, "w").close()
                print(f"[watcher] log rotado: {n} -> {n}.1")
        except Exception:
            pass


def _cli_version() -> str:
    """Versión del CLI de Claude Code (groundwork gates defer, v1.2): defer/resume
    requiere CLI >= 2.1.89. Se loguea y va al heartbeat para decidir el upgrade de
    gates CON datos, sin adivinar."""
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=15)
        out = (r.stdout or r.stderr or "").strip()
        import re as _re
        m = _re.search(r"(\d+\.\d+\.\d+)", out)
        return m.group(1) if m else (out[:20] or "?")
    except Exception:
        return "?"


def _validate_config() -> None:
    """ROB-03: fail-fast VISIBLE. Cada feature declara sus env vars; si faltan, warning
    claro (una vez) en vez de fallos silenciosos a mitad de misión."""
    features = {
        "telegram (gates/avisos)": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
        "supabase (dashboard)": ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"],
        "bridge github_api": (["GITHUB_REPO", "GITHUB_TOKEN"] if REPO_SYNC == "github_api" else []),
        "vercel (deploys)": ["VERCEL_TOKEN"],
        "auth plan Max": ["CLAUDE_CODE_OAUTH_TOKEN"],
    }
    missing = {feat: [v for v in vs if not os.environ.get(v)]
               for feat, vs in features.items()}
    missing = {k: v for k, v in missing.items() if v}
    if not missing:
        print("[watcher] config OK: todas las features tienen sus variables")
        return
    msg = "; ".join(f"{feat}: faltan {','.join(vs)}" for feat, vs in missing.items())
    print(f"[watcher] ⚠️ CONFIG INCOMPLETA -> {msg} (el resto sigue funcionando)")
    try:
        from orchestrator import gates
        gates.notify(f"⚠️ AgentOS arrancó con config incompleta: {msg}")
    except Exception:
        pass


_CLI_VER = "?"


def main() -> None:
    global _CLI_VER
    _CLI_VER = _cli_version()
    print(f"[watcher] AgentOS v{_version()} (claude CLI {_CLI_VER}) vigilando {INBOX} cada {POLL}s "
          f"(sync={REPO_SYNC}, backoff_pausa={PAUSE_BACKOFF}s)")
    _rotate_logs()
    _validate_config()
    _recover_orphans()   # auto-recuperación: limpia misiones a medias de un reinicio previo
    _seed_ledger_from_history()   # idempotencia: no re-ejecutar lo que ya está hecho
    setup_msg = ""
    try:
        from orchestrator import control
        setup_msg = control.ensure_schema()   # crea/parcha tablas de control (commands+heartbeat)
        print(f"[watcher] supabase: {setup_msg}")
        control.push_heartbeat("starting", frozen=control.is_frozen(), note=_queue_note())
    except Exception as e:
        print(f"[watcher] supabase setup error: {e}")
    try:
        from orchestrator import gates
        gates.notify(f"👀 AgentOS arrancado. Inbox + Telegram + comandos del dashboard (sync={REPO_SYNC}). {setup_msg}")
    except Exception:
        pass
    while True:
        try:
            _touch_heartbeat()           # liveness local cada ciclo
            _self_update()               # auto-recarga de código si cambió (re-exec; solo idle)
            _sync_repo()
            _consume_commands()          # comandos del dashboard (idle): abort/retry/priority/hold/freeze
            frozen = False
            try:
                from orchestrator import control
                frozen = control.is_frozen()
                # AUTO-UNFREEZE por TTL: un freeze olvidado no puede parar el sistema para
                # siempre (visto: _FROZEN del 21-jun congeló el daemon días). Pasadas
                # FREEZE_TTL_HOURS (def. 24h) se descongela solo y avisa.
                if frozen:
                    ttl_h = float(os.environ.get("FREEZE_TTL_HOURS", "24"))
                    flag = os.path.join(ROOT, "state", "_FROZEN")
                    age_h = (time.time() - os.path.getmtime(flag)) / 3600 if os.path.isfile(flag) else 0
                    if age_h > ttl_h:
                        control.set_frozen(False)
                        frozen = False
                        print(f"[watcher] auto-unfreeze: _FROZEN llevaba {age_h:.1f}h (TTL {ttl_h}h)")
                        try:
                            from orchestrator import gates
                            gates.notify(f"🧊➡️▶️ Auto-unfreeze: el daemon llevaba congelado "
                                         f"{age_h:.0f}h (> TTL {ttl_h:.0f}h). Reanudo la cola. "
                                         f"Si querías mantenerlo parado, manda 'freeze' otra vez.")
                        except Exception:
                            pass
            except Exception:
                pass
            # freeze global: el daemon no coge nada nuevo NI retoma, solo late.
            # Orden: 1) gate con decisión lista (reanuda ya) 2) pausada por rate-limit
            # 3) inbox. Los gates sin decisión NO bloquean: se saltan hasta que llegue.
            nxt = None if frozen else (_next_gate() or _next_paused() or _claim_next_inbox())
            if nxt:
                _run(nxt)
            elif _process_commands():    # ocioso: atiende /idea de Telegram (bridge)
                continue
            else:
                _maybe_consolidate_lessons()   # mantenimiento de memoria 1x/día en idle
                try:
                    from orchestrator import control
                    control.push_heartbeat("frozen" if frozen else "idle", frozen=frozen,
                                           note=_queue_note())
                except Exception:
                    pass
                time.sleep(POLL)
        except KeyboardInterrupt:
            print("[watcher] parado"); break
        except Exception as e:
            print(f"[watcher] error de ciclo: {e}")
            time.sleep(POLL)


if __name__ == "__main__":
    main()
