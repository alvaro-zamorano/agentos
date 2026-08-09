# Change Requests — El Atajo · Capítulo 1

Bugs encontrados por QA (agente m5-qa-solver, 2026-08-09).  
**No parcheados en el motor.** Para el equipo de desarrollo.

---

## CR-001 · Fallo silencioso: usar item en puerta_trasera abierta (venta)

**Severidad:** Media — no bloquea avance, pero rompe el pilar "ningún fracaso silencioso"  
**Reproducibilidad:** 100% (confirmado en test adversarial, semilla 42)

**Descripción:**  
Cuando `flag_sala_telar_abierta = true` y el jugador usa cualquier item sobre el hotspot `puerta_trasera` en la escena `venta`, el motor ejecuta `gotoScene('telar')` sin mostrar ningún texto de feedback. El jugador no recibe confirmación de que el item fue ignorado o de que la puerta se abrió.

**Combos afectados (probados):**
- `item_tarro_vacio` + `puerta_trasera@venta` → transición silenciosa a telar
- `item_tijeras` + `puerta_trasera@venta` → transición silenciosa a telar
- `item_papel_estraza` + `puerta_trasera@venta` → transición silenciosa a telar

**Código implicado (`src/engine.js`):**
```javascript
if (sceneId === 'venta' && hotspotId === 'puerta_trasera') {
  if (G.flags.flag_sala_telar_abierta) {
    gotoScene('telar'); return;  // ← sin texto ni feedback de item
  }
  const t = getInteractText(sk, 'puerta_trasera', 0);
  if (t) showText(t.speaker, t.line);
  return;
}
```

**Fix sugerido:**  
Antes de `gotoScene('telar')`, si hay un item seleccionado, mostrar un texto genérico de "La puerta ya está abierta" o simplemente ignorar el item y navegar con feedback:
```javascript
if (G.flags.flag_sala_telar_abierta) {
  if (item) {
    showText('REME', '...');  // texto de no usar item en puerta
    deselectItem();
  }
  gotoScene('telar'); return;
}
```

---

## CR-002 · Solapamiento de hitboxes: archivador ↔ libro_deudas (sótano)

**Severidad:** Alta — afecta la jugabilidad directamente (el jugador no puede usar el papel en el libro)  
**Reproducibilidad:** 100%

**Descripción:**  
Los hotspots `archivador` y `libro_deudas` en la escena `sotano` se solapan en la zona `y=146..166`:

| Hotspot | x | y | w | h | Rango y |
|---|---|---|---|---|---|
| `archivador` | 0 | 56 | 65 | 110 | 56..166 |
| `libro_deudas` | 0 | 146 | 64 | 22 | 146..168 |

El motor itera hotspots en orden y se queda con el primero. Puesto que `archivador` aparece antes en la lista, cualquier click en `y=146..166` activa `archivador`, no `libro_deudas`. La única zona exclusiva de `libro_deudas` es `y=167..168` (2 píxeles en un canvas de 320px de alto).

**Consecuencia para el jugador:**  
Al intentar usar `item_papel_estraza` sobre el libro de deudas (para escribir el nombre), el click cae en el archivador. Si el libro ya está en inventario, el archivador muestra texto genérico y el nombre nunca se escribe. El puzzle queda bloqueado hasta que el jugador pruebe coordenadas muy bajas del sprite.

**Fix sugerido:**  
Ajustar las dimensiones del hotspot `archivador` para que no cubra la zona del `libro_deudas`:
```javascript
{ id: 'archivador', x: 0, y: 56, w: 65, h: 88 },  // h: 110→88, rango y: 56..144
```
O reordenar hotspots en el array (poner `libro_deudas` antes que `archivador`).

---

## CR-003 · (Menor) Tarro_vacio consumido antes de ser necesario en sótano (ruta canónica)

**Severidad:** Baja — el motor acepta el item forzado, no bloquea  
**Tipo:** Diseño de flujo, no bug de código

**Descripción:**  
En la ruta canónica (Bancales → Sótano → Telar), el `item_tarro_vacio` se consume en bancales (al recoger la cera de la colmena). En el sótano, el jugador necesita el tarro para recoger la lágrima de Doña Pura. El motor no comprueba si el item está en inventario antes de ejecutar la lógica de la lágrima (usa `G.selected_item` directamente), lo que significa que funciona pero el jugador debería recibir un error de "no tengo el tarro". 

**Posible mejora:**  
Añadir una comprobación `hasItems('item_tarro_vacio')` antes de recoger la lágrima, y mostrar texto de "Necesito algo donde guardarla" si el tarro ya fue consumido. Esto requeriría una segunda fuente de tarro o un tarro reutilizable.

---

*Generado por el solver QA (`tests/solver.py`). Semilla adversarial: 42.*
