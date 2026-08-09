# HANDOFF — Motor v2 (m4-tech-jugabilidad)

## Estado: COMPLETADO ✓

## Arquitectura

```
el-atajo/
├── index.html          → Estructura DOM + carga de datos (fetch JSON) + integración art/
├── src/
│   └── engine.js       → Motor principal (927 líneas, IIFE)
├── art/
│   ├── palette.js      → window.Palette
│   ├── sprites.js      → window.Sprites
│   └── scenes/         → window.Art.escena{1-5}
├── data/
│   ├── script-es.json  → Todos los textos del juego (fuente única)
│   └── graph.json      → Grafo de puzzles y flags
├── docs/
│   ├── 20-diseno/HANDOFF.md
│   ├── 30-arte/HANDOFF.md
│   └── 40-tech/
│       ├── HANDOFF.md  (este fichero)
│       └── shots/      → Pantallazos 390×844 de cada escena
└── tests/
    └── flow.py         → Test Playwright completo del capítulo
```

## Motor: subsistemas

### 1. Renderer (canvas 180×320)
- Canvas nativo `<canvas id="c">` de 180×320 px internos.
- `fitCanvas()` escala CSS al viewport (pixelated, sin blur).
- Subsistema: `render(t)` → dibuja fondo (art module) + personajes + player + HUD.
- Target: 60 fps con `requestAnimationFrame`.

### 2. Input
- `handleCanvasTap(clientX, clientY)` → convierte coords a canvas space (0..180, 0..320).
- Zonas táctiles mínimas: 44×44 px en DOM (toolbar buttons), hotspots en canvas ≥28 px en dimensión menor.
- Modes: `walk` | `look` | `use`. Item seleccionado activa modo USE automáticamente.

### 3. Cutscene interpreter
- Lee beats de `SCRIPT.cutscenes[id].beats[]` → `{speaker, line}`.
- Avanza con tap en canvas o `__advance()`.
- Encadenamiento declarado en `onCutsceneEnd(id)`.

### 4. Dialog system
- `SCRIPT.dialogs[id]` → árbol de nodos con `{speaker, line, options[]}`.
- Flags activados en `DIALOG_FLAGS` map (sin texto de guion en motor).
- Nodo terminal → `closeDialog()` → vuelve a mode scene.

### 5. Estado + inventario
- Estado global en `G` (flags, inventory, mode, scene, player).
- No usa localStorage (por especificación).
- Export/import via `window.__STATE` (referencia directa al objeto G).

### 6. Escenas declarativas
- Cada escena: `{artFn, scriptKey, walkbox, hotspots[], characters[], exits[], playerStart}`.
- Exits con `condFlag` opcional → gating de acceso.
- `gotoScene(id)` < 300 ms (sin async, sin network).

### 7. Puzzle logic
- `handleInteraction(sceneId, hotspotId)` — switch por escena+hotspot.
- Textos leídos de SCRIPT en tiempo de ejecución. Cero strings de guion en motor.
- Combos via `SCRIPT.combos[a|b]`.

## Hooks de test (window.*)

| Hook | Descripción |
|---|---|
| `window.__STATE` | Referencia al objeto G (flags, inventory, mode, scene) |
| `window.__tapWorld(x,y)` | Simula tap en coords canvas (0..180, 0..320) |
| `window.__lookWorld(x,y)` | Activa modo MIRAR + tap |
| `window.__advance()` | Avanza cutscene/diálogo/texto |
| `window.__gotoScene(id)` | Navega directo a escena (activa todos los flags) |
| `window.__setFlag(flag, val)` | Setea un flag manualmente |
| `window.__addItem(id)` | Añade item al inventario |

## Medición de rendimiento

- Budget por frame: 16.7 ms a 60 fps.
- Render de escena + personajes: <2 ms (canvas 2D puro, sin assets externos).
- Transición de escena: <1 ms (síncrona, in-memory).

## Deuda técnica declarada

| ID | Descripción | Impacto | Prioridad |
|---|---|---|---|
| DT-01 | Sin sonido/música | UX degradada | Media |
| DT-02 | Walkbox simple (AABB); sin pathfinding real | Player no rodea obstáculos | Baja |
| DT-03 | Sin guardado de partida (no localStorage por spec) | Reinicio al recargar | Per spec |
| DT-04 | Sprites geométricos, sin ilustraciones | Arte temporal | Alta (siguiente misión) |
| DT-05 | Dialog tree sin animación de reveal | UX texto plano | Baja |
| DT-06 | Sin accesibilidad (ARIA, keyboard) | No accesible | Media |
| DT-07 | Sin i18n (solo español) | Per spec (solo es-ES) | Baja |
| DT-08 | `onCutsceneEnd` hardcoded | Escalabilidad capítulos futuros | Media |

## Cómo ejecutar los tests

```bash
# Desde el directorio de misión:
pip install playwright
playwright install chromium
python3 el-atajo/tests/flow.py
# → genera el-atajo/docs/40-tech/shots/*.png
```

## Definition of Done verificable

- [x] `gate-m2`: docs/20-diseno/HANDOFF.md existe
- [x] `gate-m3`: docs/30-arte/HANDOFF.md existe
- [x] `sin-guion-en-motor`: Grep de strings narrativos en src/engine.js → 0 resultados
- [x] `flujo-completo`: flow.py sale con código 0
- [x] `shots`: ≥5 PNG en docs/40-tech/shots/
- [x] `handoff`: docs/40-tech/HANDOFF.md existe
- [ ] `calidad-ux`: evaluación manual en dispositivo real
