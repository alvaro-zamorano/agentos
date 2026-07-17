# AgentOS

> **Autonomous agent infrastructure with a machine-verifiable Definition of Done — running 24/7 in production.**

---

## The 60-second pitch

**The problem:** most agents are good at *starting* tasks. Finishing them properly — with objective evidence that something is actually done — is the hard problem.

**The solution:** AgentOS takes a mission as YAML with a machine-checkable *Definition of Done*, runs it through an autonomous `plan → bookkeep → verify → route` loop, and **only closes when an independent verifier** confirms objective checks: `http_status`, `file_exists`, `command_exit_zero`, `file_contains`. The agent is never its own judge.

**In production right now** — Mac Mini, 24/7, unsupervised:

```
$ cat state/watcher_heartbeat.txt
1782051742  2026-06-21T16:22:22  pid=97368     # < 120s = system healthy

$ ls missions/done/
2026-06-16-geo-es-dossier/
2026-06-17-catering-connect-foundation/
2026-06-17-confirm-e2e/
2026-06-17-test-hello-vercel/
2026-06-18-agentos-dashboard/
2026-06-18-spcx-short-watcher/
2026-06-20-aval-framework-spine/
# → 7 missions closed autonomously, all verified

$ tail -3 state/watcher.out.log
[runner] MISSION COMPLETED: 2026-06-18-agentos-dashboard
[runner] MISSION COMPLETED: 2026-06-17-test-hello-vercel
[runner] MISSION COMPLETED: 2026-06-16-geo-es-dossier
```

**For a recruiter:** LangGraph + Claude Agent SDK + launchd daemon, 5 decoupled layers, end-to-end in production.
**For a VP of Engineering:** independent verifier (anti reward-hacking), GO/NO human gates over Telegram, crash-resumable via SQLite checkpoints.

---

## What it is

AgentOS receives a **mission** (a YAML file with an objective plus a checkable *Definition of Done*) and drives it to completion on its own. Every mission runs through a loop:

```
plan  →  bookkeep  →  verify  →  route
```

- **plan** — the agent takes the next real step toward the objective (writes files, deploys, creates repos…).
- **bookkeep** — tracks cost, iterations and no-progress counters, and applies anti-stall limits.
- **verify** — an **independent verifier** checks the *Definition of Done* with **machine checks** (it does not trust the agent).
- **route** — done? close. Human gate needed? ask GO/NO over Telegram. Neither? another loop, with the verifier's feedback fed back in.

## Why it matters

- **"Done" is not fakeable.** Every mission requires at least one **machine** check (`file_exists`, `http_status`, `command_exit_zero`, `file_contains`). LLM judgment (`agent_judgment`) can *add* quality assessment, but **never closes a mission on its own**.
- **Independent verifier.** Runs in a separate context, read-only: it cannot touch the artifacts it judges (anti reward-hacking). See [`orchestrator/verifier.py`](orchestrator/verifier.py).
- **Autonomous by default, human where it counts.** It only stops to ask **GO/NO** when facing **money** or something **irreversible**. Deploying to a public URL or creating a GitHub repo = autonomous.
- **It doesn't get stuck.** Caps on iterations, wall-clock time, no-progress loops and per-SDK-call timeouts guarantee no mission blocks the system.
- **Resumable.** All state lives in SQLite checkpoints; if the machine reboots, it picks up where it left off.

---

## Architecture

Five decoupled layers:

```
┌─────────────────────────────────────────────────────────────┐
│  BRIDGES (how a mission gets in)                            │
│  GitHub API  /  Cowork (local)  /  Telegram /idea           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓  missions/inbox/<id>.yaml
┌─────────────────────────────────────────────────────────────┐
│  WATCHER  (bin/watcher.py, launchd daemon)                  │
│  Serial priority queue · resumes paused runs · heartbeat    │
└───────────────────────────┬─────────────────────────────────┘
                            ↓  missions/active/<id>/
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR  (orchestrator/graph.py, LangGraph)           │
│  plan → bookkeep → verify → route                           │
│  SQLite checkpoints (resumable after crash/rate-limit)      │
└──────────┬────────────────┬────────────────────────────────-┘
           ↓                ↓
┌──────────────┐   ┌──────────────────────────────────────────┐
│  ENGINE      │   │  VERIFIER  (orchestrator/verifier.py)    │
│  Claude SDK  │   │  Machine checks (mandatory)              │
│  Max plan,   │   │  + agent_judgment (optional, read-only)  │
│  no API key  │   │  No green here → the graph won't close   │
└──────────────┘   └──────────────┬───────────────────────────┘
                                  ↓  if gated
                   ┌──────────────────────────────────────────┐
                   │  GATES  (orchestrator/gates.py)          │
                   │  Telegram GO/NO buttons · email fallback │
                   │  interrupt() freezes the graph, no spend │
                   └──────────────────────────────────────────┘
```

| Layer | Key file | Role |
|---|---|---|
| **Watcher** | [`bin/watcher.py`](bin/watcher.py) | launchd daemon. Watches the queue, launches the runner, resumes paused missions, handles Telegram `/idea`. |
| **Orchestrator** | [`orchestrator/graph.py`](orchestrator/graph.py) | LangGraph graph: `plan → bookkeep → verify → route`. SQLite checkpoints. |
| **Engine** | [`orchestrator/engine.py`](orchestrator/engine.py) | Wraps the Claude Agent SDK. Max plan (no API key). Captures real cost. |
| **Verifier** | [`orchestrator/verifier.py`](orchestrator/verifier.py) | Checks the DoD; combines machine checks (mandatory) with model judgment (optional, read-only). |
| **Gates** | [`orchestrator/gates.py`](orchestrator/gates.py) | GO/NO over Telegram (buttons) or email. `interrupt()` freezes the graph without burning quota. |

### Mission lifecycle

```
missions/inbox/<id>.yaml      ← watcher detects it
   → missions/active/<id>/   ← runner creates workspace, starts the graph
      · gate       → interrupt → Telegram GO/NO → resume
      · rate-limit → _PAUSED.json + exit 75 → watcher resumes later
   → missions/done/<id>/     ← finalize: workspace + _RESULT.json
   → missions/_processed/    ← yaml archived; Telegram notification
```

The agent works ONLY inside its workspace (`missions/active/<id>/`). The deliverable is named as the DoD requires; the system moves it to `done/` on close.

### The 3 bridges

| Source | How it enters | Use case |
|--------|---------------|----------|
| **GitHub API** | commit into `inbox/` → watcher pulls via API | missions from claude.ai without Mac access |
| **Cowork (local)** | `bin/new_mission.py` writes straight to inbox | working an idea with full Mac access |
| **Telegram `/idea`** | `bin/dispatcher.py` distills idea→YAML→inbox | fast, from the phone |

---

## Running it

### 1. Requirements

- Python 3.10+
- `claude` CLI (Claude Code) with an active Max session (login once)
- Telegram bot token (for gates and notifications)
- Authenticated `gh` CLI (for the GitHub bridge)

### 2. Install

```bash
git clone https://github.com/alvaro-zamorano/agentos.git
cd agentos

# Virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Credentials
cp .env.example .env
# Edit .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITHUB_REPO, ...

# Max plan login (once; the SDK won't run without it)
claude
```

### 3. Sanity checks

```bash
python smoke_test.py        # plumbing: ALL GREEN without spending credit
bash bridge_check.sh        # what's missing for the bridge (git auth, daemon, Telegram)
```

### 4. Start the daemon (watcher)

```bash
bash install_daemon.sh          # installs and starts the launchd daemon
tail -f state/watcher.out.log   # live logs
```

### 5. Submit a mission

```bash
# Option A: local YAML file
python bin/new_mission.py missions/examples/hello-world.yaml

# Option B: from Telegram
/idea "Publish a landing page with my CV summary on vercel.app"

# Option C: from claude.ai (git bridge)
# Draft the mission in a claude.ai chat → "continue on your own" → the Mac picks it up
```

### 6. Monitor

```bash
python dashboard.py                      # status: inbox / active / done
tail -f state/watcher.out.log            # daemon logs
cat state/watcher_heartbeat.txt          # liveness check (< 120s = healthy)
```

---

## Mission format

```yaml
id: 2026-06-17-landing-esgeo        # unique dated slug
title: "esGEO landing v2"
objective: "One sentence: what must be true when this is done."
context: "Distilled context from the thread."
done_level: staging                  # staging | production

definition_of_done:                  # >= 1 MACHINE check is mandatory
  - id: url-live
    check: "Responds 200 at its public URL"
    verify: { type: http_status, target: "https://x.vercel.app", expected: "200" }
  - id: cta-visible
    check: "The CTA is on the page"
    verify: { type: file_contains, target: "index.html", expected: "Request a demo" }

budget: { max_iterations: 20, credit_usd: 5.0, no_progress_limit: 4, wall_clock_hours: 6 }
gates: { payment: true, irreversible: true }
```

**Verify types:** `file_exists`, `http_status`, `command_exit_zero`, `file_contains` (machine checks — mandatory), and `agent_judgment` (model judgment — optional, never closes on its own).

---

## Production evidence

Snapshot taken 2026-06-21 from the system running on the Mac Mini:

```
# Watcher alive (pid 97368 active, heartbeat < 120s)
$ cat state/watcher_heartbeat.txt
1782051742  2026-06-21T16:22:22  pid=97368

# 7 missions closed autonomously
$ ls missions/done/
2026-06-16-geo-es-dossier/
2026-06-17-catering-connect-foundation/
2026-06-17-confirm-e2e/
2026-06-17-test-hello-vercel/
2026-06-18-agentos-dashboard/
2026-06-18-spcx-short-watcher/
2026-06-20-aval-framework-spine/

# Last lines of the daemon log
$ tail -3 state/watcher.out.log
[runner] MISSION COMPLETED: 2026-06-18-agentos-dashboard
[runner] MISSION COMPLETED: 2026-06-17-test-hello-vercel
[runner] MISSION COMPLETED: 2026-06-16-geo-es-dossier
```

Key files implementing everything above:

| File | What it does |
|------|--------------|
| [`bin/watcher.py`](bin/watcher.py) | Queue, heartbeat, launchd |
| [`orchestrator/graph.py`](orchestrator/graph.py) | Full LangGraph graph |
| [`orchestrator/verifier.py`](orchestrator/verifier.py) | All check types |
| [`orchestrator/engine.py`](orchestrator/engine.py) | Claude SDK wrapper |
| [`orchestrator/gates.py`](orchestrator/gates.py) | GO/NO over Telegram |

---

## Design decisions

- **Why serial?** One mission at a time protects the shared Max quota; interactive Claude stays responsive while the daemon works in the background.
- **Why no API key?** The SDK uses the Max plan's OAuth token. Zero marginal cost for normal missions; the daemon auto-pauses when it hits the usage limit.
- **Why an independent verifier?** To prevent reward hacking: if the agent could modify the tests, "passing" the DoD would be trivial and meaningless. The verifier is read-only.
- **Why LangGraph + SQLite?** Resumability without infrastructure. Checkpoints survive reboots, power cuts and rate-limits without losing progress.
- **Why `ps` and not `pgrep` for the health check?** On macOS, `pgrep` excludes its own ancestor processes. The watcher is an ancestor of the verifier, so `pgrep` returns a false negative. `ps aux | grep watcher` detects the process correctly.

---

## Current status

- ✅ Real end-to-end confirmed on Mac Mini (24/7)
- ✅ Watcher with reliable heartbeat under launchd (KeepAlive)
- ✅ Independent verifier + machine-checked DoD
- ✅ Telegram gates with GO/NO buttons
- ✅ Idempotency: every mission runs exactly once
- ✅ Clean re-runs (checkpoint cleared on fresh re-run)
- ✅ 7 missions closed autonomously and verified

## Roadmap

- Native gating via SDK hook (PreToolUse) for money/irreversible actions
- Metrics in SQLite (Autonomy Index, DoD pass rate)
- Anti-Potemkin verification (Playwright: real clicks, not just HTTP 200)
- No-progress hash that includes the verifier's verdict (hardened anti reward-hacking)
- Controlled parallelism: N simultaneous missions on shared quota

---

## License

MIT. Built and operated by [Álvaro Zamorano](https://github.com/alvaro-zamorano) as personal agent infrastructure.
