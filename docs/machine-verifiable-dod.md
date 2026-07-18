# A machine-verifiable Definition of Done for autonomous agents

*Why my agents are never allowed to grade their own homework — and what 30 days of unsupervised production taught me.*

---

**TL;DR.** Autonomous agents are good at *starting* tasks and bad at *proving they finished them*. The fix that has worked for me in production is a contract: every mission ships with a Definition of Done that a machine can check, and a separate, read-only verifier — not the agent — decides whether the mission closes. If "done" can't be checked by a machine, the Definition of Done is wrong, not the check.

---

## The failure mode nobody prices in

Every agent demo follows the same arc: impressive kickoff, plausible progress, and then a confident claim — "I've completed the task" — that nobody can audit cheaply.

The problem is structural, not a prompting bug. If the same model that does the work also judges the work, you've built a system with a single point of self-deception. The agent isn't lying; it's optimizing. When "the task is done" is whatever the agent says it is, the cheapest path to *done* is lowering the bar — a mild, everyday version of reward hacking. Ask an agent to "deploy a landing page and make sure it works" and you may get a beautiful summary of a deployment that returns a 404.

In enterprise settings this is the difference between a pilot and production. Nobody signs off on "the agent felt confident."

## The contract: DoD as data, not prose

In [AgentOS](https://github.com/alvaro-zamorano/agentos) — the mission runtime I've been operating unsupervised on a Mac Mini since June — every mission is a YAML file, and the heart of it is the `definition_of_done`:

```yaml
definition_of_done:
  - id: url-live
    check: "Responds 200 at its public URL"
    verify: { type: http_status, target: "https://x.vercel.app", expected: "200" }
  - id: cta-visible
    check: "The CTA is on the page"
    verify: { type: file_contains, target: "index.html", expected: "Request a demo" }
```

Four machine check types cover a surprising share of real work: `file_exists`, `http_status`, `command_exit_zero`, `file_contains`. The rule that makes the system honest is simple:

> **Every mission requires at least one machine check. Model judgment can add a quality assessment, but it can never close a mission on its own.**

`agent_judgment` exists as a check type — an LLM scoring output against a rubric. It's useful. It's also structurally forbidden from being the deciding vote. Judgment refines; machines close.

Writing the DoD this way has a second-order effect I didn't anticipate: it forces better task specification *before* the agent runs. "Improve the landing page" is not a mission. "The landing responds 200 and contains the new CTA string" is. Most of the value of machine-verifiable DoDs is that vague missions become unwritable.

## The verifier is not the agent

The second structural decision: verification runs in a **separate context, read-only**. The verifier cannot edit the artifacts it judges, and the agent cannot edit the checks it's judged by. This is the same reason code review exists, and the same reason you don't let a trading desk mark its own book.

The execution loop is `plan → bookkeep → verify → route`. The agent plans and acts; a bookkeeper tracks cost, iterations and no-progress counters; the independent verifier runs the DoD; a router decides: close, loop with the verifier's feedback, or stop and ask a human.

Humans appear in exactly two places: **money** and **irreversible actions**. Everything else — deploying to a public URL, creating a repo, writing files — runs autonomously. A gate freezes the graph (LangGraph `interrupt()` + SQLite checkpoint) and sends a GO/NO button to Telegram. No quota burns while it waits.

## What production actually taught me

Seven missions closed autonomously and verified in the first month. The lessons were not the ones I expected:

**1. The agent rarely fails; the environment does.** Rate limits, expired sessions, macOS quirks. My favorite: the health check used `pgrep`, which on macOS excludes its own ancestor processes — the watcher is an ancestor of the verifier, so the system reported itself dead while running fine. A machine check caught a bug *in the machine checks*. That's the level where reliability is won.

**2. Budgets are part of correctness.** Caps on iterations, wall-clock hours, spend and consecutive no-progress loops aren't cost control — they're what makes "the system never hangs" a property instead of a hope.

**3. Resumability beats cleverness.** Checkpoints in SQLite mean a reboot, a rate-limit or a crash resumes mid-mission instead of restarting. Boring engineering, disproportionate payoff.

**4. `http_status: 200` is necessary, not sufficient.** A page can return 200 and render garbage. The roadmap is Playwright-based checks — real clicks, rendered assertions — because the Potemkin version of *done* gets more sophisticated as the checks do.

## The principle underneath

I call it **verification over vibes**. It generalizes past agents: evals over demos, citations over confident prose, production adoption over slideware. The question that separates systems that survive contact with reality from systems that survive contact with an audience is always the same:

**"How would a machine know this is done?"**

If there's no answer, the work isn't specified yet. If there is, you can hand it to an agent — and, more importantly, you can *stop watching*.

---

*AgentOS is open: [github.com/alvaro-zamorano/agentos](https://github.com/alvaro-zamorano/agentos) — architecture, check types, gates and the production evidence are in the README. If you're deploying agents inside a real organization and wrestling with "how do we know it worked", I'd genuinely like to compare notes.*
