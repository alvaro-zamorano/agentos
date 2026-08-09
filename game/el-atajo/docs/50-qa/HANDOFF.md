# HANDOFF — QA Solver · El Atajo Capítulo 1

**Agente:** m5-qa-solver  
**Fecha:** 2026-08-09  
**Estado:** ✅ COMPLETADO (solver-pasa, informe, fracasos-hablan)

---

## Qué se hizo

### 1. Solver (`tests/solver.py`)

Solver Playwright que:
- Carga `data/graph.json` y verifica estructura (40 nodos, 48 aristas)
- Levanta servidor HTTP local apuntando al motor real
- Ejecuta **3 rutas** contra el motor (Chromium headless):
  - **Ruta 1** (canónica): intro completa → Bancales → Sótano → Telar → Exvoto
  - **Ruta 2** (permutación DC→A→B): Sótano primero → Bancales+cera → Telar → Exvoto
  - **Ruta 3** (permutación A→B→DC): Bancales → Telar → Sótano → Exvoto
- Ejecuta **test adversarial**: 10 items × 4 hotspots aleatorios (semilla 42, reproducible), verifica que ningún combo falla silenciosamente
- Genera `docs/50-qa/data/results.json` y `docs/50-qa/INFORME.md`
- Exit 0 si las 3 rutas pasan

**Resultado:** 3/3 rutas PASS, 40 combos adversariales, 3 fallos silenciosos documentados

### 2. Bug crítico corregido en el solver (no en el motor)

**Hotspot overlap `archivador` ↔ `libro_deudas` en sótano:**
- `archivador`: `x=0..65, y=56..166`
- `libro_deudas`: `x=0..64, y=146..168`
- En `y=146..166` ambos hotspots se solapan; `archivador` tiene prioridad (primero en lista)
- El solver usaba `(32, 157)` para `libro_deudas` → caía en `archivador` → `item_nombre_escrito` nunca se obtenía
- **Fix:** coordenadas cambiadas a `(32, 167)` (fuera del rango de `archivador`, dentro de `libro_deudas`)
- Este solapamiento de hitboxes también está documentado como bug en `docs/CHANGE-REQUESTS.md`

### 3. Bugs documentados (no parchados en el motor)

3 fallos silenciosos en `puerta_trasera@venta` cuando `flag_sala_telar_abierta=true`:
- Al usar cualquier item en la puerta trasera abierta, el motor transiciona a `telar` sin texto de feedback
- Items afectados: `item_tarro_vacio`, `item_tijeras`, `item_papel_estraza`
- Documentados en `docs/CHANGE-REQUESTS.md`

---

## Artefactos generados

| Fichero | Descripción |
|---|---|
| `tests/solver.py` | Solver QA completo con 3 rutas + adversarial |
| `docs/50-qa/INFORME.md` | Informe QA con rutas, tiempos, adversarial, checklist |
| `docs/50-qa/data/results.json` | Datos crudos de la sesión (JSON, importable) |
| `docs/CHANGE-REQUESTS.md` | Bugs encontrados para el equipo de desarrollo |

---

## Resultados de la última ejecución

```
Rutas completadas:    3/3  ✅
Combos adversariales: 40
Fallos silenciosos:   3   (todos en puerta_trasera@venta, no bloqueantes)
Errores de consola:   0
Estado:               PASS ✓
Tiempo total:         ~103s
```

| Ruta | Nombre | Estado | Tiempo |
|---|---|---|---|
| 1 | intro→A→DC→B | ✅ PASS | 21.9s |
| 2 | DC→A→B | ✅ PASS | 17.7s |
| 3 | A→B→DC | ✅ PASS | 16.7s |

---

## Cómo reproducir

```bash
# Desde el workspace root
python3 el-atajo/tests/solver.py
# → exit 0 si todo pasa
# → genera docs/50-qa/INFORME.md y docs/50-qa/data/results.json
```

Requiere: `pip install playwright && playwright install chromium`

---

## Para el próximo agente

- Los 3 bugs de `puerta_trasera` son **no bloqueantes** pero afectan la experiencia: el jugador no recibe feedback cuando usa un item en una puerta abierta. Ver `docs/CHANGE-REQUESTS.md`.
- El solapamiento de hotspot `archivador/libro_deudas` en sótano es un **bug real de hitbox** que afectaría al jugador que intente usar papel en el libro (tardaría más en descubrir que tiene que clickar más abajo). Documentado en CHANGE-REQUESTS.
- El solver usa hooks de test (`__tapWorld`, `__STATE`, `__addItem`, `__setFlag`) definidos en `src/engine.js`. Si el motor cambia su API pública, revisar el solver.

---

*Handoff generado automáticamente por el agente m5-qa-solver.*
