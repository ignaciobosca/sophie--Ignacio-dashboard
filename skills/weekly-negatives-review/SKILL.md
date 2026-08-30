---
name: weekly-negatives-review
description: >
  La red de seguridad SEMANAL del negative targeting automático. Por cliente, descubre las
  campañas "Loose Match - High Likelihood" (una por ASIN/producto) por PATRÓN de nombre
  (contiene "loose" Y "high likelihood", case-insensitive), lee TODOS los negativos aplicados
  ahí, y re-juzga cada uno contra el producto + el relevance_profile para detectar negativos
  que podrían estar bloqueando tráfico RELEVANTE. Arma una lista de "candidatos a archivar"
  con motivo y confianza, y la propone — NO archiva nada sin tu OK. Cuando confirmás, archiva
  esos negativos en AdLabs y los agrega a protected_relevant (learn) para que el push diario
  deje de re-negarlos. Escribe un snapshot de review a Supabase para auditoría. Trigger:
  "weekly negatives review para [Brand]", "revisá los negativos de [Brand]", "run
  weekly-negatives-review for [Brand]", o una Routine semanal que nombre una marca. NO
  identifica términos nuevos ni pushea negativos (eso es daily-negatives-supabase / -autopush).
---

# Weekly Negatives Review — red de seguridad del auto-negativizado

**Versión:** V1.0 (2026-08-30). Es el contrapeso del push diario automático
(`daily-negatives-autopush`). El diario aplica negativos solo, todos los días; **este skill,
una vez por semana, revisa lo acumulado** y caza los falsos positivos: un término que se negó
pero que en realidad puede traer tráfico relevante. Como des-negar reabre gasto, **este skill
PROPONE y vos confirmás** — nunca archiva por su cuenta.

**Respondé a Nacho en español.**

> **Por qué existe:** el push diario es agresivo por diseño (Nacho lo quiere automático). El
> filtro semántico + `protected_relevant` + exclusión de marca propia lo protegen, pero ningún
> filtro es perfecto. Un negativo mal puesto **no genera data** (bloquea el término), así que no
> se auto-corrige con métricas: hace falta una **re-lectura semántica** periódica. Esa es esta
> revisión. El OK de Nacho alimenta `protected_relevant`, así que cada corrección enseña al
> sistema y el mismo error no se repite.

---

## Cómo se define "candidato a archivar" (criterio del re-juicio)

Un negativo aplicado pasa a **candidato a archivar** si, re-juzgado hoy, cae en alguno de:
1. **Matchea `protected_relevant`** del perfil actual (igualdad o contención/wildcard) — se agregó
   una excepción después de que el término se negara. **Alta confianza.**
2. **Es marca propia o un `managed_asin`** del cliente que se negó por error. **Alta confianza.**
3. **El modelo ahora lo juzga Relevante** contra `product_context` (producto base + calificadores
   matchean) — el juicio original fue un falso positivo. **Media/alta según claridad.**
4. **Phrase root demasiado amplio:** una raíz negada en PHRASE que, además de lo irrelevante,
   captura frases claramente relevantes del producto (ej. negar `oil` en phrase cuando el producto
   ES un aceite). **Media confianza** — proponer bajar a EXACT del término puntual en vez de archivar
   la raíz entera, si aplica.
Un negativo que sigue siendo claramente irrelevante (competidor, off-category, DIY, atributo ajeno)
**se mantiene** y no aparece en la propuesta.

---

## Constants

```
Fuente de datos:  Supabase (config + perfil) · AdLabs (campañas + negativos aplicados)
  Config cliente:      public.clients (config JSONB) — brand_name, adlabs_team_id, adlabs_profile_id, managed_asins
  Perfil relevancia:   public.relevance_profiles (profile JSONB) — roots/competitors/protected_relevant
  Snapshot review:     public.dashboard_snapshots, tipo='negatives_review', fecha=HOY(ART) — lo escribe ESTE skill
Timezone:  America/Argentina/Buenos_Aires (ART) — anclar SIEMPRE a ART.
Loose Match: campañas cuyo nombre contiene "loose" Y "high likelihood" (case-insensitive).
             Hay UNA POR ASIN/producto (ej. Urban Veda: una loose-match por managed ASIN).
```

---

## Startup (siempre)
En paralelo:
1. AdLabs: `start_chat_session()` → `chat_session_id`; luego `read_resource(uri="adlabs://instructions", ...)`.
2. Supabase: leé el `config` del cliente (Step 1).

---

## Flujo (un cliente)

### Step 1 — Resolver cliente + contexto
Igual que `daily-negatives-supabase` Step 1: resolvé `requested_brand` contra `public.clients`
(exacto/case-insensitive/alias). `cfg = config`. Requeridos: `brand_name`, `adlabs_team_id`,
`adlabs_profile_id`, `managed_asins`. Multi-marketplace = 1 corrida por config.

Armá:
- `product_context` (marca, category, description desde `notes.client_overview.product_description` o
  `product_portfolio.structure`, ASINs con `name`) — idéntico a negative-targeting Step 1.
- `own_asins` (todos los `managed_asins`) y `line_of_asin` (ASIN → línea/parent).
- `protected_relevant` del perfil: `select profile->'protected_relevant' from public.relevance_profiles where brand='<brand_name>'`.

### Step 2 — Descubrir las campañas Loose Match - High Likelihood (por patrón, y CHEQUEAR)
No asumas un nombre fijo. Fetcheá campañas y quedate con las que **contienen `loose` Y `high likelihood`**:
```
get_entity_data(entity_type="campaign", team_id, profile_id, chat_session_id,
  filters=[ CAMPAIGN_STATE=ENABLED, DATE=<últimos 14 días>,
            {"key":"CAMPAIGN_NAME","conditions":[{"operator":"LIKE","values":["Loose"]}]} ])
```
`read` la reference y **filtrá en el modelo** las filas cuyo nombre (lower) contenga `loose` **y**
`high likelihood` (el filtro LIKE de arriba es un pre-corte; el AND de las dos palabras lo confirmás vos,
porque AdLabs matchea por substring simple). Guardá `loose_campaigns = [{campaign_id, campaign_name}]`.

- **CHEQUEO OBLIGATORIO (pedido de Nacho):** imprimí las campañas que encontró antes de seguir, p.ej.
  `Encontré 6 campañas Loose Match - High Likelihood en {brand}: [nombres].` Así ves si el patrón
  capturó lo correcto por cuenta (los nombres varían: "loose"/"loose match", pero siempre "loose" + "high likelihood").
- **Si 0 campañas:** avisá y ofrecé fallback: leer los negativos a **nivel cuenta** (todas las campañas
  ENABLED). No inventes campañas. Preguntá si querés el fallback o si el nombre es otro.
- Mapeá cada loose-campaign a su **producto/línea** por los ASINs que anuncia (fetch `advertised_product`
  con `CAMPAIGN_ID IN <esa campaña>` → ASIN → `line_of_asin`) o por el nombre de la campaña.

### Step 3 — Leer los negativos aplicados en esas campañas
Traé los negativos (keyword + product target) que viven en las `loose_campaigns`:
```
get_entity_data(entity_type="negative_keyword", team_id, profile_id, chat_session_id,
  filters=[ {"key":"CAMPAIGN_ID","conditions":[{"operator":"IN","values":<ref/ids de loose_campaigns>]}]},
            CAMPAIGN_STATE=ENABLED ])
```
> ⚠️ **Verificar la entidad al construir:** el nombre exacto de la entidad de negativos en AdLabs
> (`negative_keyword` / `negative_target` / `negative_targeting`) y sus columnas (`match_type`,
> `ad_group_id`, `state`, `keyword_text`/`expression`) hay que confirmarlos con
> `read_resource(uri="adlabs://instructions")` o el schema en la primera corrida real. Traé para cada
> negativo: `texto/expresión`, `match_type` (phrase/exact/product_target), `ad_group_id`, `campaign_id`,
> `state`, y un `id` para poder archivarlo en el Step 5. Para volumen alto, `download_data` a CSV.

Dedup por `(texto, match_type)` conservando en qué campañas/ad groups vive (se necesita para archivar).

### Step 4 — Re-juzgar cada negativo + armar la propuesta
Por cada negativo aplicado, corré el criterio de "candidato a archivar" (sección de arriba). Reusá el
motor de relevancia del Step 4 de `daily-negatives-supabase` (mismo criterio), pero **invertido**: acá
buscás los que HOY parecen Relevantes o protegidos, no los irrelevantes. Salida por negativo:
`keep` (sigue siendo buen negativo) o `archive_candidate` con `{reason, confidence: high|med, suggested_action: archive|downgrade_to_exact}`.

Armá `proposal = [{texto, match, kind, product/campaña, reason, confidence, action}]`, ordenada por
confianza desc. Si `proposal` está vacía → todo sano, reportá y saltá al Step 6 (snapshot de "sin cambios").

### Step 5 — Proponer → confirmar → archivar (NUNCA sin OK)
1. **Presentá la propuesta** clara: agrupada por producto, con motivo y confianza por término, y el conteo.
   Ejemplo:
   > **Revisión semanal {brand} — {fecha}. {N} negativos podrían estar bloqueando tráfico relevante:**
   > **Hair Growth Serum** · loose-match `HGS | Loose - High Likelihood`
   >  - `hair serum` (PHRASE) — ahora en protected_relevant · **alta** → archivar
   >  - `growth oil` (EXACT) — el modelo lo juzga relevante (producto ES un aceite de crecimiento) · media → archivar
   > ¿Archivo estos {N}? Podés decir "todos", "solo los de alta confianza", o listarme cuáles.
2. **Esperá el OK de Nacho.** Sin confirmación explícita **no se archiva nada.** ("todos" / "solo alta" /
   una sublista son confirmaciones válidas.)
3. **Al confirmar, archivá** los seleccionados en AdLabs. Mecánica (verificar en la 1ª corrida):
   ```
   update_entities(entity_type="negative_keyword", team_id, profile_id, chat_session_id,
     reference/ids=<los negativos seleccionados>, updates={"state":"ARCHIVED"})
   ```
   > Si AdLabs no expone archivar negativos vía `update_entities`, la alternativa es PAUSE del negativo o
   > darle a Nacho el link "View in AdLabs" de esos negativos para archivarlos en la UI (equivale a un
   > dry-run con acción manual). Confirmá el mecanismo real al construir y dejá registrado cuál se usa.
4. **Learn (enseñar al sistema):** por cada negativo archivado, agregalo a `protected_relevant` del perfil
   para que `daily-negatives-autopush` no lo vuelva a negar. Reusá `daily-negatives-supabase` MODE=learn
   (upsert a `public.relevance_profiles`, con chequeo de conflicto: si el término está en roots/competitors,
   removerlo — gana la excepción — y loguearlo en `change_log`). Confirmá el learn en el resumen.

### Step 6 — Snapshot de review a Supabase (auditoría)
`datos` schema `negatives-review-v1`:
```json
{ "schema":"negatives-review-v1", "generated_at_iso":"<ISO ART>", "brand":"<brand_name>", "date_iso":"<HOY-ART>",
  "loose_campaigns":[{"campaign_id":"...","campaign_name":"...","product":"..."}],
  "reviewed_count":N, "proposed_count":N, "archived_count":N,
  "proposal":[{"texto":"...","match":"...","kind":"...","product":"...","reason":"...","confidence":"high|med","action":"archive|downgrade","status":"archived|declined|pending"}],
  "learned":[{"term":"...","reason":"..."}] }
```
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives_review', '<HOY-ART>', $rev$<datos>$rev$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
Confirmá: `Revisión semanal {brand}: {reviewed} negativos revisados en {C} campañas loose-match, {proposed} propuestos, {archived} archivados, {learned} agregados a protected_relevant.`

---

## Scheduling (Routine semanal — crear aparte)
- Una Routine **semanal** por cliente activo (ej. lunes a la mañana ART), prompt
  `Run weekly-negatives-review for {brand_name}`. Connectors: **Supabase + Adlabs**.
- Como el Step 5 **requiere tu OK**, esta Routine tiene sentido corriéndola en una sesión donde puedas
  responder (o dejando la propuesta en el snapshot/dashboard y confirmando vos después). Si se corre
  desatendida: llega hasta el Step 4–5, escribe la propuesta al snapshot con `status:"pending"`, y NO
  archiva — vos confirmás luego con "archivá la revisión de {brand}".
- Multi-marketplace = 1 Routine por config.

---

## Edge cases
| Situación | Comportamiento |
|---|---|
| 0 campañas loose-match encontradas | Avisar; ofrecer fallback a negativos a nivel cuenta. No inventar campañas. |
| Patrón captura campañas de más (falsos loose) | El CHEQUEO del Step 2 lo muestra; Nacho ajusta el patrón o excluye. |
| Propuesta vacía (todo sano) | Snapshot "sin cambios", nada que archivar. Reportar limpio. |
| Sin OK de Nacho | NO archivar. Guardar propuesta `status:"pending"` para confirmar después. |
| AdLabs no permite archivar vía MCP | Fallback: pause, o link "View in AdLabs" para archivar en la UI. Registrar el mecanismo usado. |
| Negativo archivado | Agregar a protected_relevant (learn) para que el autopush no lo re-negue. |
| Entidad/columnas de negativos inciertas | Confirmar con adlabs://instructions o el schema en la 1ª corrida. |
| Multi-marketplace | 1 corrida por config; brand distingue US/CA. |
