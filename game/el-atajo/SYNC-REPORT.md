# SYNC-REPORT — El Atajo · Misiones m0–m5 + Distro Batch

**Generado:** 2026-08-09  
**Propósito:** Auditoría de entregables producidos por cada misión del estudio "El Atajo Capítulo 1", antes de consolidar en `alvaro-zamorano/alvaro-pipeline`.

---

## Resumen ejecutivo

| Misión | ID misión | Estado | Entregables encontrados | Entregables ausentes |
|--------|-----------|--------|------------------------|----------------------|
| m0 · Dirección Creativa | 2026-08-09-atajo-m0-direccion | ✅ COMPLETA | 3/3 | 0 |
| m1 · Guion + Escaleta | 2026-08-09-atajo-m1-guion | ✅ COMPLETA | 5/5 | 0 |
| m2 · Diseño de Puzzles | 2026-08-09-atajo-m2-diseno-puzzles | ✅ COMPLETA | 6/6 | 0 |
| m3 · Arte + Biblia Visual | 2026-08-09-atajo-m3-arte | ✅ COMPLETA | 9/9 | 0 |
| m4 · Tech + Jugabilidad | 2026-08-09-atajo-m4-tech-jugabilidad | ✅ COMPLETA | 13/13 | 0 |
| m5 · QA + Solver | 2026-08-09-atajo-m5-qa-solver | ✅ COMPLETA | 16/16 | 0 |
| distro · Batch distribución | 2026-08-09-atajo-distro-batch | ✅ COMPLETA | 7/7 | 0 |

**Total archivos consolidados en `game/el-atajo/`:** 44  
**Total drafts distro en `distro/el-atajo/drafts/`:** 7  
**Archivos >50 MB excluidos:** ninguno (máx. encontrado: 96 KB)

---

## Detalle por misión

### m0 · Dirección Creativa
**Workspace fuente:** `missions/done/2026-08-09-atajo-m0-direccion/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| Greenlight creativo | `game/el-atajo/docs/00-direccion/GREENLIGHT.md` | ✅ presente |
| Handoff dirección | `game/el-atajo/docs/00-direccion/HANDOFF.md` | ✅ presente |
| Protocolo STUDIO | `game/el-atajo/docs/STUDIO.md` | ✅ presente |

**Ausentes reportados pero no encontrados:** ninguno

---

### m1 · Guion + Escaleta
**Workspace fuente:** `missions/done/2026-08-09-atajo-m1-guion/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| Escaleta Acto I | `game/el-atajo/docs/10-guion/ESCALETA.md` | ✅ presente |
| Personajes (biblia) | `game/el-atajo/docs/10-guion/PERSONAJES.md` | ✅ presente |
| Handoff guion | `game/el-atajo/docs/10-guion/HANDOFF.md` | ✅ presente (de m3) |
| Script ES (JSON) | `game/el-atajo/data/script-es.json` | ✅ presente (de m5) |
| Change requests | `game/el-atajo/docs/CHANGE-REQUESTS.md` | ✅ presente (de m5) |

**Ausentes reportados pero no encontrados:** ninguno

---

### m2 · Diseño de Puzzles
**Workspace fuente:** `missions/done/2026-08-09-atajo-m2-diseno-puzzles/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| Diseño de puzzles | `game/el-atajo/docs/20-diseno/PUZZLES.md` | ✅ presente |
| Handoff diseño | `game/el-atajo/docs/20-diseno/HANDOFF.md` | ✅ presente (de m5) |
| Grafo navegación (JSON) | `game/el-atajo/data/graph.json` | ✅ presente (de m5) |
| Validador de grafo | `game/el-atajo/tools/validate-graph.py` | ✅ presente |
| Script ES (JSON) | `game/el-atajo/data/script-es.json` | ✅ presente (de m5) |
| Change requests | `game/el-atajo/docs/CHANGE-REQUESTS.md` | ✅ presente (de m5) |

**Ausentes reportados pero no encontrados:** ninguno

---

### m3 · Arte + Biblia Visual
**Workspace fuente:** `missions/done/2026-08-09-atajo-m3-arte/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| Biblia visual | `game/el-atajo/docs/30-arte/BIBLIA-VISUAL.md` | ✅ presente |
| Handoff arte | `game/el-atajo/docs/30-arte/HANDOFF.md` | ✅ presente (de m5) |
| Preview escena1 | `game/el-atajo/docs/30-arte/previews/escena1-canada-cerrada.png` | ✅ presente (16 KB) |
| Preview escena2 | `game/el-atajo/docs/30-arte/previews/escena2-venta-tiavelas.png` | ✅ presente (12 KB) |
| Preview escena3 | `game/el-atajo/docs/30-arte/previews/escena3-bancales-colmena.png` | ✅ presente (20 KB) |
| Preview escena4 | `game/el-atajo/docs/30-arte/previews/escena4-sala-telar.png` | ✅ presente (24 KB) |
| Preview escena5 | `game/el-atajo/docs/30-arte/previews/escena5-sotano-registro.png` | ✅ presente (20 KB) |
| Preview completo | `game/el-atajo/docs/30-arte/previews/preview-completo.png` | ✅ presente (96 KB) |
| Render preview tool | `game/el-atajo/tools/render-preview.html` | ✅ presente |

**Ausentes reportados pero no encontrados:** ninguno  
⚠️ **Nota:** No hay archivos SVG ni assets de sprites en formato imagen (solo JS). Art assets son representaciones Canvas/JS, no ficheros PNG de sprites.

---

### m4 · Tech + Jugabilidad
**Workspace fuente:** `missions/done/2026-08-09-atajo-m4-tech-jugabilidad/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| index.html (juego) | `game/el-atajo/index.html` | ✅ presente |
| Engine JS | `game/el-atajo/src/engine.js` | ✅ presente |
| Flow tests | `game/el-atajo/tests/flow.py` | ✅ presente |
| Art: palette | `game/el-atajo/art/palette.js` | ✅ presente |
| Art: sprites | `game/el-atajo/art/sprites.js` | ✅ presente |
| Art: 5 escenas JS | `game/el-atajo/art/scenes/escena{1..5}.js` | ✅ presentes (5/5) |
| Handoff tech | `game/el-atajo/docs/40-tech/HANDOFF.md` | ✅ presente |
| Screenshots: 7 shots | `game/el-atajo/docs/40-tech/shots/` | ✅ presentes (7/7) |

**Ausentes reportados pero no encontrados:** ninguno

---

### m5 · QA + Solver
**Workspace fuente:** `missions/done/2026-08-09-atajo-m5-qa-solver/el-atajo/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| index.html (final) | `game/el-atajo/index.html` | ✅ presente |
| Engine JS (patched) | `game/el-atajo/src/engine.js` | ✅ presente |
| QA Informe | `game/el-atajo/docs/50-qa/INFORME.md` | ✅ presente |
| QA Handoff | `game/el-atajo/docs/50-qa/HANDOFF.md` | ✅ presente |
| QA results JSON | `game/el-atajo/docs/50-qa/data/results.json` | ✅ presente |
| Solver script | `game/el-atajo/tests/solver.py` | ✅ presente |
| Report script | `game/el-atajo/tests/report.py` | ✅ presente |
| Flow tests | `game/el-atajo/tests/flow.py` | ✅ presente |
| Change requests | `game/el-atajo/docs/CHANGE-REQUESTS.md` | ✅ presente |

**Ausentes reportados pero no encontrados:** ninguno  
**Resultado QA:** ✅ PASS — 3/3 rutas, 40 combos adversariales, 0 errores de consola

---

### distro · Batch distribución
**Workspace fuente:** `missions/done/2026-08-09-atajo-distro-batch/distro/el-atajo/drafts/`

| Entregable | Ruta en repo | Estado |
|-----------|-------------|--------|
| MANIFEST.md | `distro/el-atajo/drafts/MANIFEST.md` | ✅ presente |
| pieza-00-anuncio-el-atajo.md | `distro/el-atajo/drafts/pieza-00-anuncio-el-atajo.md` | ✅ presente |
| pieza-01-reloj-de-arena.md | `distro/el-atajo/drafts/pieza-01-reloj-de-arena.md` | ✅ presente |
| pieza-02-grafo-acto-i.md | `distro/el-atajo/drafts/pieza-02-grafo-acto-i.md` | ✅ presente |
| pieza-03-monkey-wrench.md | `distro/el-atajo/drafts/pieza-03-monkey-wrench.md` | ✅ presente |
| pieza-04-anacronismos.md | `distro/el-atajo/drafts/pieza-04-anacronismos.md` | ✅ presente |
| pieza-05-humor-de-fracaso.md | `distro/el-atajo/drafts/pieza-05-humor-de-fracaso.md` | ✅ presente |

**Ausentes reportados pero no encontrados:** ninguno

---

## Archivos excluidos por tamaño

Ninguno. Todos los archivos están por debajo del límite de 50 MB. El fichero más grande es `docs/30-arte/previews/preview-completo.png` (96 KB).

---

## Notas de consolidación

1. **Misión base:** Se usó `m5-qa-solver` como árbol base por ser el más completo (incluye todo lo de m4 + QA). Las misiones anteriores aportaron ficheros únicos que m5 no tenía.
2. **Versiones preferidas:** Para archivos que existían en múltiples versiones (engine.js, index.html, graph.json, script-es.json), se tomó la versión de `m5` por ser la más actualizada y haber pasado QA.
3. **docs/10-guion/HANDOFF.md:** La versión final procede de `m3-arte` (handoff recibido por arte, que incluye el resumen del guion definitivo).
4. **distro-batch-attempt1:** Existe un intento previo (`2026-08-09-atajo-distro-batch-attempt1`) con los mismos drafts. Se usó la versión final del batch exitoso.
