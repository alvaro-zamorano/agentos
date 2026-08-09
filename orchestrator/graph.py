"""
graph.py — Orquestador LangGraph.

Grafo de estados:  plan -> bookkeep -> verify -> route
  route:  done?           -> END (cierre + mover a missions/done)
          gate pendiente?  -> interrupt (congela vivo, email, espera GO)
          no-progreso/topes-> END (aborta, avisa)
          si no            -> plan (otra vuelta)

Checkpointing en SQLite (SqliteSaver): cada paso persiste el estado. Si el Mac
se reinicia, se retoma con el mismo thread_id desde el último checkpoint.
Los gates usan interrupt(): el grafo se detiene SIN gastar crédito; al recibir GO
se reanuda con Command(resume=...).

EJECUCIÓN SÍNCRONA (a propósito): el grafo corre con .invoke()/sync SqliteSaver,
no con .ainvoke(). Motivo verificado (jun 2026, langgraph 1.2.5): interrupt() lee
el contexto del runnable vía un contextvar que NO se propaga en ejecución async
bajo Python < 3.11 (get_config -> 'outside of a runnable context'), y el
SqliteSaver síncrono no soporta métodos async (NotImplementedError). La ruta
síncrona funciona en 3.10 y 3.11+. Las llamadas async del SDK/verificador se
puentean con run_sync() dentro de cada nodo (loop efímero por paso).
"""
from __future__ import annotations
import os, json, hashlib, time, asyncio
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command

from .engine import run_agent
from .verifier import verify_dod
from . import gates, metrics, control, stuckdetect


def run_sync(coro):
    """Drive an async coroutine to completion from a synchronous graph node.
    Sync .invoke() runs nodes in the main thread with no active event loop, so a
    short-lived asyncio.run() is safe and isolates each SDK/verifier call."""
    return asyncio.run(coro)


def mlog(ws: str, kind: str, **payload) -> None:
    """AUDIT TRAIL (v1.1): registro COMPLETO por misión en <workspace>/_LOG.jsonl.
    A diferencia del stream a Supabase (truncado, para el dashboard), aquí va TODO:
    la salida íntegra de cada vuelta, cada verify, cada atasco. El fichero viaja con
    el workspace a missions/done/<id>/ -> auditar una misión fallida = leer un jsonl."""
    try:
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind}
        rec.update(payload)
        os.makedirs(ws, exist_ok=True)
        with open(os.path.join(ws, "_LOG.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


class RateLimitPause(Exception):
    """Se topó el límite de uso del plan Max. NO es un fallo de la misión: se pausa
    el grafo (el checkpoint queda intacto) y el watcher la retoma cuando la ventana
    de uso del plan se resetee. Distinto de 'aborted' (que sí cierra la misión)."""


class GatePending(Exception):
    """GATE NO-BLOQUEANTE (v1.3): la misión espera una decisión humana (GO/NO). En vez de
    bloquear el proceso durante horas/días, el runner SALE (exit 76) dejando el checkpoint
    intacto; el watcher relanza la misión en cuanto llega la decisión. Sobrevive a reinicios
    del Mac (el estado del interrupt vive en SqliteSaver, no en RAM)."""


# ---------------------------------------------------------------- estado
class MissionState(TypedDict, total=False):
    mission: dict                       # la misión cargada del yaml
    cwd: str                            # workspace de la misión
    iteration: int
    last_action: str
    last_error: bool                    # la última vuelta acabó en error del SDK
    log: Annotated[list, operator.add]  # se acumula
    state_hashes: list                  # legado (v1.0); sustituido por action_history
    action_history: list                # entradas stuckdetect.make_entry() por vuelta
    stuck_strikes: int                  # atascos detectados (1º -> replan, 2º -> abort)
    stuck_note: str                     # feedback anti-atasco para la vuelta siguiente
    lessons_txt: str                    # lecciones de misiones previas (inyecta el runner)
    spend_usd: float                    # estimación acumulada
    last_cost_usd: float                # coste real de la última vuelta (lo acumula bookkeep)
    started_at: float                   # epoch del arranque (tope wall_clock_hours)
    verifier_results: list
    dod_counts: list                    # nº de checks ✓ por verify (regla de convergencia F3)
    done: bool
    aborted: bool
    abort_reason: str
    pending_gate: dict                  # {subject, body} si hay gate
    last_human: str                     # respuesta humana inyectada


# (v1.1) _hash_state eliminado: el no-progreso lo decide orchestrator/stuckdetect.py
# (multi-patrón: error_streak / repeat_action / ping_pong, con firma normalizada).
# El hash literal no detectó el bucle de aval-landing (15x "[SDK ERROR]", $9.30).


# ---------------------------------------------------------------- nodos
def node_plan(state: MissionState) -> MissionState:
    m = state["mission"]
    it = state.get("iteration", 0) + 1
    dod_txt = "\n".join(f"- [{d['id']}] {d['check']}" for d in m["definition_of_done"])
    human = state.get("last_human", "")
    # Realimentación del verificador: si la vuelta anterior falló checks, el agente DEBE
    # verlos para autocorregirse. Sin esto, un check estricto haría loop infinito.
    fails = [r for r in state.get("verifier_results", []) if not r.get("passed")]
    verifier_feedback = (
        "RESULTADO DEL VERIFICADOR (vuelta anterior) — el sistema NO cerrará hasta que "
        "estos checks pasen con evidencia objetiva. Corrige EXACTAMENTE esto:\n"
        + "\n".join(f"- {r['id']}: {r['evidence']}" for r in fails) + "\n\n"
    ) if fails else ""
    # ANTI-ATASCO (v1.1): si el stuck-detector saltó, la vuelta siguiente DEBE replantear.
    stuck_note = state.get("stuck_note", "")
    stuck_feedback = (
        f"⚠️ ATASCO DETECTADO ({stuck_note}). Tu enfoque actual NO avanza. CAMBIA de "
        "estrategia RADICALMENTE: relee la DoD, cuestiona tus supuestos (¿la ruta existe?, "
        "¿el comando está instalado?, ¿la URL es la correcta?), y ataca por un camino "
        "DISTINTO al que repetías. Prohibido repetir la misma acción.\n\n"
    ) if stuck_note else ""
    # REFLEXION (v1.1): intento 2 tras post-mortem del intento 1 (lo inyecta el watcher).
    attempt = int(m.get("attempt", 1) or 1)
    retry_feedback = (
        f"ESTE ES EL INTENTO {attempt}. POST-MORTEM DEL INTENTO ANTERIOR (síguelo):\n"
        f"{m.get('retry_notes','')}\n\n"
    ) if attempt >= 2 and m.get("retry_notes") else ""
    prompt = (
        f"MISIÓN: {m['objective']}\n\nCONTEXTO: {m.get('context','')}\n\n"
        f"DEFINITION OF DONE (lo que debe ser verdad para terminar):\n{dod_txt}\n\n"
        f"RESTRICCIONES: {'; '.join(m.get('constraints', []))}\n\n"
        + state.get("lessons_txt", "")
        + retry_feedback
        + stuck_feedback
        + verifier_feedback +
        f"Estás en la vuelta {it}. Tu WORKSPACE es el directorio de trabajo ACTUAL (.). "
        "Lo hecho hasta ahora vive ahí.\n"
        "REGLAS DE WORKSPACE (obligatorias):\n"
        "- Trabaja SOLO dentro de tu directorio actual. NO subas a directorios padre, NO "
        "uses rutas que empiecen por 'missions/', NO crees/muevas/borres nada en "
        "missions/active|done|inbox ni en el resto del repo. Mover tu propio workspace lo ROMPE.\n"
        "- El entregable principal debe llamarse EXACTAMENTE como pida la DoD (p.ej. DOSSIER.md) "
        "y vivir en tu directorio actual. El sistema ya lo moverá a missions/done al cerrar.\n"
        "- Los checks de la DoD que buscan un substring (p.ej. 'Competidores', 'Pricing') son "
        "LITERALES: usa encabezados claros con esas palabras EXACTAS, sin numerar "
        "(escribe '## Competidores', no '## 2. Competidores GEO').\n"
        + (f"INSTRUCCIÓN HUMANA NUEVA: {human}\n" if human else "")
        + "Ejecuta el SIGUIENTE paso concreto hacia la DoD. Crea/edita ficheros reales "
          "en tu directorio actual.\n"
          "GATES — pide aprobación (una línea que empiece por 'GATE:') SOLO en estos casos:\n"
          "- GASTAR DINERO: comprar dominio, API de pago, publicidad, subir de plan.\n"
          "- IRREVERSIBLE-GRAVE: borrar datos, publicar a una audiencia real, o enviar email a terceros.\n"
          "- CAPTCHA / OTP / 2FA: agrúpalos y pídelos.\n"
          "TODO LO DEMÁS ES AUTÓNOMO, incluido desplegar a una URL pública gratis "
          "(p.ej. *.vercel.app) y crear/empujar repos de GitHub (públicos o privados): "
          "NO pidas gate para eso, hazlo.\n"
          "WORKAROUND-FIRST (política de autonomía): si un camino está bloqueado (URL/nombre "
          "ocupado, comando ausente, API caída, permiso denegado), NO te pares ni preguntes: "
          "busca un RODEO (nombre alternativo, otra herramienta equivalente, otra fuente, otra "
          "ruta) que cumpla la MISMA DoD, y documenta el cambio en el workspace (p.ej. la URL "
          "real en DEPLOY_URL.txt). Escalar al humano es el ÚLTIMO recurso, solo si NINGÚN "
          "rodeo puede cumplir la DoD.\n"
          "Si despliegas algo, escribe SIEMPRE la URL final real en DEPLOY_URL.txt (la DoD "
          "puede referirse a ella como $DEPLOY_URL).\n"
          "PRUEBA DE PROPIEDAD (obligatoria si despliegas): tu workspace tiene _PROOF_NONCE.txt. "
          "El sitio desplegado DEBE servir ese contenido EXACTO en /.well-known/agentos-proof.txt "
          "(p.ej. copia el fichero a public/.well-known/agentos-proof.txt antes de deployar). "
          "El verificador lo comprueba; sin nonce servido, la misión NO cierra.\n"
          "Si no hay gate, actúa y al final resume en una línea que empiece por 'DONE-STEP:'."
    )
    try:
        control.push_log(m["id"], "step", f"⏳ vuelta {it} en curso (máx "
                         f"{m['budget'].get('max_turns_per_iter', 30)} turnos del SDK)…",
                         node="plan", iteration=it)
    except Exception:
        pass
    res = run_sync(run_agent(
        prompt,
        system_prompt=(
            "Agente ejecutor autónomo. Acción > narración. Una acción por vuelta.\n"
            "RUTAS (macOS/TCC): trabaja SOLO dentro de tu directorio actual y de ~/agentos. "
            "NUNCA accedas a ~/Desktop, ~/Documents ni ~/Downloads — macOS los bloquea y lanza "
            "diálogos de permisos. El código fuente de AgentOS está en ~/agentos (NO en "
            "~/Desktop). Para publicar el repo, usa el código de ~/agentos.\n"
            "NO TE SUICIDES: NUNCA reinicies, recargues, mates ni pares el daemon/watcher que "
            "te está EJECUTANDO (nada de `launchctl unload/load/kickstart` sobre "
            "com.alvaro.agentos, ni `kill` del proceso watcher/python): te abortarías a ti "
            "mismo a media misión. Si tu objetivo es 'arreglar el watcher', EDITA los ficheros "
            "y deja una nota en el workspace; el operador lo recarga aparte.\n"
            "ANTI-CUELGUE (CRÍTICO): NUNCA ejecutes comandos que no terminen solos — nada de "
            "servidores en primer plano (`npm run dev`, `vercel dev`, `python -m http.server`, "
            "`next dev`), watchers, ni procesos que se quedan a la escucha. Para DESPLEGAR usa "
            "siempre el modo no-interactivo (`npx vercel --yes --prod ...`), nunca el dev server. "
            "Si un comando puede pedir confirmación/input, pásale el flag que lo evita (`--yes`, "
            "`-y`, `--force`) o envuélvelo en `timeout 120 <cmd>`. Para comprobar que un deploy "
            "responde usa `curl -sf` (que termina), no abras un navegador ni un servidor.\n"
            "PUBLICAR: tienes el CLI de Vercel (usa VERCEL_TOKEN del entorno; "
            "`npx vercel --yes --prod --scope=wcoach24s-projects`). "
            "BACKEND: Supabase — herramientas mcp__supabase__* si están disponibles "
            "(crear tablas/edge functions), o REST con la anon key para lecturas."
        ),
        cwd=state["cwd"],
        max_turns=m["budget"].get("max_turns_per_iter", 30),
        setting_sources=["user", "project"],   # descubre las SKILLS del usuario + CLAUDE.md
        skills=m.get("skills", "all"),          # el planner puede autoinvocar tus skills (override por misión)
        with_integrations=True,                 # cablea Vercel (env) + Supabase (MCP) desde el .env
    ))
    if getattr(res, "rate_limited", False):
        # Pausa resumible: no quemamos vueltas ni cerramos la misión. v1.2: si el SDK
        # dio resets_at (RateLimitEvent), lo propagamos para que el watcher espere
        # EXACTAMENTE hasta el reset en vez de reintentar a ciegas cada 15 min.
        e = RateLimitPause(res.error or "límite de uso del plan Max alcanzado")
        e.reset_at = float(getattr(res, "rate_reset_at", 0) or 0)
        raise e
    # telemetría de cuota (v1.2): si la ventana va cargada, que se vea en el dashboard
    util = float(getattr(res, "quota_utilization", 0) or 0)
    if util >= 0.7:
        try:
            control.push_log(m["id"], "quota",
                             f"ventana de uso al {util:.0%}" +
                             (f" (reset {time.strftime('%H:%M', time.localtime(res.rate_reset_at))})"
                              if getattr(res, "rate_reset_at", 0) else ""),
                             node="plan", iteration=it)
        except Exception:
            pass
    text = res.text.strip()
    # F1: error_max_turns con salida real NO es un error de progreso (se quedó sin
    # turnos a mitad de faena); no debe alimentar la racha del stuck-detector.
    _is_err = bool(getattr(res, "is_error", False))
    _subtype = str(getattr(res, "subtype", "") or "")
    err_is_real = _is_err and not stuckdetect.is_productive_error(_subtype, text)
    # stream en vivo del SDK: la salida real de esta vuelta -> dashboard
    try:
        control.push_log(m["id"], "step",
                         text[:3500] or ("(sin salida del SDK) "
                                         + (_subtype or "error") + ": "
                                         + (getattr(res, "error", "") or "sin detalle")[:300]),
                         node="plan", iteration=it)
    except Exception:
        pass
    # F2 (auditoría 2026-07-10): el MOTIVO del error, visible en remoto. Antes solo
    # llegaba '(sin salida del SDK)' y res.error moría en el _LOG.jsonl local del Mac:
    # imposible distinguir max_turns / 429 / crash desde el dashboard.
    if _is_err:
        try:
            control.push_log(m["id"], "error",
                             (_subtype or "error") + ": "
                             + (getattr(res, "error", "") or "(sin detalle)")[:400]
                             + ("" if err_is_real else
                                " [max-turns con salida útil: no cuenta como atasco]"),
                             node="plan", iteration=it)
        except Exception:
            pass
    # audit trail completo (sin truncar) -> <ws>/_LOG.jsonl
    mlog(state["cwd"], "plan", iteration=it, text=text or "(sin salida)",
         is_error=bool(getattr(res, "is_error", False)), subtype=_subtype,
         err_counts_for_stuck=err_is_real,
         error=getattr(res, "error", "")[:500], cost_usd=getattr(res, "cost_usd", 0.0),
         num_turns=getattr(res, "num_turns", 0))
    gate = None
    for line in text.splitlines():
        if line.strip().upper().startswith("GATE:"):
            gate = {"subject": line.split(":", 1)[1].strip()[:70], "body": text[:1500]}
            break
    err_note = (" [SDK ERROR]" if err_is_real else " [MAX-TURNS]") if _is_err else ""
    out: MissionState = {
        "iteration": it,
        "last_action": (text[:300] or f"(sin salida){err_note}"),
        "last_error": err_is_real,
        "stuck_note": "",  # consumida por esta vuelta
        "log": [f"[plan/act it{it}]{err_note} {text[:200]}"],
        "last_cost_usd": getattr(res, "cost_usd", 0.0),  # coste REAL del SDK; lo acumula node_bookkeep
        "last_human": "",  # consumida
    }
    if gate:
        out["pending_gate"] = gate
    if not state.get("started_at"):
        out["started_at"] = time.time()  # marca de tiempo para el tope wall_clock_hours
    return out


def node_bookkeep(state: MissionState) -> MissionState:
    """Contabilidad por vuelta (entre plan y verify). Acumula el coste REAL del SDK
    (ResultMessage.total_cost_usd, no una estimación), registra el hash para el
    detector de no-progreso, y aplica los TOPES: max_iterations, 80% del crédito y
    no-progreso. Si alguno salta, marca aborted+motivo. Separa 'llevar la cuenta' del
    planificar (plan) y del juzgar (verify); así route() queda como decisión pura."""
    b = state["mission"]["budget"]
    spend = state.get("spend_usd", 0.0) + state.get("last_cost_usd", 0.0)
    out: MissionState = {
        "spend_usd": spend,
        "last_cost_usd": 0.0,
        "log": [f"[bookkeep] it={state.get('iteration')} gasto_real=${spend:.4f}/{b['credit_usd']}"],
    }
    # SDK en VIVO: publica el estado de esta vuelta a Supabase (para el dashboard en tiempo real)
    try:
        _m = state["mission"]
        metrics.push_mission(_m["id"], _m.get("title", ""), "active", False,
                             spend, state.get("iteration", 0),
                             node="plan", last_action=state.get("last_action", ""))
    except Exception:
        pass
    if state.get("iteration", 0) >= b["max_iterations"]:
        out["aborted"] = True; out["abort_reason"] = "Máximo de iteraciones."
        return out
    started = state.get("started_at", 0)
    wall_h = b.get("wall_clock_hours", 0)
    if started and wall_h and (time.time() - started) > wall_h * 3600:
        out["aborted"] = True
        out["abort_reason"] = f"Límite de tiempo de pared ({wall_h}h) superado."
        return out
    # GASTO = SOLO TELEMETRÍA (no es stopper). Con el SDK por el plan de suscripción de
    # Claude, el coste no debe parar nada: prima que la misión se COMPLETE con calidad.
    # ANTI-ATASCO v1.1 (stuckdetect multi-patrón): 1ª detección -> REPLAN (se inyecta
    # stuck_note y se resetea la ventana); 2ª detección -> abort (el replan tampoco salió).
    entry = stuckdetect.make_entry(state.get("last_action", ""), state.get("last_error", False))
    hist = ((state.get("action_history") or []) + [entry])[-12:]
    out["action_history"] = hist
    stuck, why = stuckdetect.detect(hist, limit=b.get("no_progress_limit", 4))
    if stuck:
        strikes = int(state.get("stuck_strikes", 0)) + 1
        out["stuck_strikes"] = strikes
        try:
            control.push_log(state["mission"]["id"], "stuck",
                             f"atasco #{strikes}: {why}" + (" -> REPLAN" if strikes < 2 else " -> ABORT"),
                             node="bookkeep", iteration=state.get("iteration"))
        except Exception:
            pass
        if strikes >= 2:
            out["aborted"] = True
            out["abort_reason"] = f"Atasco persistente ({why}) — el replan automático tampoco avanzó."
        else:
            out["stuck_note"] = why
            out["action_history"] = []   # ventana fresca para juzgar el nuevo enfoque
            out["log"] = out["log"] + [f"[bookkeep] ATASCO ({why}) -> replan automático"]
        mlog(state["cwd"], "stuck", strike=strikes, reason=why,
             action="replan" if strikes < 2 else "abort")
    if out.get("aborted"):
        mlog(state["cwd"], "budget_abort", reason=out.get("abort_reason", ""),
             iteration=state.get("iteration"), spend_usd=spend)
    return out


def node_verify(state: MissionState) -> MissionState:
    m = state["mission"]
    if state.get("pending_gate") or state.get("aborted"):
        return {"log": ["[verify] saltado (gate o abort pendiente; no se gasta SDK)"]}
    all_ok, results = run_sync(verify_dod(m["definition_of_done"], state["cwd"], m["objective"]))
    dod = [{"id": r.dod_id, "passed": r.passed, "evidence": r.evidence} for r in results]
    # publica el checklist del DoD para el drill-down del dashboard
    try:
        metrics.push_mission(m["id"], m.get("title", ""), "active", False,
                             node="verify", dod=[{**d, "evidence": (d["evidence"] or "")[:200]} for d in dod])
        control.push_log(m["id"], "verify",
                         "DoD: " + "; ".join(f"{d['id']}={'✓' if d['passed'] else '✗'}" for d in dod),
                         node="verify")
    except Exception:
        pass
    mlog(state["cwd"], "verify", done=all_ok,
         results=[{"id": r.dod_id, "passed": r.passed, "evidence": r.evidence} for r in results])
    out: MissionState = {
        "verifier_results": dod,
        "done": all_ok,
        "log": [f"[verify] done={all_ok} :: " + "; ".join(f"{r.dod_id}={r.passed}" for r in results)],
    }
    # F3 (2026-07-10): regla de CONVERGENCIA. Si el nº de checks ✓ lleva
    # dod_stall_limit verificaciones sin moverse, la misión no converge -> abort
    # retryable ("Sin progreso" dispara el auto-retry con post-mortem). Señal más
    # limpia que el error_streak: mide el AVANCE REAL hacia la DoD, no la forma
    # de la salida del SDK.
    if not all_ok:
        counts = (state.get("dod_counts") or []) + [sum(1 for d in dod if d["passed"])]
        out["dod_counts"] = counts
        b = m.get("budget", {})
        stalled, why = stuckdetect.dod_stalled(counts, b.get("dod_stall_limit",
                                                             b.get("no_progress_limit", 4)))
        if stalled:
            out["aborted"] = True
            out["abort_reason"] = why
            try:
                control.push_log(m["id"], "stuck", why + " -> ABORT", node="verify",
                                 iteration=state.get("iteration"))
            except Exception:
                pass
            mlog(state["cwd"], "dod_stalled", reason=why, counts=counts[-8:])
    return out


def node_gate_notify(state: MissionState) -> MissionState:
    """Envía el email [GATE] UNA sola vez. Va en un nodo separado del wait a
    propósito: en langgraph el nodo que llama interrupt() se re-ejecuta ENTERO al
    reanudar, así que cualquier efecto secundario (mandar el correo) debe vivir en
    un nodo previo ya 'checkpointed' para no duplicar la notificación."""
    g = state["pending_gate"]
    m = state["mission"]
    to = m.get("notify_email") or os.environ.get("DISPATCHER_EMAIL", "")
    gates.send_gate(m["id"], g["subject"], g["body"], to=to or None, decision=True)
    mlog(state["cwd"], "gate_notify", subject=g["subject"], body=g["body"][:2000])
    return {"log": [f"[gate] [GATE] enviado (con botones GO/NO) -> {g['subject']}"]}


def node_gate_wait(state: MissionState) -> MissionState:
    """Congela el grafo y espera la decisión humana. interrupt() pausa SIN gastar
    crédito; al reanudar con Command(resume={...}) llega 'decision'. Este nodo se
    re-ejecuta al reanudar (por eso el envío del correo está en node_gate_notify)."""
    g = state["pending_gate"]
    m = state["mission"]
    decision = interrupt({"type": "payment_gate", "mission": m["id"], "subject": g["subject"]})
    approved = bool(decision.get("approved"))
    human = decision.get("instructions", "")
    mlog(state["cwd"], "gate_decision", subject=g["subject"], approved=approved,
         instructions=(human or "")[:500])
    if not approved:
        return {"aborted": True, "abort_reason": f"Gate rechazado: {g['subject']}",
                "log": [f"[gate] NO -> abortado"], "pending_gate": {}}
    return {"pending_gate": {}, "last_human": human or "Gate aprobado, continúa.",
            "log": [f"[gate] GO -> {g['subject']}"]}


def route(state: MissionState) -> str:
    """Decisión PURA (sin efectos secundarios). Los topes y la contabilidad viven en
    node_bookkeep; aquí solo se elige la siguiente arista."""
    if state.get("aborted"):
        return "end"
    if state.get("done"):
        return "end"
    if state.get("pending_gate"):
        return "gate"
    return "plan"


# ---------------------------------------------------------------- build
def build_graph(checkpoint_path: str):
    g = StateGraph(MissionState)
    g.add_node("plan", node_plan)
    g.add_node("bookkeep", node_bookkeep)
    g.add_node("verify", node_verify)
    g.add_node("gate_notify", node_gate_notify)
    g.add_node("gate_wait", node_gate_wait)
    g.add_edge(START, "plan")
    g.add_edge("plan", "bookkeep")
    g.add_edge("bookkeep", "verify")
    g.add_conditional_edges("verify", route, {"plan": "plan", "gate": "gate_notify", "end": END})
    g.add_edge("gate_notify", "gate_wait")
    g.add_edge("gate_wait", "plan")
    saver = SqliteSaver.from_conn_string(checkpoint_path)
    return g, saver
