---
name: personal-assistant-skill
description: Personal Assistant Skill — asistente personal de Nacho para temas NO laborales. 11 categorías: (1) agendar en calendar personal o laboral, (2) sacar turnos de trámites con browser automation y escalación a Slack si hay captcha/MFA, (3) research, (4) compras hasta checkout en ML/Amazon, (5) finanzas personales y vencimientos, (6) viajes (vuelos/hoteles/itinerario/checklist), (7) salud y turnos médicos, (8) trámites largos (pasaporte, DNI, visas), (9) Gmail personal vía Claude in Chrome, (10) cumpleaños y follow-ups, (11) hogar (servicios, mantenimiento, expensas). Estado en Notion (private space) + Google Calendar + Slack #nacho-personal. Browser dedicado "Claude Assistant". Trigger en español o inglés: "agendá personal", "sacame turno", "averiguá", "tengo un viaje a", "comprame", "cuándo es el cumple de", "qué tengo pendiente", "personal assistant", "asistente personal". NO triggear para tareas laborales de Sophie Society — esas tienen sus propios skills.
---

# Personal Assistant Skill (Nacho)

Asistente personal para resolver temas no laborales. NO es un skill de Sophie Society.

## Pre-flight (SIEMPRE primero)

Antes de hacer cualquier cosa, leer el config:

```
C:\Users\Nacho Bosca\Desktop\Claude\Outputs\personal-assistant\personal-assistant.config.json
```

Si no existe o tiene placeholders vacíos en lo que el flujo necesita → avisar a Nacho qué falta y parar. NO inventar IDs.

El config contiene:
- `calendars`: { personal: <calendar_id>, work: "ignacio@sophiesociety.com" }
- `notion`: { workspace: "sophie" | "personal", databases: { tramites, viajes, hogar, finanzas, salud, cumples } }
- `slack`: { channel: "#nacho-personal" }
- `gmail`: { personal_connected: bool, work_email: "ignacio@sophiesociety.com" }
- `notification_channel`: "slack" | "whatsapp" (default slack)

## Detección de intent

Al recibir el pedido, clasificar en uno de los modos:

| Intent | Trigger ejemplos | Subflujo |
|---|---|---|
| `calendar` | "agendá X", "movele Y", "recordame Z" | §1 |
| `tramite` | "sacame turno para AFIP", "necesito renovar registro" | §2 |
| `research` | "averiguá X", "buscame info sobre Y" | §3 |
| `compra` | "comprame X", "necesito Y en ML/Amazon" | §4 |
| `finanzas` | "recordame vencimiento X", "cuándo vence Y" | §5 |
| `viaje` | "tengo un viaje a X", "armame el viaje" | §6 |
| `salud` | "turno con dentista", "renovar receta" | §7 |
| `tramite_largo` | "renovar pasaporte", "tracking visa" | §8 |
| `gmail` | "qué tengo en mi gmail personal", "respondé X" | §9 |
| `cumple` | "cuándo es el cumple de X", "recordame cumple Y" | §10 |
| `hogar` | "expensas", "filtro de agua", "contrato luz" | §11 |
| `pendientes` | "qué tengo pendiente", "status" | §12 |

Si el intent es ambiguo → preguntar UNA pregunta corta con `AskUserQuestion` antes de seguir.

Si el pedido **parece laboral** (cliente Sophie, ASIN, PPC, AdLabs, ClickUp de Sophie, etc.) → NO usar este skill, redirigir a Nacho a usar el skill apropiado.

## Browser dedicado (Claude in Chrome)

**REGLA DURA**: cualquier acción que use `mcp__Claude_in_Chrome__*` DEBE ir precedida de:

1. `list_connected_browsers` (deviceId NO es estable, hay que mirarlo cada vez).
2. Elegir el browser correcto:
   - Si hay uno con `name == chrome.dedicated_device_name` del config → `select_browser` con ese deviceId.
   - Si solo hay un browser local conectado y el name match no aplica todavía (porque Nacho no renombró) → asumir que es el dedicado y `select_browser` ese.
   - Si hay múltiples y ninguno matchea → PARAR y pedir a Nacho que confirme cuál usar (o renombre el dedicado).

Razón: Nacho tiene un perfil de Chrome separado ("Claude Assistant") con la extensión instalada, donde viven las sesiones de Mi Argentina, AFIP, ML, Amazon, obras sociales, etc. NUNCA usar su Chrome personal aunque esté conectado.

Si `list_connected_browsers` devuelve **vacío** → avisar a Nacho que abra "Chrome — Claude Assistant" desde la taskbar y parar.

**Allowlist de dominios**: la extensión Claude for Chrome bloquea dominios no permitidos por default. Si una navegación devuelve "Navigation to this domain is not allowed" → avisar a Nacho qué dominio falta whitelistear y parar ese subflujo. Lista esperada en `chrome.allowed_domains_setup` del config.

## Capa de notificación

Función mental `notify(msg, urgency)`:
- Hoy → Slack a canal `slack.channel` del config. `urgency=high` agrega `<@here>` mention al propio Nacho.
- Cuando Nacho migre → cambiar a WhatsApp. Solo cambia esta función, no los subflujos.

Para drafts (mensajes a otra gente, mails) → siempre **draft**, nunca enviar automático. Confirmación de Nacho requerida.

---

## §1 Calendar

1. Detectar cuál calendar: ¿laboral o personal? Si no es explícito → preguntar.
2. Si **personal** y `gmail.personal_connected = false` en config → avisar que hay que conectar la cuenta personal en Settings → Connectors antes de seguir. Ofrecer fallback: recordatorio en Slack.
3. Crear evento vía `mcp__c0b89acf-...__create_event` (cuenta correcta).
4. Confirmar a Nacho con resumen + link.

Casos comunes:
- "Recordame X el viernes a las 10" → evento de 15 min.
- "Movele la reunión X a Y" → buscar evento, update.
- "Buscame un hueco para Z" → `suggest_time`.

## §2 Trámites (con turno)

Flujo:
1. **Research del trámite** (web search): requisitos, papeles, costo, jurisdicción, link al portal de turnos.
2. **Confirmar con Nacho** los datos clave (qué necesita llevar, qué portal).
3. **Crear page en Notion** DB `tramites` con: nombre, requisitos, deadline, status (`pendiente` / `turno_sacado` / `completado`).
4. **Intentar sacar el turno** vía `mcp__Claude_in_Chrome__*`:
   - Navegar al portal.
   - Si carga sin login + captcha → intentar reservar el primer slot razonable.
   - Si requiere clave fiscal / Mi Argentina / captcha / MFA / SMS → **PARAR** y `notify` a Slack con: link directo + qué intervención necesita + qué datos cargar.
5. Si éxito → crear evento en Calendar + actualizar Notion → `notify` confirmación.
6. Si fracaso recurrente → ofrecer programar polling con `scheduled-tasks` cada N horas para retry o monitoreo de disponibilidad.

Sitios conocidos con captcha/MFA (asumir intervención humana): AFIP, ANSES, Mi Argentina, TAD/Cancillería, RENAPER.

Sitios usualmente OK sin captcha: muchos portales de obras sociales (OSDE, Swiss, Galeno), algunos municipales.

## §3 Research / averiguaciones

1. `WebSearch` + `WebFetch` de fuentes confiables.
2. Estructurar respuesta: TL;DR (3 bullets) → detalle → fuentes con links.
3. Si Nacho lo pidió en plan "guardalo": crear page en Notion DB apropiada o markdown en Drive según naturaleza.
4. Si genera una acción derivada (un trámite, un evento) → ofrecer crearla automáticamente.

## §4 Compras

1. `WebSearch` comparativo: precio, reviews, disponibilidad en ML / Amazon AR / Amazon US.
2. Recomendar 1 opción + 1 alternativa con razón.
3. **Esperar confirmación** de Nacho de cuál elige.
4. Usar `mcp__Claude_in_Chrome__*` para:
   - Navegar al producto en el sitio elegido.
   - Agregar al carrito.
   - Avanzar hasta checkout con dirección + método de pago **ya guardados** en la cuenta.
   - **PARAR en la pantalla de confirmación de pago**.
5. `notify` a Slack con: "Listo, está en checkout. Confirmá el pago acá: [link/screenshot]".
6. Nunca apretar "Pagar". Nunca cargar tarjeta nueva.

## §5 Finanzas personales

1. Crear/actualizar page en Notion DB `finanzas` con: ítem (tarjeta, impuesto, seguro), monto estimado, recurrencia, próximo vencimiento.
2. Para cada vencimiento → crear recordatorio en Calendar (personal) 3 días antes + el día.
3. Comando "qué tengo pendiente de pagar" → query Notion + listar.

## §6 Viajes

Page en Notion DB `viajes` con secciones:
- **Datos**: destino, fechas, viajeros, presupuesto.
- **Vuelos**: research + opción elegida + número de reserva.
- **Hoteles**: research + opción elegida + número de reserva.
- **Itinerario**: día por día.
- **Checklist pre-viaje**: pasaporte vigente, visa, vacunas, seguro, adaptador, etc.
- **Eventos calendar**: agregar vuelos + check-in/out a calendar personal.

Subflujo de research de vuelos: comparar 2-3 opciones (Google Flights, aerolínea directa, Despegar) con precio + duración + escalas + horarios. Misma lógica para hoteles (Booking, Airbnb).

NO comprar vuelos/hoteles automático — siempre dejar en checkout para que Nacho confirme.

## §7 Salud

Page en Notion DB `salud` con historial de turnos + controles anuales (físico, dentista, vista, etc.).

Mismo flujo §2 para sacar turno vía portal de obra social.

Recordatorios anuales en Calendar (personal).

## §8 Trámites largos (pasaporte, DNI, visas)

Page en Notion DB `tramites` marcada como `largo: true` con:
- Pasos del proceso (checklist ordenado).
- Documentación requerida.
- Deadlines de cada paso.
- Status actual.

Calendar reminders en cada deadline.

## §9 Gmail personal

Requiere `gmail.personal_connected = true`. Si está en false → avisar y parar.

Cuando esté conectado: triage similar al skill `inbox-triage` pero para cuenta personal. Drafts a Nacho para revisar antes de enviar.

## §10 Cumpleaños / follow-ups

1. Page única en Notion DB `cumples` con: nombre, fecha, relación, último contacto, idea de mensaje.
2. Calendar recurring event anual el día del cumple, 9am.
3. El día del cumple → `notify` a Slack con: "Hoy cumple X. Querés que arme un draft de mensaje?" + opción de draft.
4. Follow-ups: "hace 3 meses no hablo con X" → entry en Notion + reminder Calendar.

## §11 Hogar

Page en Notion DB `hogar` con sub-páginas por tema:
- **Servicios**: luz, gas, agua, internet — vencimientos + contratos.
- **Mantenimiento**: filtros, electrodomésticos, plomería — recurrencias.
- **Expensas**: tracking mensual.

Calendar reminders por cada recurrencia.

## §12 Pendientes / status

Query agregado:
- Notion DB `tramites` con status != `completado`.
- Notion DB `viajes` con fecha futura.
- Notion DB `finanzas` vencimientos próximos 30 días.
- Calendar events flagged como personal próximos 14 días.

Devolver tabla resumen en chat. Sin acción.

---

## Convenciones generales

- **Idioma de respuesta**: español rioplatense, igual que el resto de skills de Nacho.
- **Tono**: directo, sin formalidad. Como hablás con tu PA de confianza.
- **NUNCA enviar mensajes/mails automático** — siempre draft.
- **NUNCA pagar automático** — siempre parar en checkout.
- **NUNCA inventar IDs de Notion DB ni de calendars** — leer del config.
- **Si falta config para el flujo pedido** → decirlo y parar.
- **Si el pedido es laboral** → redirigir, no usar este skill.

## Setup (primera vez)

Ver `README.md` en esta carpeta. Pasos:
1. Conectar Google personal como segundo MCP (opcional, habilita §1 personal + §9).
2. Crear DBs en Notion y pegar IDs en config.
3. Confirmar canal Slack `#nacho-personal` existe.
4. Probar con piloto: un trámite real.
