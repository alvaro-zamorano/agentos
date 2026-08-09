# EL ATAJO — PROTOCOLO DE ESTUDIO
### Coherencia entre agentes y roles

---

## ANTES DE TRABAJAR

Todo rol que entre al workspace debe hacer, en orden:

1. **Leer `docs/00-direccion/GREENLIGHT.md`** — dirección creativa fundacional. Si algo contradice este documento, la dirección creativa tiene precedencia.
2. **Leer todos los `docs/**/HANDOFF.md` existentes** — estado actualizado de cada área. Son la memoria viva del proyecto.
3. **Leer `docs/CHANGE-REQUESTS.md`** si existe — cambios pendientes que pueden afectar tu área.

Solo después de estos tres pasos se puede comenzar a trabajar.

---

## AL TERMINAR

Cada rol escribe su `HANDOFF.md` en su directorio (`docs/<area>/HANDOFF.md`) con:

```
# HANDOFF — <ROL> — <FECHA>

## Qué hice
- Lista concreta de lo producido o modificado

## Decisiones tomadas
- Cada decisión no obvia, con su razonamiento

## Estado actual
- Qué está completo, qué está en progreso, qué falta

## Qué necesito de otros roles
- Peticiones concretas con destinatario claro (ej: "M2-Arte: necesito sprite de Reme en bicicleta, 16×32 px")

## Qué no tocar
- Áreas o decisiones que no deben modificarse sin consulta
```

---

## CAMBIOS QUE AFECTAN A OTROS ROLES

Si una decisión tuya cambia algo que otro rol ya ha trabajado o va a trabajar:

1. **NO modifiques el trabajo del otro rol directamente.**
2. Escribe la petición en `docs/CHANGE-REQUESTS.md` con este formato:

```
## [FECHA] [ROL-ORIGEN] → [ROL-DESTINO]: [Título breve]

**Motivo:** Por qué es necesario el cambio.
**Cambio solicitado:** Qué debe cambiar exactamente.
**Impacto si no se hace:** Qué rompe o queda incoherente.
**Urgencia:** [BLOQUEANTE | ALTA | NORMAL | BAJA]
```

El rol destinatario lee el CHANGE-REQUESTS en su próxima entrada al workspace y decide si acepta, negocia o escala a dirección (M0).

---

## REGLAS DE ORO

| Regla | Descripción |
|-------|-------------|
| **LEER ANTES** | Ningún rol modifica sin haber leído el GREENLIGHT y los HANDOFF existentes |
| **HANDOFF AL SALIR** | Sin HANDOFF escrito, el trabajo no está terminado |
| **NO BORRAR** | Ningún rol borra trabajo de otro. Se enmienda vía change request |
| **GREENLIGHT manda** | Ante conflicto entre roles, el GREENLIGHT.md tiene la última palabra |
| **M0 es árbitro** | Si el conflicto no se resuelve con el GREENLIGHT, escala a dirección (rol M0) |

---

## MAPA DE ROLES

| Rol | Área | Directorio |
|-----|------|-----------|
| M0 | Dirección creativa | `docs/00-direccion/` |
| M1 | Guion y narrativa | `docs/01-guion/` |
| M2 | Arte y assets | `docs/02-arte/` |
| M3 | Motor y código | `docs/03-motor/` |
| M4 | Diseño de niveles | `docs/04-niveles/` |
| M5 | QA y balance | `docs/05-qa/` |

---

## WORKSPACE COMPARTIDO

Todas las rutas son relativas a `./el-atajo/`. Este directorio es el espacio compartido de todas las misiones `atajo-m*`. Ningún rol trabaja fuera de él.

---

*Versión: v0 · Fecha: 2026-08-09 · Dirección: M0*
