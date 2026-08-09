# HANDOFF — Diseño de Puzzles · Capítulo 1
## Misión atajo-m2-diseno-puzzles · 2026-08-09

---

## Qué hice

- Creado `data/graph.json`: grafo de dependencias hub-and-spoke con 40 nodos (item, flag, puzzle, cutscene) y 48 aristas `requires`. Nodo final marcado con `"final": true`.
- Creado `docs/20-diseno/PUZZLES.md`: spec completa de los 4 puzzles principales (uno por ingrediente del exvoto), con intención de diseño, pasos, pistas oblicuas, gag de recompensa y tabla de fracasos posibles con respuesta de personaje.
- Creado `tools/validate-graph.py`: validador ejecutable que verifica 5 criterios (referencias a guion, alcanzabilidad, ausencia de ciclos, ausencia de huérfanos, hub con ≥2 ramas). Sale con **exit 0** sobre el grafo entregado.
- Verificado alineamiento con `data/script-es.json`: todos los `script_ref` del grafo existen en el guion.

---

## Decisiones relevantes

### 1. Diseño hacia atrás desde el exvoto

Empecé por el estado final (4 ingredientes → exvoto → campanilla suena) y retrocedí preguntando: ¿qué necesito para obtener cada ingrediente? Esto evitó puzzles de relleno y garantiza que cada elemento del mundo tiene función estructural.

### 2. Cuatro ramas, cuatro tipos de puzzle

Asigné un tipo distinto a cada ingrediente:
- **Cera virgen** = transformación de objeto (fumigador calma abejas → tarro recoge cera). 2 pasos. Enseña la mecánica de preparación→acción.
- **Hilo de esparto** = información con solución lejos del problema (cuaderno de bancales abre caja de telar). 4 pasos. El Greenlight pide que en cadenas de 3+ pasos la solución viva lejos.
- **Nombre escrito** = observación de sistema social (leer el libro de deudas y entender quién es el Quincallero). 2 pasos. Recompensa al jugador que ha prestado atención a la narrativa.
- **Lágrima** = puzzle en capas con fracasos que informan (3 capas: falla directa → falla cuaderno → éxito libro). 4 pasos. El diseño más delicado: la solución requiere comprender el personaje, no solo la mecánica.

### 3. Objetos bisagra (cuaderno y libro de deudas)

El `item_cuaderno_antiguo` y el `item_libro_deudas` se usan en **dos ramas cada uno**. Esto:
- Mantiene la economía de objetos (≤12 simultáneos, todo objeto usado ≥1 vez).
- Crea coherencia narrativa: el mismo objeto que desbloquea una cadena de puzzles también avanza otra.
- Hace que el jugador que explora un rama recoja info útil para otra sin saberlo.

### 4. El tarro de cristal como objeto reutilizable

El mismo `item_tarro_vacio` recoge la cera en bancales y la lágrima en el sótano. Tía Velas extrae la cera y devuelve el tarro vacío. Este uso doble no necesita explicación en UI: el tarro visible en el inventario después de la entrega es la pista.

### 5. La Rama D y la no-violencia narrativa

El puzzle de la lágrima (Rama D) se resuelve mostrando a Pura su propio nombre en el libro de deudas. No hay engaño, no hay violencia: la verdad desencadena la emoción. Este diseño:
- Es coherente con el tono del juego (humor de navaja, sin crueldad).
- Recompensa al jugador que ha entendido quién es el Quincallero y qué son las deudas pendientes.
- El único momento del capítulo sin ironía de Reme.

### 6. Hub con dos spokes simultáneos

Desde `puzzle_hub_explora` se abren dos spokes en paralelo: portillo (bancales) y sótano. Dentro de bancales, dos sub-branches también simultáneas (cera y cuaderno). El jugador nunca tiene solo una opción.

---

## Estructura del grafo — métricas

| Métrica | Valor |
|---------|-------|
| Total nodos | 40 |
| Cutscenes | 7 |
| Flags | 6 |
| Items | 10 |
| Puzzles | 17 |
| Total aristas | 48 |
| Ramas desde hub | 2 (portillo + sótano) |
| Ramas cortas (≤2 pasos) | 2 (Rama A y C) |
| Ramas largas (3-4 pasos) | 2 (Rama B y D) |
| Objetos simultáneos máximos | ~8 (límite: 12) |

---

## DoD cumplida

| Check | Estado |
|-------|--------|
| gate-m1: HANDOFF del guion | ✓ docs/10-guion/HANDOFF.md existe |
| grafo: data/graph.json | ✓ creado y válido |
| specs: docs/20-diseno/PUZZLES.md | ✓ creado con spec completa |
| validador-pasa: exit 0 | ✓ python3 tools/validate-graph.py → exit 0 |
| handoff: docs/20-diseno/HANDOFF.md | ✓ este fichero |
| calidad-diseno | ✓ cumple manual (ver PUZZLES.md §verificación) |

---

## Qué necesito de otros roles

### Técnico (motor)
- El grafo en `data/graph.json` usa la misma estructura de IDs que `data/script-es.json`. Los campos `script_ref` de cada nodo apuntan directamente a hotspot IDs o cutscene IDs del guion.
- El campo `"final": true` en el nodo `cs_resurreccion` marca el estado de victoria.
- Los flags (`type: "flag"`) son estados booleanos que el motor gestiona internamente.
- Los puzzles con múltiples prerequisitos (aristas entrantes) requieren que TODOS los prerequisitos estén satisfechos antes de activarse (AND-gate, no OR-gate).

### Artista
- La transición de estado de la colmena (antes/después del fumigador) necesita dos estados visuales distintos: abejas en movimiento vs. humo tranquilo.
- La caja del telar (`caja_lacre`) necesita dos estados: lacrada vs. abierta con tijeras visibles.
- El olivo partido necesita la oquedad visible y un objeto marrón (cuaderno) asomando en la segunda mirada de Turbo.
- El momento D3 (Pura llora de espaldas) es el único sin gag visual: necesita un beat de silencio claro.

### Guionista (Capítulo 2)
- La Rama D revela que Pura también está en el libro de deudas del Quincallero → tiene deuda pendiente con él.
- La campanilla que Pura lleva en el maletín al salir la convierte en vector de la resurrección del Quincallero.
- Estos dos hilos son semilla directa del Capítulo 2. Ver `docs/CHANGE-REQUESTS.md` para ajuste menor solicitado al guion.

---

## Estado del área

🟢 **VERDE** — Grafo completo, validado (exit 0), coherente con script-es.json. Spec de puzzles con los 4 tipos requeridos, 4 gags de recompensa y tablas de fracaso. Sin dead-ends. Listo para que Técnico monte el motor de puzzles y Arte diseñe los estados de escena.
