# AgentOS

Sistema de agentes autónomos en el Mac Mini. Una idea trabajada en un chat se convierte en
algo **terminado y corriendo** (no solo planificado), parándose solo en pagos / acciones
irreversibles. Motor: Claude Agent SDK bajo el plan Max. Orquestación: LangGraph + checkpoint
SQLite. Control humano: Telegram.

**Filosofía:** lo importante no es lanzar agentes, es **pararlos bien** — la DoD verificable y
el verificador independiente son el corazón.

**Estado:** v1.0 — end-to-end real confirmado en el Mac (`bash confirm.sh` → ✅). Operativo.

## Arranque rápido

```bash
cd ~/Desktop/os/agent-os
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
claude                      # login del plan Max (una vez); si falta: npm i -g @anthropic-ai/claude-code
bash confirm.sh             # confirma el e2e real (misión mínima, barata, sin gates)
bash bridge_check.sh        # dice qué falta para el bridge (git auth, daemon, Telegram)
bash install_daemon.sh      # enciende el daemon (vigila inbox + Telegram + git pull)
```

## Cómo se lanza una misión (3 bridges → una inbox)

- **claude.ai + git:** en un chat dices "continúalo solo" → claude.ai commitea el `mission.yaml`
  a `Wcoach24/alvaro-pipeline/missions/inbox/` → el Mac hace `git pull` y lo ejecuta.
  (Requiere pegar el snippet en las preferencias de claude.ai — ver `docs/CLAUDEAI_BRIDGE.md`.)
- **Cowork:** trabajando aquí, "continúalo solo" → se escribe directo en la inbox.
- **Telegram `/idea <texto>`:** el Mac destila la idea en una misión y la encola.

Los gates (GO/NO) y los avisos (done/abortada/pausa) llegan por **Telegram**.

## Documentación

- `docs/ARCHITECTURE.md` — referencia completa: las 5 capas, el grafo, los componentes,
  el ciclo de vida de una misión, auth/coste, y los **invariantes que no romper**.
- `docs/ROADMAP.md` — backlog priorizado y el bucle para **sacar mejores versiones**.
- `docs/BRIDGE.md` — el bridge local (Cowork) y el formato del `mission.yaml`.
- `docs/CLAUDEAI_BRIDGE.md` — el bridge claude.ai + git, con el **snippet de preferencias**.
- `CHANGES.md` — log cronológico de todo lo construido y por qué (runs 1–7).
- `schemas/mission.schema.json` — contrato de la misión.

## Operativa

```bash
python dashboard.py           # estado: inbox / active / done
tail -f state/watcher.out.log # logs del daemon (errores: watcher.err.log)
bash run.sh                   # correr la misión de prueba (geo-dossier) a mano
launchctl unload ~/Library/LaunchAgents/com.alvaro.agentos.watcher.plist   # parar el daemon
```

## Mejorar el sistema

Cada X tiempo: abre `docs/ROADMAP.md`, elige 1–2 mejoras por impacto/esfuerzo, impleméntalas
sin romper los invariantes (`ARCHITECTURE.md §9`), deja `python smoke_test.py` en TODO VERDE
+ `bash confirm.sh` en ✅, anótalo en `CHANGES.md` y sube la versión.

⚠️ Nunca definas `ANTHROPIC_API_KEY` (fuerza el plan Max). El sistema la borra del proceso.
