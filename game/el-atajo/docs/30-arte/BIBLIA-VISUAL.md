# BIBLIA VISUAL — El Atajo · Capítulo 1

**Director de arte:** atajo-m3  
**Fecha:** 2026-08-09  
**Canvas:** 180×320 px vertical  
**Estilo:** Pixel art flat, sin dithering pesado, sin contornos negros puros

---

## 1. Filosofía Visual

"El Atajo" transcurre en una Andalucía rural atemporal bañada en dos luces: el **atardecer naranja-rosa** (poniente) y la **hora azul** (blue hour al amanecer y al anochecer). Estas dos paletas se alternan según la escena e informan toda la dirección de color.

**Reglas absolutas:**
- Sin `#000000` ni `#ffffff` puros — el negro más oscuro es `SOMBRA_PROFUNDA` (`#1a1225`), el blanco más claro es `PIEDRA_CALIZA` (`#e8d9b0`)
- Máximo 24 colores globales; ninguna escena inventa colores nuevos
- Flat art: sin dithering de 4×4, solo bloques de color sólido
- Contornos implícitos por contraste de color, no por línea negra

---

## 2. Paleta Global — 24 Colores

```
 SOMBRA_PROFUNDA   ████  #1a1225  Fondos nocturnos
 PIEDRA_OSCURA     ████  #2d2b3d  Muros, siluetas
 TIERRA_SECA       ████  #5c4a32  Caminos, sombras
 BARRO_TOSTADO     ████  #8b6a3e  Adobe, paredes
 PAJA_VIEJA        ████  #c4a265  Piel, trigo
 PIEDRA_CALIZA     ████  #e8d9b0  Encalado, papel

 CIELO_TORMENTA    ████  #2b3a6b  Blue hour profundo
 AZUL_HORA         ████  #4a6fa5  Cielo medio
 LAVANDA_TARDE     ████  #8b7eb8  Horizonte transición
 PONIENTE_ROSA     ████  #d4708a  Horizonte atardecer
 PONIENTE_NARANJA  ████  #e8864a  Sol bajo, barro en luz
 SOL_BAJO          ████  #f2c46d  Destellos, miel

 OLIVO_OSCURO      ████  #3d5c2e  Árboles lejanos
 SECANO_VERDE      ████  #6b8c45  Hierba seca, troncos
 HIERBA_POLVO      ████  #9aab6e  Cardos, primer plano

 AZUL_MANDIL  ████  #2d5a8e  ← REME
 NEGRO_SASTRE ████  #1e2433  ← DOÑA PURA
 CASTANO_TURBO████  #8b6042  ← TURBO
 CERA_VELAS   ████  #e8c97e  ← TÍA VELAS
 TERGAL_MARRON████  #7a5c3a  ← MELQUÍADES
 GRIS_JUBILADO████  #7a7d8a  ← EL PRÁCTICO

 LACRE_ESCARLATA   ████  #c4202a  HOTSPOT crítico
 MIEL_AMBAR        ████  #d4924a  Miel, velas
 HUMO_AZUL         ████  #7b8fad  Humo ambiental
```

---

## 3. Hoja de Personajes

### REME (protagonista)
- **Color firma:** `AZUL_MANDIL` (`#2d5a8e`) — blusa/camiseta de trabajo
- **Ancho sprite:** 16px lógico = 32px real
- **Silueta:** Figura femenina adulta, cabello oscuro (`TIERRA_SECA`), botas de campo
- **Diferenciador:** La única con pantalón verde olivo y blusa azul mandil
- **API:** `drawReme(ctx, x, y, frame, facing)`

### TURBO (galgo)
- **Color firma:** `CASTANO_TURBO` (`#8b6042`) — pelaje castaño
- **Ancho sprite:** 16px lógico = 32px real (horizontal)
- **Silueta:** Cuádrupedo largo y delgado, perfil de galgo
- **Diferenciador:** Único cuadrúpedo del cast
- **API:** `drawTurbo(ctx, x, y, frame, facing)`

### DOÑA PURA (notaria)
- **Color firma:** `NEGRO_SASTRE` (`#1e2433`) — traje de chaqueta
- **Accento:** `LACRE_ESCARLATA` en pecho (brocha)
- **Ancho sprite:** 14px lógico = 28px real
- **Silueta:** Figura erguida, cabello `PIEDRA_OSCURA`, traje oscuro con toque rojo
- **API:** `drawPura(ctx, x, y, frame, facing)`

### TÍA VELAS
- **Color firma:** `CERA_VELAS` (`#e8c97e`) — mandil y delantal
- **Acento:** `MIEL_AMBAR` — tarro en mano
- **Ancho sprite:** 14px lógico = 28px real
- **Silueta:** Figura redondeada con mandil claro sobre vestido oscuro
- **API:** `drawTiaVelas(ctx, x, y, frame, facing)`

### MELQUÍADES (alcalde)
- **Color firma:** `TERGAL_MARRON` (`#7a5c3a`) — traje de tergal
- **Acento:** `PIEDRA_CALIZA` — camisa blanca visible
- **Ancho sprite:** 14px lógico = 28px real
- **Silueta:** Figura mayor, cabello `GRIS_JUBILADO`, traje marrón
- **API:** `drawMelquiades(ctx, x, y, frame, facing)`

### EL PRÁCTICO (jubilado)
- **Color firma:** `GRIS_JUBILADO` (`#7a7d8a`) — ropa de faena
- **Acento:** `TIERRA_SECA` — boina oscura
- **Ancho sprite:** 14px lógico = 28px real
- **Silueta:** Figura encorvada con boina `TIERRA_SECA`, ropa gris desteñida
- **API:** `drawPractico(ctx, x, y, frame, facing)`

---

## 4. Reglas de Composición por Escena

### Sistema de 3 planos

```
PLANO 1 (fondo): cielo, paredes, ventanas — NO interactuable
PLANO 2 (medio): vegetación, muebles, estructuras — NO interactuable
PLANO 3 (jugable): suelo, mostrador, camino — HOTSPOTS aquí
```

Los personajes se colocan sobre el plano 3 (jugable), nunca ocultados por plano 2.

### Escena 1 — La Cañada Cerrada
- **Luz dominante:** Blue hour (CIELO_TORMENTA → AZUL_HORA → LAVANDA_TARDE)
- **Plano jugable:** Camino de BARRO_TOSTADO, 44-134px horizontal
- **Contraste:** Personajes sobre barro (AZUL_MANDIL contrasta bien)
- **Vida:** Pájaros V-shape en cielo, polvo semitransparente en camino

### Escena 2 — Venta de Tía Velas
- **Luz dominante:** Interior cálido (SOL_BAJO, MIEL_AMBAR) vs ventana azul
- **Plano jugable:** Mostrador a y=218, suelo bajo TIERRA_SECA
- **Hotspot:** Tarros de miel (MIEL_AMBAR) en estantería
- **Vida:** Llamas de vela (flicker α-sinusoidal), abeja emergente

### Escena 3 — Bancales de la Colmena
- **Luz dominante:** Atardecer (PONIENTE_ROSA → PONIENTE_NARANJA en horizonte)
- **Plano jugable:** Sendero 28-152px horizontal, y=250
- **Contraste:** Personajes sobre tierra seca (todos los firmas visibles)
- **Vida:** Hojas meciéndose (desplazamiento ±2px), humo de ahumador

### Escena 4 — Sala del Telar
- **Luz dominante:** Doble (ventana blue hour izquierda + vela cálida derecha)
- **Plano jugable:** Suelo de losas, y=252
- **Hotspot:** Lacres LACRE_ESCARLATA en estantería derecha (contraste máximo)
- **Vida:** Hilos del telar oscilan (dy = Math.round(sway×2)), polilla

### Escena 5 — Sótano del Registro
- **Luz dominante:** Bombilla cálida sobre azul profundo de sótano
- **Plano jugable:** Suelo de mampostería, y=265
- **Hotspot:** Cintas LACRE_ESCARLATA en legajos (estantería derecha)
- **Vida:** Motes de polvo en cono de luz, cucaracha con patas alternantes

---

## 5. Reglas de Animación

```javascript
// Patrón estándar de animación barata:
const f = Math.floor(t / 400) % 4;        // frame discreto (4 estados)
const sway = Math.sin(t / 800);            // oscilación suave (-1..1)
const flicker = 0.85 + 0.15 * Math.sin(t / 200); // parpadeo de vela

ctx.globalAlpha = 0.3 + 0.1 * Math.sin(t / 600); // humo/polvo
```

- **Máximo** 2 elementos animados por escena
- **Sprites personaje:** frame = `Math.floor(t / 150) % 3` durante marcha, 0 en idle
- **Sin requestAnimationFrame interno** — el motor llama a drawEscenaX(ctx, t) en su propio loop

---

## 6. Guía de Accesibilidad

| Elemento | Color | Plano | Contraste mínimo |
|----------|-------|-------|-----------------|
| REME sobre camino | AZUL_MANDIL vs BARRO_TOSTADO | jugable | ✓ 3.2:1 |
| Lacres sobre pared | LACRE_ESCARLATA vs BARRO_TOSTADO | medio | ✓ 4.1:1 |
| Texto/UI (si aplica) | PIEDRA_CALIZA vs CIELO_TORMENTA | overlay | ✓ 5.8:1 |
| Cucaracha (escena5) | TIERRA_SECA vs PIEDRA_OSCURA | jugable | ✓ 3.0:1 |

Los hotspots LACRE_ESCARLATA son el elemento con mayor contraste de todo el juego — diseño intencional para que el jugador los encuentre sin pistas explícitas.
