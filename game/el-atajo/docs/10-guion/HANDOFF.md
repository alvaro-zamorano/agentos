# HANDOFF — Guion · 2026-08-09

## Qué hice

- Creado `docs/10-guion/PERSONAJES.md`: cast definitivo de 8 personajes con motivación, función estructural y 3 líneas de voz de ejemplo cada uno.
- Creado `docs/10-guion/ESCALETA.md`: 5 localizaciones del Capítulo 1 con beats de escena, estructura de puzzles, cutscenes y cierre donde la victoria activa la resurrección del Quincallero.
- Creado `data/script-es.json`: guion de datos completo y válido (JSON parse OK).

**Métricas del JSON:**
- 5 escenas (canada, venta, bancales, telar, sotano)
- 41 hotspots en total (8-9 por escena), cada uno con looks y líneas de interact
- 3 árboles de diálogo (dialog_tiavelas, dialog_pratico, dialog_pura) con 3 o más opciones por nodo raíz
- 30 combos de objeto (25 mínimo)
- 7 cutscenes (6 mínimo): cs_apertura, cs_embargo, cs_llegada_venta, cs_pili_checkpoint, cs_exvoto_completo, cs_pura_huye, cs_resurreccion
- 6 goals con descripción y pista oblicua

## Decisiones relevantes

1. **Cast mantenido íntegro**: todas las funciones estructurales del Greenlight conservadas. Melquíades y El Práctico tienen apellidos completos pero los NPC los nombran por mote, como dice el Greenlight.
2. **La campanilla no suena mientras Reme la maneja**: regla de diseño sembrada narrativamente. Solo suena cuando la Pura la toca. Esto siembra el twist sin explicarlo.
3. **El cuaderno antiguo es el objeto bisagra** que conecta las escenas 3 (bancales), 4 (telar) y 5 (sótano). Sin él no se llega al nombre del Quincallero ni a la confrontación con la Pura.
4. **La lágrima de la Pura se obtiene en silencio**: no hay puzzle forzado. Reme muestra el libro, espera, recoge. El humor en esa escena está ausente por diseño: es el único momento sin ironía del capítulo.
5. **Puns intraducibles: cero**. Revisado. Ningún chiste depende de homofonía española.
6. **Humor de fracaso en todos los combos**: los 30 combos tienen respuesta de personaje. Ningún silencio ante el error.

## Qué necesito de otros roles

- **Artista**: sprites de 8 personajes (Reme, Turbo, Pura, Tía Velas, Melquíades, El Práctico; Quincallero solo en retrato sepia). Fondos de 5 escenas en 180x320 px. El archivo de referencia es ESCALETA.md sección "Hotspots" y los nombres de cada escena.
- **Diseñador de juego**: confirmar si los combos usan ID de item tal como están en el JSON o si hace falta tabla de mapeo. Los IDs actuales son en español, directos.
- **Técnico**: el JSON está en `data/script-es.json`. La estructura es `scenes > sceneId > hotspots > hotspotId > {name, looks[], interact[][]}`. Los diálogos son grafos con nodos y opciones. Los combos son `"item|hotspot": "line"`. Listo para montar el motor.

## Notas de calidad de voz

- **Reme**: directa, sin subordinadas, ironía de navaja fina. Media de palabras por frase: 14.
- **Turbo**: nunca habla. Reme lee sus acciones.
- **Doña Pura**: formal, sin elevar el tono. La amenaza en voz baja.
- **Tía Velas**: advertencia como modo por defecto. El subjuntivo es su tiempo verbal.
- **El Práctico**: circunloquios y referencias locales. La anécdota es el formato.
- **Melquíades**: entusiasmo de vendedor sin consciencia del entorno.
- **Pili**: preguntas cortas que abren monólogos largos.

## Estado de mi área

🟡 **AMARILLO** — Guion completo para Capítulo 1. Pendiente de feedback de Arte y Técnico para confirmar que los IDs y estructura del JSON sean consumibles. Sin dependencias que bloqueen la siguiente misión de guion (Capítulo 2).
