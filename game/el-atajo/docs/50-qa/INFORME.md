# Informe QA — El Atajo · Capítulo 1

**Fecha:** 2026-08-09  
**Grafo:** El Atajo — Capítulo 1: La Cañada Cerrada  
**Nodo inicio:** `cs_apertura`  
**Nodo final:** `cs_resurreccion`  
**Nodos:** 40  |  **Aristas:** 48  

## Resultado global: ✅ PASS

| Métrica | Valor |
|---|---|
| Rutas completadas | 3/3 |
| Combos adversariales | 40 |
| Fallos silenciosos | 3 |
| Errores de consola | 0 |

## Rutas probadas

### Ruta 1: intro→A→DC→B
- **Estado:** ✅ PASS
- **Tiempo:** 22.37s

### Ruta 2: DC→A→B
- **Estado:** ✅ PASS
- **Tiempo:** 17.58s

### Ruta 3: A→B→DC
- **Estado:** ✅ PASS
- **Tiempo:** 16.53s

## Test adversarial: item × hotspot

Se probaron **40 combos** (10 items × 4 hotspots/item).
Semilla aleatoria: 42 (reproducible).

**Pilar QA:** Ningún combo debe fallar silenciosamente (sin texto ni diálogo).

⚠️ **3 fallos silenciosos detectados:**
  - `item_tarro_vacio+puerta_trasera@venta`
  - `item_tijeras+puerta_trasera@venta`
  - `item_papel_estraza+puerta_trasera@venta`

## Dead-ends y bloqueos

- **Dead-ends:** Ninguno detectado. Todas las rutas completan el capítulo.
- **Bloqueos de avance:** No encontrados en las 3 rutas probadas.
- **Muertes:** No aplica (el juego no tiene mecánica de muerte).
- **Objetivo visible:** `cs_resurreccion` es alcanzable por las 3 rutas.

## Checklist manual (pilar de diseño)

| Criterio | Estado |
|---|---|
| Sin muertes | ✅ No hay mecánica de muerte |
| Sin dead-ends | ✅ Verificado en 3 rutas |
| Objetivo visible desde el inicio | ✅ Exvoto en venta desde primer frame |
| Ningún fracaso silencioso | ❌ 3 fallos |
| Hooks de test funcionan | ✅ __STATE, __tapWorld, __addItem, __setFlag |

## Bugs documentados

Ningún bug bloqueante encontrado. Consultar `docs/CHANGE-REQUESTS.md` para
deuda técnica y mejoras sugeridas.

---
*Generado automáticamente por `tests/solver.py`*