# HANDOFF — ARTE · Cap. 1 "La Cañada Cerrada"

**Estado:** Producción completa — listo para integración en motor  
**Fecha:** 2026-08-09  
**Director de arte:** atajo-m3  
**Misión:** atajo-m3-arte

---

## Artefactos entregados

| Fichero | Tipo | Descripción |
|---------|------|-------------|
| `art/palette.js` | CommonJS | Paleta global 24 colores, sin #000/#fff puros |
| `art/sprites.js` | CommonJS | Módulo sprites del cast completo (6 personajes) |
| `art/scenes/escena1.js` | CommonJS | La Cañada Cerrada — camino rocoso blue hour |
| `art/scenes/escena2.js` | CommonJS | Venta de Tía Velas — interior cálido con colmenas |
| `art/scenes/escena3.js` | CommonJS | Bancales de la Colmena — exterior atardecer rosado |
| `art/scenes/escena4.js` | CommonJS | Sala del Telar — taller con telar y lacres |
| `art/scenes/escena5.js` | CommonJS | Sótano del Registro — archivo subterráneo azul |
| `docs/30-arte/previews/escena1-canada-cerrada.png` | PNG 180×320 | Preview renderizado |
| `docs/30-arte/previews/escena2-venta-tiavelas.png` | PNG 180×320 | Preview renderizado |
| `docs/30-arte/previews/escena3-bancales-colmena.png` | PNG 180×320 | Preview renderizado |
| `docs/30-arte/previews/escena4-sala-telar.png` | PNG 180×320 | Preview renderizado |
| `docs/30-arte/previews/escena5-sotano-registro.png` | PNG 180×320 | Preview renderizado |
| `docs/30-arte/BIBLIA-VISUAL.md` | Markdown | Biblia visual completa |

---

## Paleta Global — 24 Colores

Sin `#000000` ni `#ffffff` puros. Importar con `require('./palette.js')`.

| Nombre | Hex | Rol semántico | Firma |
|--------|-----|---------------|-------|
| `SOMBRA_PROFUNDA` | `#1a1225` | Fondos nocturnos, sombras densas | — |
| `PIEDRA_OSCURA` | `#2d2b3d` | Muros de ladera, interiores, siluetas | — |
| `TIERRA_SECA` | `#5c4a32` | Suelo del camino, sombras de personaje | — |
| `BARRO_TOSTADO` | `#8b6a3e` | Paredes de adobe, caminos a medio sol | — |
| `PAJA_VIEJA` | `#c4a265` | Piel de personajes, paredes iluminadas | — |
| `PIEDRA_CALIZA` | `#e8d9b0` | Mojones, paredes encaladas, papel | — |
| `CIELO_TORMENTA` | `#2b3a6b` | Cielo alto blue hour, sótano | — |
| `AZUL_HORA` | `#4a6fa5` | Cielo medio, sombras azuladas | — |
| `LAVANDA_TARDE` | `#8b7eb8` | Horizonte transición, humo frío | — |
| `PONIENTE_ROSA` | `#d4708a` | Horizonte atardecer, reflejos | — |
| `PONIENTE_NARANJA` | `#e8864a` | Banda sol bajo, barro en luz | — |
| `SOL_BAJO` | `#f2c46d` | Muela, miel, destellos metálicos | — |
| `OLIVO_OSCURO` | `#3d5c2e` | Árboles lejanos, matorral fondo | — |
| `SECANO_VERDE` | `#6b8c45` | Hierba seca, troncos, matorral medio | — |
| `HIERBA_POLVO` | `#9aab6e` | Césped ralo, cardos, primer plano | — |
| `AZUL_MANDIL` | `#2d5a8e` | **Firma REME** — blusa/ropa de trabajo | REME |
| `NEGRO_SASTRE` | `#1e2433` | **Firma DOÑA PURA** — traje chaqueta | PURA |
| `CASTANO_TURBO` | `#8b6042` | **Firma TURBO** — pelaje galgo castaño | TURBO |
| `CERA_VELAS` | `#e8c97e` | **Firma TÍA VELAS** — mandil y cera | VELAS |
| `TERGAL_MARRON` | `#7a5c3a` | **Firma MELQUÍADES** — traje tergal | MELQUÍADES |
| `GRIS_JUBILADO` | `#7a7d8a` | **Firma EL PRÁCTICO** — ropa faena | PRÁCTICO |
| `LACRE_ESCARLATA` | `#c4202a` | **Hotspot crítico** — lacres Pura | PURA (acento) |
| `MIEL_AMBAR` | `#d4924a` | Miel, panal, velas encendidas | VELAS (acento) |
| `HUMO_AZUL` | `#7b8fad` | Humo ambiental, vapor, niebla | — |

---

## API de Sprites

```javascript
const { drawReme, drawTurbo, drawPura, drawTiaVelas, drawMelquiades, drawPractico } = require('./art/sprites.js');

// Uso: draw*(ctx, x, y, frame, facing)
// frame: 0=idle, 1=walk1, 2=walk2
// facing: 'right' | 'left'
drawReme(ctx, 70, 240, 0, 'right');
```

| Función | Personaje | Color firma |
|---------|-----------|-------------|
| `drawReme(ctx,x,y,f,dir)` | Reme (protagonista) | AZUL_MANDIL |
| `drawTurbo(ctx,x,y,f,dir)` | Turbo (galgo) | CASTANO_TURBO |
| `drawPura(ctx,x,y,f,dir)` | Doña Pura | NEGRO_SASTRE |
| `drawTiaVelas(ctx,x,y,f,dir)` | Tía Velas | CERA_VELAS |
| `drawMelquiades(ctx,x,y,f,dir)` | Melquíades | TERGAL_MARRON |
| `drawPractico(ctx,x,y,f,dir)` | El Práctico | GRIS_JUBILADO |

---

## API de Escenas

```javascript
const { drawEscena1 } = require('./art/scenes/escena1.js');
// Uso: drawEscenaX(ctx, t)
// t = Date.now() para animación en tiempo real
drawEscena1(ctx, Date.now());
```

### Elementos de vida por escena

| Escena | Vida 1 | Vida 2 |
|--------|--------|--------|
| escena1 | Pájaros migrando (frame-based) | Polvo de camino (alpha oscilante) |
| escena2 | Velas titilando (flicker sinusoidal) | Abeja saliendo de colmena |
| escena3 | Hojas meciéndose (Math.sin) | Humo de ahumador (fade-out alpha) |
| escena4 | Hilos del telar oscilando (sway) | Polilla volando hacia vela |
| escena5 | Motes de polvo en rayo de luz | Cucaracha cruzando el suelo |

---

## Reglas de Composición

1. **3 planos obligatorios**: cielo/fondo · plano medio · plano jugable
2. **Hotspots con contraste**: `LACRE_ESCARLATA` sobre fondo oscuro (escenas 4 y 5)
3. **Silueta por color firma**: cada personaje reconocible por un solo bloque de color a 28px
4. **Sin negro/blanco puros**: usar `SOMBRA_PROFUNDA` en lugar de `#000`, `PIEDRA_CALIZA` en lugar de `#fff`
5. **Animación barata**: solo `Math.sin(t)`, `Math.floor(t/ms)%n`, `ctx.globalAlpha` — sin requestAnimationFrame interno

---

## Notas de Integración para el Motor

- Todos los módulos son **CommonJS** (`require()`), compatibles con Node y bundlers sin config especial
- Las funciones de escena son **puras**: sin estado, sin efectos secundarios, redibujar cada frame
- `t` debe ser `Date.now()` o el timestamp del gameloop en ms
- Los PNGs de preview son 180×320 RGBA — el motor debe usar el mismo lienzo
- `LACRE_ESCARLATA` (`#c4202a`) es el color de hotspot principal — el motor puede filtrar píxeles de este color para detectar áreas clicables

---

## Próximos pasos (Motor / Cap. 2)

1. Integrar `drawEscenaX(ctx, t)` en el gameloop del motor
2. Conectar `drawReme(ctx, x, y, Math.floor(t/150)%3, dir)` al estado de movimiento
3. Los lacres (escenas 4 y 5) son objetos interactuables — definir hitbox sobre `LACRE_ESCARLATA`
4. Cap. 2 necesitará nuevas escenas — misma paleta, mismo API
