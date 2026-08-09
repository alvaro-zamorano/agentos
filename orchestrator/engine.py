"""
engine.py — Capa de inferencia sobre el Claude Agent SDK.

Corre bajo el plan Max 20x (sin API key). El SDK se autentica vía las
credenciales del CLI de Claude Code guardadas localmente. NO definir
ANTHROPIC_API_KEY en el entorno del daemon: si está, el SDK la prefiere y
factura pago-por-token en vez del crédito del plan.

API verificada (jun 2026): claude_agent_sdk.query / ClaudeSDKClient,
ClaudeAgentOptions. Paquete: claude-agent-sdk (el viejo claude-code-sdk está muerto).
"""
from __future__ import annotations
import os
import asyncio
from dataclasses import dataclass, field, fields
from typing import Optional

# Cinturón de seguridad: forzar uso del plan, nunca API key.
# Si el entorno trae una API key heredada, la quitamos para este proceso.
os.environ.pop("ANTHROPIC_API_KEY", None)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from claude_agent_sdk import (  # type: ignore
    query, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage,
)


@dataclass
class EngineResult:
    text: str
    raw_messages: list = field(default_factory=list)
    cost_usd: float = 0.0      # coste REAL de la vuelta (ResultMessage.total_cost_usd)
    is_error: bool = False     # el SDK devolvió error o lanzó excepción
    subtype: str = ""          # subtipo del ResultMessage (p.ej. error_max_turns) — F1 auditoría 2026-07-10
    num_turns: int = 0
    error: str = ""
    rate_limited: bool = False  # se topó el límite de uso del plan Max -> pausar y retomar
    rate_reset_at: float = 0.0  # epoch de reset del límite (RateLimitEvent.resets_at), 0 si n/a
    quota_utilization: float = 0.0  # 0-1 de la ventana de uso (RateLimitEvent), 0 si n/a
    structured_output: object = None  # dict validado si se pidió output_format json_schema


_RL_KEYS = ("rate limit", "rate_limit", "429", "usage limit", "usage_limit",
            "quota", "overloaded", "too many requests", "limit reached")

# Errores TRANSITORIOS (red/infra): se reintentan DENTRO de la misma vuelta con backoff,
# sin quemar iteración del grafo. Antes un blip de red contaba como "[SDK ERROR]" y
# empujaba la misión hacia el aborto (caso aval-landing: 15 vueltas de SDK ERROR).
_TRANSIENT_KEYS = ("connection", "econnreset", "econnrefused", "epipe", "socket",
                   "network", "temporarily", "500", "502", "503", "504", "529",
                   "internal server error", "bad gateway", "service unavailable",
                   "cliconnection", "broken pipe", "reset by peer")


def _is_rate_limit(*parts) -> bool:
    s = " ".join(str(p) for p in parts if p is not None).lower()
    return any(k in s for k in _RL_KEYS)


def _is_transient(*parts) -> bool:
    s = " ".join(str(p) for p in parts if p is not None).lower()
    return any(k in s for k in _TRANSIENT_KEYS)


# Campos que soporta TU versión instalada del SDK: pasamos solo esos -> compatible
# hacia delante y hacia atrás (skills/setting_sources/can_use_tool existen en >=0.2.x).
_OPT_FIELDS = {f.name for f in fields(ClaudeAgentOptions)}


def _integrations_from_env():
    """Conectividad del agente desde el .env, igual que en Cowork.
    - Supabase: MCP oficial (mcp__supabase__*) si hay SUPABASE_PROJECT_REF + SUPABASE_ACCESS_TOKEN.
    - Vercel: NO necesita MCP — el CLI usa VERCEL_TOKEN, que el agente hereda del entorno del daemon.
    Devuelve (mcp_servers, tools_extra)."""
    servers, tools = {}, []
    ref = os.environ.get("SUPABASE_PROJECT_REF", "")
    tok = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if ref and tok:
        servers["supabase"] = {
            "command": "npx",
            "args": ["-y", "@supabase/mcp-server-supabase@latest", f"--project-ref={ref}"],
            "env": {"SUPABASE_ACCESS_TOKEN": tok},
        }
        tools.append("mcp__supabase__*")
    return servers, tools


async def run_agent(
    prompt: str,
    *,
    system_prompt: str = "",
    cwd: Optional[str] = None,
    allowed_tools: Optional[list[str]] = None,
    max_turns: int = 25,
    permission_mode: str = "acceptEdits",
    model: Optional[str] = None,
    setting_sources: Optional[list] = None,   # ["user","project"] -> descubre skills + CLAUDE.md
    skills=None,                               # "all" | ["gsd-pro", ...] | None
    can_use_tool=None,                         # callback de permisos -> GATES nativos del SDK
    mcp_servers=None,                          # dict de MCP servers para el SDK
    with_integrations: bool = False,           # cablea Supabase MCP + Vercel desde el .env
    output_format=None,                        # {"type":"json_schema","schema":...} -> structured output
) -> EngineResult:
    """
    Lanza un sub-loop de agente (planificación + tools + ejecución) y devuelve
    el texto agregado. El SDK gestiona internamente el bucle de tool-use,
    acceso a ficheros, bash, web y compactación de contexto.
    """
    # Defensa: el SDK lanza un subproceso con cwd=workspace y PETA si no existe
    # (p.ej. si una vuelta anterior movió/borró el directorio). Garantizar que existe.
    if cwd:
        os.makedirs(cwd, exist_ok=True)
    base_tools = allowed_tools or ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebSearch"]
    if with_integrations:
        servers, extra_tools = _integrations_from_env()
        base_tools = base_tools + [t for t in extra_tools if t not in base_tools]
        if servers and mcp_servers is None:
            mcp_servers = servers
    _raw = {
        "system_prompt": system_prompt or "Eres un agente autónomo ejecutor. Actúa, no narres.",
        "max_turns": max_turns,
        "permission_mode": permission_mode,
        "cwd": cwd,
        "allowed_tools": base_tools,
        "model": model,
        "setting_sources": setting_sources,
        "skills": skills,
        "can_use_tool": can_use_tool,
        "mcp_servers": mcp_servers,
        "output_format": output_format,
    }
    # solo claves soportadas por el SDK instalado y con valor (None -> default del SDK)
    opts = ClaudeAgentOptions(**{k: v for k, v in _raw.items() if k in _OPT_FIELDS and v is not None})

    # ANTI-CUELGUE: una llamada al SDK NO puede bloquear el daemon para siempre
    # (p.ej. si el agente lanza un servidor/dev/comando interactivo que no termina).
    timeout_s = int(os.environ.get("SDK_CALL_TIMEOUT_SECONDS", "900"))  # 15 min por vuelta
    max_retries = int(os.environ.get("SDK_TRANSIENT_RETRIES", "2"))
    backoffs = (20, 45, 90)

    attempt = 0
    while True:
        chunks: list[str] = []
        raw: list = []
        cost_usd = 0.0
        is_error = False
        subtype = ""
        num_turns = 0
        err = ""
        api_status = None
        rl_reset_at = 0.0
        rl_util = 0.0
        rl_rejected = False
        structured = None

        async def _consume():
            nonlocal cost_usd, is_error, subtype, num_turns, err, api_status
            nonlocal rl_reset_at, rl_util, rl_rejected, structured
            async for message in query(prompt=prompt, options=opts):
                raw.append(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            chunks.append(block.text)
                elif isinstance(message, ResultMessage):
                    cost_usd = message.total_cost_usd or 0.0
                    is_error = bool(message.is_error)
                    subtype = str(getattr(message, "subtype", "") or "")
                    num_turns = message.num_turns or 0
                    api_status = getattr(message, "api_error_status", None)
                    structured = getattr(message, "structured_output", None)
                    if message.errors:
                        err = "; ".join(str(e) for e in message.errors)
                    if not err and message.result and message.is_error:
                        err = str(message.result)
                elif type(message).__name__ == "RateLimitEvent":
                    # SEÑAL ESTRUCTURADA de cuota del plan Max (v1.2): mejor que adivinar
                    # por strings. Duck-typing defensivo por si el SDK instalado no la trae.
                    info = getattr(message, "rate_limit_info", None) or getattr(message, "info", None) or message
                    try:
                        rl_util = float(getattr(info, "utilization", 0) or 0)
                        rl_reset_at = float(getattr(info, "resets_at", 0) or 0)
                        if str(getattr(info, "status", "")).lower() == "rejected":
                            rl_rejected = True
                    except Exception:
                        pass

        timed_out = False
        try:
            await asyncio.wait_for(_consume(), timeout=timeout_s)
        except asyncio.TimeoutError:
            is_error = True
            timed_out = True
            err = f"SDK timeout > {timeout_s}s (posible comando colgado: servidor/dev/interactivo)"
        except Exception as e:
            # Resiliencia: un fallo del SDK NO debe reventar el runner. Se registra como
            # paso erróneo; el detector de no-progreso lo cierra bien y avisa por email.
            is_error = True
            err = f"{type(e).__name__}: {e}"

        rate_limited = rl_rejected or (api_status == 429) or _is_rate_limit(err, api_status)

        # F6 (2026-07-10): persistir la última foto de cuota -> el watcher decide si
        # ARRANCAR misiones nuevas con la ventana cargada (defer, no mid-mission).
        if rl_util > 0:
            try:
                import json as _json, time as _time
                os.makedirs(os.path.join(_ROOT, "state"), exist_ok=True)
                with open(os.path.join(_ROOT, "state", "quota.json"), "w", encoding="utf-8") as _f:
                    _json.dump({"utilization": rl_util, "reset_at": rl_reset_at,
                                "ts": _time.time()}, _f)
            except Exception:
                pass

        # RETRY DE TRANSITORIOS (clasificación: rate-limit -> pausa fuera; timeout -> NO
        # reintentar, probable cuelgue real; transitorio de red/infra SIN texto producido
        # (=> sin efectos secundarios que duplicar) -> backoff + reintento aquí dentro).
        if (is_error and not rate_limited and not timed_out and not chunks
                and attempt < max_retries and _is_transient(err, api_status)):
            import random
            wait = backoffs[min(attempt, len(backoffs) - 1)] + random.uniform(0, 10)
            print(f"[engine] error transitorio del SDK (intento {attempt+1}/{max_retries+1}): "
                  f"{err[:160]} -> reintento en {wait:.0f}s")
            await asyncio.sleep(wait)
            attempt += 1
            continue

        return EngineResult(
            text="\n".join(chunks), raw_messages=raw,
            cost_usd=cost_usd, is_error=is_error, subtype=subtype,
            num_turns=num_turns, error=err,
            rate_limited=rate_limited, rate_reset_at=rl_reset_at,
            quota_utilization=rl_util, structured_output=structured,
        )
