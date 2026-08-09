"""
runner.py — Ejecuta una misión a través del grafo, de principio a 'done'.

Maneja el ciclo de interrupt/resume: cuando el grafo se congela en un gate,
el runner espera la decisión humana (IMAP) y reanuda con Command(resume=...).
Todo el estado vive en el checkpointer SQLite -> resumible tras crash.

Uso:
    python -m orchestrator.runner missions/active/<id>.yaml
"""
from __future__ import annotations
import sys, os, shutil, json, time, sqlite3
import yaml

from .graph import build_graph, MissionState, RateLimitPause, GatePending
from . import gates, metrics, control

# Motivos de aborto que MERECEN un reintento automático con estrategia revisada
# (Reflexion). Un gate rechazado o un abort humano NO se reintentan solos.
RETRYABLE_ABORTS = ("Máximo de iteraciones", "Atasco persistente", "Sin progreso",
                    "Límite de tiempo de pared")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "state")
CHECKPOINT_DB = os.path.join(STATE_DIR, "checkpoints.sqlite")

# 'Done' no falseable: toda misión exige >=1 check de MÁQUINA (no agent_judgment).
OBJECTIVE_CHECKS = {"file_exists", "http_status", "command_exit_zero", "file_contains"}


def validate_mission(m: dict) -> None:
    """Guardarraíl del verificador (el corazón). Como el handoff es auto-go (no revisas
    el yaml), validamos aquí que el 'done' no puede cerrarse solo con el juicio de un LLM."""
    for field in ("id", "title", "objective", "definition_of_done", "budget", "gates"):
        if not m.get(field):
            raise ValueError(f"mission inválida: falta el campo obligatorio '{field}'")
    dod = m["definition_of_done"]
    kinds = {d.get("verify", {}).get("type") for d in dod}
    if not (kinds & OBJECTIVE_CHECKS):
        raise ValueError(
            "mission inválida: la DoD necesita AL MENOS un check de máquina "
            f"{sorted(OBJECTIVE_CHECKS)}; agent_judgment no puede cerrar una misión solo.")


def load_mission(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        m = yaml.safe_load(f)
    validate_mission(m)
    return m


def mission_workspace(mission_id: str) -> str:
    ws = os.path.join(ROOT, "missions", "active", mission_id)
    os.makedirs(ws, exist_ok=True)
    return ws


def run_mission(path: str) -> None:
    m = load_mission(path)
    mid = m["id"]
    ws = mission_workspace(mid)
    os.makedirs(STATE_DIR, exist_ok=True)
    # ¿reanudación por rate-limit (hay _PAUSED) o arranque fresco? Si es fresco, borra
    # cualquier checkpoint viejo del mismo id para no reanudar estado obsoleto (re-run limpio).
    resuming = os.path.isfile(_paused_marker(ws))
    # ¿Reanudación por GATE (v1.3)? Si hay _GATE_PENDING y ya llegó la decisión, la
    # inyectamos al reanudar el grafo desde el checkpoint. Si aún no hay decisión, salimos
    # otra vez con 76 (seguimos esperando) sin gastar nada.
    gate_resume = None
    if os.path.isfile(_gate_pending_marker(ws)):
        dec = gates.poll_decision(mid)
        if dec is None:
            print(f"[runner] {mid}: gate aún sin respuesta; sigo esperando (exit 76)")
            sys.exit(76)
        gate_resume = {"approved": dec.approved, "instructions": dec.raw_reply}
        _clear_gate_pending(ws)
        _mark_gate_waiting(ws, False)
        control.push_log(mid, "gate", f"decisión recibida: {'GO' if dec.approved else 'NO'} -> reanudo")
    resuming = resuming or (gate_resume is not None)
    _clear_paused(ws)
    if not resuming:
        _clear_checkpoint(mid)
        # NONCE DE PROPIEDAD (v1.2, estilo ACME): único por intento. Si la misión
        # despliega algo, DEBE servirlo en $DEPLOY_URL/.well-known/agentos-proof.txt;
        # el verificador lo comprueba sin seguir redirects. Cierra el caso aval-TMS.
        try:
            import secrets
            with open(os.path.join(ws, "_PROOF_NONCE.txt"), "w", encoding="utf-8") as f:
                f.write(f"agentos-{mid}-{secrets.token_hex(12)}")
        except Exception:
            pass
    metrics.push_mission(mid, m.get("title", ""), "active", False)
    control.push_log(mid, "start", f"{'reanudada' if resuming else 'arrancada'}: {m.get('title','')}")

    graph_def, saver = build_graph(CHECKPOINT_DB)
    with saver as checkpointer:
        app = graph_def.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": mid}}

        # LECCIONES (v1.1): memoria entre misiones — top-K lecciones cuyo trigger matchea
        # el texto de esta misión, inyectadas al prompt del planner. Best effort.
        lessons_txt = ""
        try:
            from . import lessons
            lessons_txt = lessons.match(" ".join(str(m.get(k, "")) for k in ("title", "objective", "context")))
            if lessons_txt:
                control.push_log(mid, "lessons", f"inyectadas lecciones previas ({len(lessons_txt)} chars)")
        except Exception:
            pass

        init: MissionState = {
            "mission": m, "cwd": ws, "iteration": 0, "lessons_txt": lessons_txt,
            "log": [], "action_history": [], "stuck_strikes": 0,
            "spend_usd": 0.0, "done": False, "aborted": False,
        }

        # Primer arranque o reanudación: si ya hay checkpoint, invoke sin init lo retoma.
        try:
            result = _drive(app, init, config, mid, resume_payload=gate_resume)
        except GatePending:
            # GATE NO-BLOQUEANTE: salimos SIN cerrar la misión; el checkpoint queda intacto
            # y el watcher nos relanza cuando llegue el GO/NO. El [GATE] ya se envió (nodo
            # gate_notify). El proceso muere aquí -> ni cuelga el daemon ni gasta cuota.
            metrics.push_mission(mid, m.get("title", ""), "waiting_gate", False, note="esperando GO/NO")
            print(f"[runner] MISIÓN EN GATE: {mid} — proceso libera; espero decisión")
            sys.exit(76)  # el watcher deja el yaml en active/ y relanza al recibir decisión
        except RateLimitPause as e:
            # Pausa resumible: NO se finaliza, el checkpoint queda intacto.
            _mark_paused(ws, str(e), reset_at=float(getattr(e, "reset_at", 0) or 0))
            metrics.push_mission(mid, m.get("title", ""), "paused", False, note="rate-limit del plan")
            control.push_log(mid, "pause", "pausada por límite de uso del plan")
            print(f"[runner] MISIÓN PAUSADA: {mid} — límite de uso del plan")
            gates.send_gate(mid, "PAUSADA",
                            f"La misión '{m['title']}' se pausó por el límite de uso de tu plan Max "
                            f"({e}). El checkpoint queda intacto y no has perdido progreso; el watcher "
                            f"la retoma sola cuando la ventana de uso se resetee.")
            sys.exit(75)  # EX_TEMPFAIL: el watcher lo interpreta como 'reintentar luego'

        # Cierre
        spend = float(result.get("spend_usd", 0.0) or 0.0)
        iters = int(result.get("iteration", 0) or 0)
        url = _result_url(ws)
        if result.get("done"):
            _finalize(m, ws, ok=True, spend_usd=spend, iterations=iters, result_url=url)
            # F8: note="" limpia notas stale de pushes previos (p.ej. "timeout watcher"
            # de una ejecución anterior que quedó pegada a una misión luego completada).
            metrics.push_mission(mid, m.get("title", ""), "done", True, spend, iters, url, note="")
            control.push_log(mid, "done", f"COMPLETADA en {iters} vueltas" + (f" — {url}" if url else ""))
            print(f"[runner] MISIÓN COMPLETADA: {mid}")
            body = f"La misión '{m['title']}' pasó el verificador." + (f"\n\n🔗 {url}" if url else f"\nResultado en missions/done/{mid}/.")
            gates.send_gate(mid, "COMPLETADA", body)
            to = m.get("notify_email")
            if to and url:
                try:
                    gates._email_send_gate(mid, f"COMPLETADA — {url}", body, to=to)
                except Exception as e:
                    print(f"[runner] email notify falló: {e}")
            _learn(m, True, "", result, os.path.join(ROOT, "missions", "done", mid))
        else:
            reason = result.get("abort_reason", "desconocido")
            attempt = int(m.get("attempt", 1) or 1)
            retryable = any(k in (reason or "") for k in RETRYABLE_ABORTS)
            will_retry = retryable and attempt < 2
            _finalize(m, ws, ok=False, spend_usd=spend, iterations=iters, result_url=url,
                      note=reason, retry_requested=will_retry, attempt=attempt)
            dest = os.path.join(ROOT, "missions", "done", mid)
            pm = None
            if will_retry:
                # REFLEXION: post-mortem del intento 1 -> el watcher re-encola el intento 2
                # con contexto FRESCO + estrategia revisada. Humano solo si el 2º también cae.
                pm = _postmortem_safe(m, reason, result, dest)
                metrics.push_mission(mid, m.get("title", ""), "aborted", False, spend, iters, url,
                                     note=f"[intento 1/2 -> auto-retry] {reason}")
                control.push_log(mid, "retry", f"intento 1 falló ({reason}); post-mortem listo -> reintento automático")
                print(f"[runner] MISIÓN FALLIDA (intento 1): {mid} — reintento automático")
                gates.send_gate(mid, "🔁 REINTENTO AUTOMÁTICO",
                                f"'{m['title']}' falló el intento 1: {reason}\n\n"
                                f"Causa raíz: {(pm or {}).get('root_cause','?')}\n"
                                f"Estrategia intento 2: {(pm or {}).get('new_strategy','?')[:400]}\n\n"
                                f"Reintento en marcha; te aviso solo si también falla.")
            else:
                metrics.push_mission(mid, m.get("title", ""), "aborted", False, spend, iters, url, note=reason)
                control.push_log(mid, "abort", f"DETENIDA: {reason}")
                print(f"[runner] MISIÓN DETENIDA: {mid} — {reason}")
                extra = f" (intento {attempt} de 2; sin más reintentos automáticos)" if attempt >= 2 else ""
                gates.send_gate(mid, "DETENIDA", f"La misión '{m['title']}' se detuvo: {reason}{extra}")
            _learn(m, False, reason, result, dest)


def _learn(m: dict, ok: bool, reason: str, result: dict, dest: str) -> None:
    """LRN-01: destila ≤3 lecciones reutilizables al cerrar (best effort, nunca rompe).
    Cada lección se publica también a Supabase (level=lesson) -> sección Lecciones del
    dashboard: el aprendizaje es auditable sin tocar el Mac."""
    try:
        from . import lessons
        ls = lessons.distill(m, ok, reason, result.get("verifier_results", []), dest)
        n = lessons.save(m["id"], ls)
        for l in (ls or [])[:3]:
            if l.get("title") and l.get("lesson"):
                control.push_log(m["id"], "lesson",
                                 f"{l['title']} [{', '.join(l.get('triggers', [])[:5])}] — {l['lesson']}"[:1200])
        if n:
            print(f"[runner] {n} lección(es) destiladas")
    except Exception as e:
        print(f"[runner] distill lecciones falló (no crítico): {e}")


def _postmortem_safe(m: dict, reason: str, result: dict, dest: str):
    """Genera y persiste _POSTMORTEM.json en done/<id>/ (best effort con fallback)."""
    pm = None
    try:
        from . import lessons
        log_tail = "\n".join(str(x) for x in (result.get("log") or [])[-6:])
        pm = lessons.postmortem(m, reason, result.get("verifier_results", []), log_tail, dest)
    except Exception as e:
        print(f"[runner] post-mortem falló (uso fallback): {e}")
        pm = {"root_cause": reason[:300], "avoid": "repetir el mismo enfoque",
              "new_strategy": "Replantear desde cero atacando el motivo del aborto."}
    try:
        with open(os.path.join(dest, "_POSTMORTEM.json"), "w", encoding="utf-8") as f:
            json.dump(pm, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # post-mortem también a Supabase -> auditable desde el dashboard sin tocar el Mac
    try:
        control.push_log(m["id"], "postmortem",
                         f"CAUSA: {pm.get('root_cause','?')} | EVITAR: {pm.get('avoid','?')} | "
                         f"PLAN INTENTO 2: {pm.get('new_strategy','?')}"[:2500])
    except Exception:
        pass
    return pm


def _gate_pending_marker(ws: str) -> str:
    return os.path.join(ws, "_GATE_PENDING.json")


def _drive(app, init, config, mid, resume_payload=None) -> dict:
    """Avanza el grafo. GATES NO-BLOQUEANTES (v1.3): al toparse un interrupt (gate), NO se
    bloquea esperando horas; mira UNA vez si la decisión ya llegó y, si no, SALE del proceso
    (GatePending -> exit 76). El watcher relanza la misión cuando la decisión aparece,
    reanudando desde el checkpoint. Sobrevive a reinicios del Mac; no deja procesos colgados.
    resume_payload: si el watcher nos relanza con una decisión ya tomada, se inyecta aquí."""
    from langgraph.types import Command
    ws = os.path.join(ROOT, "missions", "active", mid)
    if resume_payload is not None:
        state = app.invoke(Command(resume=resume_payload), config=config)
    else:
        state = app.invoke(init, config=config)
    while True:
        snapshot = app.get_state(config)
        if not snapshot.next:           # no hay nodo pendiente -> terminó
            _clear_gate_pending(ws)
            return state
        # Interrupt pendiente (gate). ¿Ya hay decisión esperándonos? (una pasada, no bloquea)
        decision = gates.poll_decision(mid)
        if decision is None:
            # Nadie ha respondido aún -> persistir estado de espera y SALIR (exit 76).
            _mark_gate_pending(ws)
            _mark_gate_waiting(ws, True)   # el watcher no lo trata como cuelgue
            raise GatePending(f"gate pendiente en {mid}")
        _clear_gate_pending(ws)
        _mark_gate_waiting(ws, False)
        cmd_payload = {"approved": decision.approved, "instructions": decision.raw_reply}
        state = app.invoke(Command(resume=cmd_payload), config=config)


def _mark_gate_pending(ws: str) -> None:
    try:
        os.makedirs(ws, exist_ok=True)
        with open(_gate_pending_marker(ws), "w", encoding="utf-8") as f:
            json.dump({"gate_pending": True, "ts": time.time()}, f)
    except Exception:
        pass


def _clear_gate_pending(ws: str) -> None:
    try:
        p = _gate_pending_marker(ws)
        if os.path.isfile(p):
            os.remove(p)
    except Exception:
        pass


def _gate_waiting_marker(ws: str) -> str:
    return os.path.join(ws, "_WAITING_GATE")


def _mark_gate_waiting(ws: str, on: bool) -> None:
    """Señala al watcher que esta misión está bloqueada esperando una decisión humana
    (gate), no colgada. Mientras exista la marca, el watcher no aplica su timeout."""
    try:
        p = _gate_waiting_marker(ws)
        if on:
            os.makedirs(ws, exist_ok=True)
            open(p, "w").write(str(time.time()))
        elif os.path.isfile(p):
            os.remove(p)
    except Exception:
        pass


def _clear_checkpoint(mid: str) -> None:
    """Borra el checkpoint del thread para un arranque FRESCO. Sin esto, re-lanzar una
    misión ya ejecutada reanuda su estado viejo (started_at antiguo -> aborta por tope de
    tiempo al instante; iteración heredada). Solo se llama en arranque NO-pausa."""
    try:
        con = sqlite3.connect(CHECKPOINT_DB)
        for t in ("writes", "checkpoint_blobs", "checkpoints"):
            try: con.execute(f"DELETE FROM {t} WHERE thread_id=?", (mid,))
            except Exception: pass
        con.commit(); con.close()
    except Exception:
        pass


def _paused_marker(ws: str) -> str:
    return os.path.join(ws, "_PAUSED.json")


def _mark_paused(ws: str, reason: str, reset_at: float = 0.0) -> None:
    try:
        os.makedirs(ws, exist_ok=True)
        with open(_paused_marker(ws), "w", encoding="utf-8") as f:
            json.dump({"paused": True, "reason": reason[:300], "ts": time.time(),
                       "reset_at": reset_at}, f, ensure_ascii=False)
    except Exception:
        pass


def _clear_paused(ws: str) -> None:
    try:
        p = _paused_marker(ws)
        if os.path.isfile(p):
            os.remove(p)
    except Exception:
        pass


def _result_url(ws: str):
    """Lee la URL del deploy de cualquier fichero tipo *URL*.txt en el workspace, a CUALQUIER
    profundidad. Antes solo miraba la raíz con nombres fijos -> si el agente la dejaba en
    p.ej. aval/site/DEPLOY_URL.txt, la URL no se capturaba y no salía en el aviso."""
    import glob
    names = ("DEPLOYED_URL.txt", "DEPLOY_URL.txt", "URL.txt", "_URL.txt",
             "deployed_url.txt", "deploy_url.txt", "url.txt")
    cands = []
    for n in names:
        cands += glob.glob(os.path.join(ws, n))
        cands += glob.glob(os.path.join(ws, "**", n), recursive=True)
    for p in sorted(set(cands)):
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith("http"):
                    return line
        except Exception:
            pass
    return None


def _finalize(m: dict, ws: str, ok: bool, spend_usd: float = 0.0,
              iterations: int = 0, result_url=None, note=None,
              retry_requested: bool = False, attempt: int = 1) -> None:
    mid = m["id"]
    dest = os.path.join(ROOT, "missions", "done", mid)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.abspath(ws) != os.path.abspath(dest):
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.move(ws, dest)
    # registro (con coste, vueltas, url, motivo, y señal de auto-retry para el watcher)
    with open(os.path.join(dest, "_RESULT.json"), "w", encoding="utf-8") as f:
        json.dump({"id": mid, "ok": ok, "title": m["title"],
                   "spend_usd": round(spend_usd, 4), "iterations": iterations,
                   "result_url": result_url, "note": note,
                   "retry_requested": bool(retry_requested), "attempt": int(attempt)},
                  f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("uso: python -m orchestrator.runner <ruta_mission.yaml>")
        sys.exit(1)
    run_mission(sys.argv[1])


if __name__ == "__main__":
    main()
