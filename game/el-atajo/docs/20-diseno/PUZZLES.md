# PUZZLES — Capítulo 1: La Cañada Cerrada
## Diseño hacia atrás · Estructura hub-and-spoke
### Misión atajo-m2 · 2026-08-09

---

## OBJETIVO DEL CAPÍTULO (estado final)

Quemar el exvoto de cera con 4 ingredientes → la cañada se abre → Doña Pura huye → la campanilla suena.

**Diseño hacia atrás:** para conseguir el exvoto necesito los 4 ingredientes. Cada ingrediente es el final de una cadena de puzzles. Las cadenas comparten objetos bisagra (cuaderno, libro de deudas) que crean dependencias cruzadas.

---

## MAPA DE DEPENDENCIAS (resumen textual)

```
cs_apertura → cs_embargo → puzzle_canada_llegada → flag_venta_activa
    → cs_llegada_venta → puzzle_hub_explora
        ├─[RAMA A/B] puzzle_portillo_info → flag_portillo_conocido
        │    ├─ item_fumigador → puzzle_fumigador_colmena (A1)
        │    │   → flag_bees_calmed → puzzle_cera_recolectar + item_tarro_vacio (A2)
        │    │       → item_cera_virgen → puzzle_cera_entrega → cs_pili_checkpoint_1
        │    │           → flag_sala_telar_abierta + item_cuaderno_antiguo (B3)
        │    │               → puzzle_telar_caja → item_tijeras → puzzle_hilo_tijeras (B4)
        │    │                   → item_hilo_esparto
        │    └─ puzzle_olivo_cuaderno (B1) → item_cuaderno_antiguo
        │
        └─[RAMA C/D] puzzle_sotano_info → flag_sotano_acceso
             ├─ puzzle_archivador_consulta (C1) → item_papel_estraza + item_libro_deudas
             │   → puzzle_nombre_escribir (C2) → item_nombre_escrito
             └─ puzzle_pura_fail (D1, falla) → puzzle_pura_cuaderno (D2, falla)
                 → puzzle_pura_libro (D3) + item_libro_deudas
                     → flag_pura_confrontada → puzzle_lagrima_recoger + item_tarro_vacio (D4)
                         → item_lagrima

puzzle_exvoto_final ← item_cera_virgen + item_hilo_esparto + item_nombre_escrito + item_lagrima
    → cs_exvoto_completo → cs_pura_huye → cs_resurreccion (FIN)
```

---

## RAMA A — Cera Virgen (2 pasos, corta)

**Tipo de puzzle:** Transformación de objeto
**Localización:** Bancales / Colmena
**Ingrediente producido:** item_cera_virgen

### Intención de diseño

La rama más directa del hub. El jugador ve el problema (abejas que bloquean la colmena) y tiene la solución en escena (fumigador abandonado junto al muro). La solución requiere dos pasos en secuencia: primero calmar, luego recoger. Enseña la mecánica de "preparación → acción" que el juego usará más adelante.

**Norma del Greenlight cumplida:** "Jugable con un pulgar en un metro de autobús." Dos taps en el orden correcto.

### Pasos

| Paso | Acción | Resultado |
|------|--------|-----------|
| A1   | Usar `item_fumigador` en hotspot `colmena` | `flag_bees_calmed` |
| A2   | Usar `item_tarro_vacio` en hotspot `colmena` (requiere `flag_bees_calmed`) | `item_cera_virgen` |

**Prerequisito:** `flag_portillo_conocido` (llegar a los bancales por el portillo del Práctico).

**Objetos necesarios:** item_fumigador (encontrado junto al muro de piedra seca), item_tarro_vacio (encontrado en el bancal).

### Pistas oblicuas

- Turbo huele el muro de piedra y retrocede → lleva al jugador al fumigador visualmente.
- Tía Velas, en el hub: "El fumigador calma a las abejas. No las engaña. Solo les dice que no tienes prisa."
- Look del tarro_vacio: "Tiene restos de cera en el borde. Alguien se adelantó, pero dejó el tarro." → sugiere que el tarro ya ha servido para esto antes.
- Look de la colmena: "La colmena está activa. No hay forma de acercarse sin protección." → el problema es claro.

### Gag de recompensa

Reme recoge la cera del panal interior con el tarro. Turbo, que había retrocedido del olivo, vuelve a mirarla. REME (narrando): "La primera vez que una abeja me deja hacer mi oficio sin cobrarme. Ha sido más barato que la mayoría de mis clientes."

### Fracasos posibles y respuestas

| Acción incorrecta | Respuesta de Reme |
|---|---|
| Usar `tarro_vacio` en colmena sin calmar abejas | "Me acerco. Una abeja me avisa. Retrocedo. El diálogo ha sido claro." |
| Usar `fumigador` en colmena sin tarro en inventario | "Las abejas están calmadas. Ahora necesito algo donde recoger la cera. La mano no vale." |
| Usar `fumigador` en otros hotspots (Tía Velas, gato, telar) | Respuestas individuales registradas en combos del script. Ningún silencio. |
| Usar `tarro_vacio` en pozo_seco | "Bajo el tarro. Sube polvo. El registro sigue vacío." |
| Usar `tarro_vacio` en barrica_miel | "La miel no es de bote. Es de barrica y de proceso. Tía Velas lo explica con la mirada." |

---

## RAMA B — Hilo de Esparto (4 pasos, larga)

**Tipo de puzzle:** Información (solución lejos del problema)
**Localización:** Bancales → Venta (hub) → Sala del Telar
**Ingrediente producido:** item_hilo_esparto

### Intención de diseño

La cadena más larga. El problema está en el telar (la madeja de esparto necesita tijeras), pero las tijeras están en una caja lacrada. La llave conceptual (el cuaderno) está en una localización completamente diferente (bancales/olivo). El jugador que entiende los lacres verá la conexión: la caja tiene los mismos lacres que Doña Pura usa en los embargos. El cuaderno del olivo tiene nombres de deudores. Los lacres son del Quincallero. La caja se abre al reconocer la conexión documental.

**Norma del Greenlight cumplida:** "El QUÉ siempre visible, el CÓMO nunca regalado." El problema (madeja necesita tijeras) es inmediato. La solución (cuaderno del bancal abre la caja del telar) requiere que el jugador infiera el nexo entre los lacres, los nombres y el sistema del Quincallero.

**Norma del manual cumplida:** "En cadenas de 3 o más pasos la solución vive lejos del problema." El cuaderno (bancales, escena exterior) desbloquea la caja (telar, interior de la Venta). Son escenas distintas separadas por la entrega de la cera.

### Pasos

| Paso | Acción | Resultado |
|------|--------|-----------|
| B1   | Examinar hotspot `olivo_partido` en bancales | `item_cuaderno_antiguo` |
| B2   | Entregar `item_cera_virgen` a `tia_velas` en venta | `flag_sala_telar_abierta` + `cs_pili_checkpoint_1` |
| B3   | Usar `item_cuaderno_antiguo` en hotspot `caja_lacre` en telar | `item_tijeras` |
| B4   | Usar `item_tijeras` en hotspot `madeja_esparto` en telar | `item_hilo_esparto` |

**Prerequisito de B1:** `flag_portillo_conocido` (bancales accesibles).
**Prerequisito de B2:** `item_cera_virgen` (rama A completada).
**Prerequisito de B3:** `flag_sala_telar_abierta` + `item_cuaderno_antiguo`.

### Pistas oblicuas

- Turbo huele el olivo y ladea la cabeza → señal no verbal de que hay algo dentro.
- Look de olivo_partido (2ª vez): "El olivo partido tiene una oquedad grande en el tronco. Perfecta para guardar o para perder cosas."
- Look de caja_lacre: "Los lacres son del mismo molde que los de los embargos. Esto se complica más de lo que parecía."
- Look de tijeras_oxidadas: "Las tijeras están en la caja. La caja tiene un lacre. El lacre es el problema de hoy."
- Tía Velas: "El esparto trenzado ata lo que el exvoto quiere retener. La madeja está en el telar. La puerta trasera la abro yo cuando tengas la cera."

### Gag de recompensa

Reme usa el cuaderno sobre la caja lacrada. Los nombres del cuaderno coinciden con los sellos de la caja. La caja se abre como si hubiera estado esperando ser reconocida. REME (narrando): "La caja no tenía cerradura. Tenía memoria. Y yo le dije lo que sabía. Suficiente."

Reme corta la madeja. El hilo sale limpio. Tía Velas lo acepta sin mirarlo: lo huele. Dice: "El esparto tiene que saber a campo, no a mano. Huele a campo." Reme: "También huele a tijeras oxidadas. Pero eso ya lo arreglará el exvoto."

### Fracasos posibles y respuestas

| Acción incorrecta | Respuesta de Reme |
|---|---|
| Usar cualquier item en `madeja_esparto` sin tijeras | "La madeja está aquí. Las tijeras están en otro sitio. Así es este día." |
| Usar `item_cuaderno_antiguo` en `madeja_esparto` | "Lo ato. El cuaderno no lo necesitaba. Yo sí necesitaba hacer algo con las manos." |
| Usar `item_cuaderno_antiguo` en `telar` (no en caja) | "El telar es mayor que yo y más complicado. El cuaderno no simplifica nada." |
| Intentar entrar al telar sin haber entregado la cera | "Cerrada. Tía Velas la abre cuando le parece, no cuando yo lo decido." |
| Usar `madeja_esparto` en `rueca` | "La madeja no va en la rueca. O va, pero no así, y no es el momento de aprenderlo." |

---

## RAMA C — Nombre Escrito (2 pasos, corta)

**Tipo de puzzle:** Observación de sistema social
**Localización:** Sótano del Registro
**Ingrediente producido:** item_nombre_escrito

### Intención de diseño

La rama de información pura. El jugador accede al sótano (acceso paralelo al bancal, abierto desde el hub) y descubre el sistema que conecta todos los embargos: el Quincallero tiene un nombre verdadero enterrado en el registro, y ese nombre es la clave del exvoto. El puzzle es de lectura y cruce de información: papel en blanco + nombre en el archivador = nombre escrito en papel.

**Observación de sistema social:** el jugador no resuelve un mecanismo físico, sino que lee un patrón social (el Quincallero como figura de deuda oculta detrás de un nombre falso). El puzzle valida que el jugador ha entendido quién es el Quincallero.

### Pasos

| Paso | Acción | Resultado |
|------|--------|-----------|
| C1   | Examinar hotspot `archivador` en sótano | `item_papel_estraza` + `item_libro_deudas` |
| C2   | Usar `item_papel_estraza` con hotspot `libro_deudas` | `item_nombre_escrito` |

**Prerequisito:** `flag_sotano_acceso` (Práctico explica la entrada por la higuera).

**Pistas del Práctico (para acceso):** "El sótano del registro tiene entrada propia por la parte de la higuera. La puerta está sin llave desde el ochenta y nueve." + advertencia sobre firmar sin querer (siembra tensión sin bloquear).

### Pistas oblicuas

- Look de archivador (2ª): "El archivador huele a papel viejo y a cosas que alguien quiso enterrar y no enterró." → hay algo que encontrar.
- Look de libro_deudas: "El libro tiene el nombre en la portada. Eustasio Quero Pintado. Ya lo sé. Y ahora no puedo no saberlo."
- Interact de archivador: "El cajón tercero no cierra del todo. Dentro están los registros más viejos. Y el nombre que busco." → el jugador sabe qué busca.
- Tía Velas (hub): "El nombre verdadero del Quincallero. No el que usaba de camino. El del registro. Sin él el exvoto no sabe a quién apunta."

### Gag de recompensa

Reme copia el nombre en el papel. REME (narrando): "Eustasio Quero Pintado. Un nombre que nadie dice en voz alta. Como si pronunciarlo te comprometiera. Lo escribí con la letra más clara que tengo. No mucho, pero suficiente para que el exvoto lo reconozca." Turbo, fuera del sótano, ladra una vez. Reme: "Turbo aprueba el nombre. Eso es lo más tranquilizador de esta tarde."

### Fracasos posibles y respuestas

| Acción incorrecta | Respuesta de Reme |
|---|---|
| Usar `item_papel_estraza` en `retrato_quincallero` | "El papel se niega a doblarse sobre el retrato. O lo noto yo. Guardo el papel." |
| Usar `item_papel_estraza` en `campanilla_caja` | "Envolver la campanilla en papel no cancela lo que es. Lo noto antes de hacerlo." |
| Intentar leer `archivador` sin entrar al sótano | (no accesible sin flag_sotano_acceso) |
| Usar `cuaderno_antiguo` en `archivador` | "El cuaderno encaja en el archivador como si siempre hubiera sido suyo. Pero no es el que busco ahora." |

---

## RAMA D — Lágrima de Deudor (3-4 pasos, larga)

**Tipo de puzzle:** En capas con fracasos que informan
**Localización:** Sótano del Registro
**Ingrediente producido:** item_lagrima

### Intención de diseño

El puzzle más difícil del capítulo. La solución es invisible al principio: ¿cómo hacer que Doña Pura, funcionaria implacable, llore? Cada fracaso enseña algo sobre el personaje y acerca al jugador a la solución. Los fracasos no bloquean: informan, ajustan la estrategia y revelan capas de Pura que de otra forma permanecerían ocultas.

**Diseño sin violencia, sin trampa:** la lágrima no se arranca. Se provoca con la verdad. El jugador descubre que Pura también está en el libro de deudas (páginas en blanco con su nombre) y ese descubrimiento la rompe.

**Norma de Greenlight:** "Cada fracaso paga con un chiste — nunca silencio." Las dos fases de fallo tienen respuestas de personaje específicas que dan información y mantienen el humor de la voz de Reme.

### Pasos (secuencia de capas)

| Paso | Acción | Resultado | Tipo |
|------|--------|-----------|------|
| D1 | Acercarse a Pura en `pura_escritorio` sin palanca → `dialog_pura` → `dp_registro` → `dp_cierre_neutral` | Pura cierra el diálogo. Reme aprende: necesita algo que Pura no pueda ignorar | Fracaso 1 — informa: la autoridad burocrática no se rompe con argumentos |
| D2 | Usar `item_cuaderno_antiguo` en Pura (`dp_cuaderno`) | Pura reconoce los nombres del pueblo pero no se altera. Reme aprende: los nombres de otras personas no la afectan | Fracaso 2 — informa: necesita algo personal, algo de Pura |
| D3 | Usar `item_libro_deudas` en Pura (`dp_libro` → `dp_libro2` → `dp_libro3` → `dp_libro4` → `dp_lagrima`) | Pura ve su nombre en las páginas en blanco. Se rompe. Llora una vez, de espaldas | Éxito — el detonante es la deuda personal de Pura |
| D4 | Usar `item_tarro_vacio` en Pura durante `flag_pura_confrontada` | `item_lagrima` | Recolección en silencio |

**Prerequisito:** `flag_sotano_acceso` + `item_cuaderno_antiguo` (de Rama B, paso B1) + `item_libro_deudas` (de Rama C, paso C1) + `item_tarro_vacio`.

### Por qué D1 y D2 fallan (y qué enseñan)

**D1 (acercarse sin palanca):**
Pura cita el reglamento. El horario. El formulario. No hay grieta. Reme aprende que la Pura tiene blindaje institucional y que argumentos legales no sirven.
→ El jugador entiende: necesita palanca personal, no institucional.

**D2 (mostrar cuaderno):**
Pura lee los nombres. Dice: "Estos nombres son del pueblo. Algunos ya no están." Fría, profesional. No es su problema personal. Reme aprende: los daños colectivos no la mueven.
→ El jugador entiende: tiene que mostrarle algo que la afecte a ELLA.

**D3 (mostrar libro con su nombre):**
La página en blanco con el nombre de Pura. Las deudas pendientes sin fecha. El libro de deudas del Quincallero la incluye. Pura no puede ignorarlo. Llora una vez, sola, de espaldas.
→ El jugador entiende: no era una funcionaria corrupta a sabiendas. Era también víctima.

### Pistas oblicuas

- Tía Velas: "Una lágrima de alguien que le deba algo al Quincallero. Alguien que todavía esté en el libro." → el libro importa.
- Tía Velas: "¿La Pura está en el libro? Eso es lo que tienes que descubrir tú. Yo no leo libros ajenos." → siembra la pregunta sin responderla.
- Look de libro_deudas: "El libro tiene páginas en blanco al final. Eso es lo más preocupante de todo lo que he visto hoy." → el jugador nota las páginas en blanco antes de entender su función.
- Pura (D2): "Estos nombres son del pueblo. Algunos ya no están." → distancia emocional. Reme nota que no se altera.
- El tarro ya está en inventario (lo usó para la cera). Tía Velas devolvió el tarro vacío al entregar la cera → el objeto bisagra está disponible.

### Gag de recompensa

La Pura llora una vez, de espaldas. Reme recoge la lágrima con el tarro sin decir nada. REME (narrando a Pili): "La Pura lloró una vez. No volvió a hacerlo. No era necesario." La lágrima en el tarro tiene un color que no esperaba: no es transparente. "No sé qué color tiene una lágrima de deuda. Ahora lo sé. Y preferiría no haberlo descubierto." PILI: "¿Era muy distinto?" REME: "Era exactamente lo que me imaginaba. Eso es lo peor."

### Fracasos posibles y respuestas

| Acción incorrecta | Respuesta |
|---|---|
| Usar `tarro_vacio` en Pura antes de `flag_pura_confrontada` | "La Pura no llora por las buenas. Y yo no tengo un embudo para el aguante." |
| Usar `item_cera_virgen` en `pura_escritorio` | "Pegar cera a la funcionaria no cancela los embargos. Lo he pensado igualmente." |
| Usar `fumigador` en `pura_escritorio` | "Ahumar el escritorio no cancela el embargo. Lo he pensado igualmente." (respuesta del script) |
| Usar `lacre` en `pura_escritorio` | "Sellar su propio escritorio contra ella. No está mal como idea. No funciona, pero no está mal." (respuesta del script) |
| Intentar acercarse a Pura sin entrar al sótano | (no accesible sin flag_sotano_acceso) |

---

## PUZZLE FINAL — Exvoto de Cera (1 paso)

**Localización:** La Venta (hub)
**Acción:** Entregar los 4 ingredientes a Tía Velas → `cs_exvoto_completo`

### Orden flexible de entrega

El juego acepta los ingredientes en cualquier orden. Tía Velas reacciona a cada uno con una línea específica:
- Cera virgen: "Cera buena. Primera vez hoy que algo sale bien." (ya vista en el combo del script)
- Hilo de esparto: Tía Velas enrolla el hilo y lo guarda en el mandil. Sin palabras.
- Nombre escrito: "Lee el nombre en voz baja y cierra los ojos un momento. Luego los abre y sonríe poco."
- Lágrima: (abre el tarro, lo huele, lo cierra) "La deuda está en el recipiente. El recipiente ya puede arder."

### Gag de recompensa final

Tía Velas quema el exvoto. El humo sube recto. La campana de la venta suena sola. REME (narrando): "Fue entonces cuando me di cuenta de que habíamos ganado la batalla equivocada." Beat. PILI: "Reme. ¿La campanilla sonó?" REME: "Sonó, Pili. Y lo que vino después ya no es historia de esta noche."

---

## ECONOMÍA DE OBJETOS

| Objeto | Obtenido en | Usado en | Veces usado |
|--------|------------|----------|-------------|
| item_fumigador | bancales/muro_piedra | puzzle_fumigador_colmena | 1 |
| item_tarro_vacio | bancales/tarro_vacio | puzzle_cera_recolectar + puzzle_lagrima_recoger | 2 |
| item_cuaderno_antiguo | bancales/olivo_partido | puzzle_telar_caja + puzzle_pura_cuaderno | 2 |
| item_cera_virgen | puzzle_cera_recolectar | puzzle_cera_entrega + puzzle_exvoto_final | 2 |
| item_tijeras | puzzle_telar_caja | puzzle_hilo_tijeras | 1 |
| item_hilo_esparto | puzzle_hilo_tijeras | puzzle_exvoto_final | 1 |
| item_papel_estraza | puzzle_archivador_consulta | puzzle_nombre_escribir | 1 |
| item_libro_deudas | puzzle_archivador_consulta | puzzle_nombre_escribir + puzzle_pura_libro | 2 |
| item_nombre_escrito | puzzle_nombre_escribir | puzzle_exvoto_final | 1 |
| item_lagrima | puzzle_lagrima_recoger | puzzle_exvoto_final | 1 |

**Total objetos: 10** (máximo simultáneo estimado: 8, bien por debajo del límite de 12).

**Todo objeto se usa al menos una vez:** ✓ (todos tienen al menos 1 puzzle que los requiere).

**Objetos bisagra** (usados en más de una rama): item_tarro_vacio, item_cuaderno_antiguo, item_libro_deudas.

---

## CERO DEAD-ENDS

El grafo no tiene dead-ends por diseño:
- Todas las ramas convergen en el exvoto final.
- Los objetos bisagra (cuaderno, libro) son reusables sin consumirse.
- El tarro se reutiliza: Tía Velas extrae la cera y devuelve el tarro vacío antes de la escena del sótano.
- Los fracasos en la Rama D (D1, D2) no eliminan opciones: siempre queda la opción de volver al hub o continuar intentando.
- El Práctico sigue disponible en el hub siempre que Reme quiera repasar las rutas.

---

## ESTRUCTURA HUB-AND-SPOKE — VERIFICACIÓN MANUAL

| Criterio | Cumplimiento |
|----------|-------------|
| Hub definido | ✓ puzzle_hub_explora (Tía Velas en la Venta) |
| 4 ramas | ✓ A (cera), B (hilo), C (nombre), D (lágrima) |
| 2 ramas cortas (≤2 pasos) | ✓ Rama A (2 pasos), Rama C (2 pasos) |
| 2 ramas largas (3-4 pasos) | ✓ Rama B (4 pasos), Rama D (4 pasos) |
| Solución lejos del problema en ≥3 pasos | ✓ Rama B: cuaderno (bancales) abre caja (telar) |
| 2+ ramas abiertas simultáneamente en el hub | ✓ Desde puzzle_hub_explora: portillo_info y sotano_info abren en paralelo |
| 1 puzzle de información | ✓ Rama B (cuaderno como llave documental) |
| 1 puzzle de observación social | ✓ Rama C (leer el sistema de deudas del Quincallero) |
| 1 puzzle de transformación de objeto | ✓ Rama A (fumigador transforma estado de colmena → cera) |
| 1 puzzle en capas con fracasos que informan | ✓ Rama D (3 capas: falla directa → falla cuaderno → éxito libro) |
| Cero puzzles verbales como cerradura | ✓ Ningún puzzle se resuelve diciendo la frase correcta |
| Cero dead-ends | ✓ Verificado por validate-graph.py |
| Cada objeto usado ≥1 vez | ✓ Ver tabla de economía |
| Max 12 objetos simultáneos | ✓ Máximo estimado: 8 |
| Cada fracaso tiene respuesta de personaje | ✓ Registrado en combos de script-es.json |

---

## NOTAS DE DISEÑO — CALIDAD

### El cuaderno antiguo como objeto bisagra

El cuaderno (encontrado en bancales) actúa como llave para la Rama B (abre la caja del telar) y como palanca parcial en la Rama D (revela nombres de deudores a Pura). Este uso doble refuerza la coherencia del mundo: el mismo objeto que conecta los embargos también avanza la confrontación. El jugador que encuentra el cuaderno en bancales no sabe aún que lo usará dos veces.

### El libro de deudas como objeto bisagra

Encontrado en el sótano (Rama C), el libro es también la llave de la Rama D. El jugador que lleva el libro para escribir el nombre descubre al mismo tiempo que tiene la herramienta para hacer llorar a Pura. Este "doble descubrimiento" es el diseño que hace a la Rama D parecer más corta de lo que es.

### El tarro como objeto de múltiple uso

El tarro viaja bancales → venta (con cera) → sótano (con lágrima). Su reutilización después de la entrega de la cera no necesita explicación en la UI: Tía Velas saca la cera y el tarro queda en el mandil de Reme. Naturalidad del mundo > eficiencia de inventario.

### La Rama D y la no-violencia narrativa

Doña Pura llora porque se enfrenta a su propia deuda, no porque se la engañe ni se la fuerce. El gag de recompensa refuerza que Reme tampoco esperaba ese resultado y que la victoria tiene un coste emocional. Este es el único momento del capítulo sin ironía de Reme.
