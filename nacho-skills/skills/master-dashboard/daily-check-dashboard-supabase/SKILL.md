---
name: daily-check-dashboard-supabase
description: >
  PILOT (Supabase) copy of daily-check-dashboard. Composes and deploys the Sophie Society
  pod Daily Check dashboard reading EVERYTHING from Supabase instead of local files:
  per-client snapshots from the dashboard_snapshots table, the expected-client list from
  the clients table, and the HTML template from the dashboards table. Zero data pulls,
  zero local-disk reads — runs fully headless with the machine off. Deploys to a SEPARATE
  pilot slug (sophie-daily-check-pilot-nacho) so it never touches the production dashboard.
  Trigger only for the migration pilot: "run the supabase daily-check dashboard", "compose
  the pilot dashboard", "refresh del dashboard piloto".
---

# Daily Check Dashboard — Supabase PILOT (compose & deploy)

**Versión actual:** V1.0 (2026-07-31). Copia piloto de `daily-check-dashboard` V1.1. Único cambio: la capa de datos pasa de archivos locales a Supabase. La lógica de compose/render/deploy es idéntica al original. Par del feeder `daily-check-client-supabase`. Ver `memory/dashboard_cloud_migration.md`.

> **🧪 ESTO ES EL PILOTO.** Corre en paralelo a la tarea local de producción sin pisarla:
> lee de Supabase (no del disco) y publica a un **slug separado** (`sophie-daily-check-pilot-nacho`).
> NUNCA uses la URL/slug de producción (`sophie-daily-check-pod-nacho`).

You compose the pod dashboard from Supabase and deploy it **once**. You pull **zero** AdLabs/Shurq data and read **zero** local files — the per-client `daily-check-client-supabase` runs already wrote their snapshots to the `dashboard_snapshots` table. Your job: query Supabase → render → deploy to the pilot URL.

---

## Supabase source of truth

Todo vía el conector **Supabase MCP** (`execute_sql`). Proyecto: `POD 66 - Organization`.

```
Snapshots:  dashboard_snapshots  (tipo='daily_check'; una fila por cliente/fecha; datos = snapshot completo)
Clientes:   clients              (active=true = quién aparece en el dashboard)
Template:   dashboards           (id='daily_check' → template_html + artifact_url)
Timezone:   America/Argentina/Buenos_Aires (ART)
```

**Failure rule:** log ONE specific line and stop; never loop. `⚠️ Dashboard piloto: {qué falló} — deploy {ok|omitido}`.

---

## Step 1: Fetch everything from Supabase (3 queries)

Run these with the Supabase MCP `execute_sql` tool. Save each result to the session scratchpad so the composer script (Step 2) can read them — those scratch files live in the cloud task's own workspace, NOT on Nacho's disk.

**1a — latest snapshot per client** (one row per client; `datos` is the full snapshot object):
```sql
select distinct on (cliente) cliente, datos, fecha, actualizado
from public.dashboard_snapshots
where tipo = 'daily_check'
order by cliente, fecha desc, actualizado desc;
```
Save the returned rows as JSON to `<scratchpad>/dc_snapshots.json`.

**1b — expected (active) clients**:
```sql
select brand,
       coalesce(config->>'amazon_marketplace', config->>'marketplace', 'US') as marketplace
from public.clients
where active = true;
```
Save to `<scratchpad>/dc_clients.json`.

**1c — template + artifact url**:
```sql
select template_html, artifact_url from public.dashboards where id = 'daily_check';
```
Save `template_html` to `<scratchpad>/dc_template.html` and keep `artifact_url` (may be null on first run — see Step 3).

If 1a returns zero rows → **STOP**, log `⚠️ Dashboard piloto: sin snapshots en dashboard_snapshots — deploy omitido`. If 1c returns no template → STOP + log.

## Step 2: Compose + render (Python — deterministic, auto-ASCII)

`json.dumps(..., ensure_ascii=True)` escapes every non-ASCII char (including emoji surrogate pairs) to `\uXXXX`, so the injected data is pure ASCII and the deployed file never mojibakes. Identical guarantee to the original skill.

```python
import json

SNAP = r"<scratchpad>/dc_snapshots.json"   # [{cliente, datos, fecha, actualizado}, ...]
CLI  = r"<scratchpad>/dc_clients.json"     # [{brand, marketplace}, ...]
TPL  = r"<scratchpad>/dc_template.html"
OUT  = r"<scratchpad>/daily-check-pilot-live.html"

snap_rows = json.load(open(SNAP, encoding="utf-8"))
snaps = [r["datos"] for r in snap_rows]          # each row's datos IS the old file body
assert snaps, "no snapshots"

template = open(TPL, encoding="utf-8").read()
assert template.count("@@DATA@@") == 1
assert template.startswith("<title>Sophie Daily Check")

EXPECTED = json.load(open(CLI, encoding="utf-8"))      # [{brand, marketplace}]

snaps.sort(key=lambda s: s["generated_at_iso"], reverse=True)
meta   = dict(snaps[0]["meta"])                        # newest snapshot wins global meta
newest = snaps[0]["meta"]["short_date"]

clients = []
for s in snaps:
    c = dict(s["client"])
    c["as_of_label"] = s["meta"]["short_date"] + " · " + s["meta"]["pull_time"]
    c["stale"] = s["meta"]["short_date"] != newest
    clients.append(c)

expected_names = {e["brand"] for e in EXPECTED}
mk = {e["brand"]: (e.get("marketplace") or "US") for e in EXPECTED}
orphans = [c["brand_name"] for c in clients if c["brand_name"] not in expected_names]
clients = [c for c in clients if c["brand_name"] in expected_names]      # baja: drop offboarded
have = {c["brand_name"] for c in clients}
for e in EXPECTED:                                                       # alta: pending placeholder
    if e["brand"] not in have:
        clients.append({"brand_name": e["brand"], "marketplace": mk.get(e["brand"], "US"), "status": "pending"})

nPend  = sum(1 for c in clients if c["status"] == "pending")
nStale = sum(1 for c in clients if c.get("stale"))
parts = []
if nPend:  parts.append(f"{nPend} cliente(s) pendientes del run de hoy")
if nStale: parts.append(f"{nStale} con datos de un run anterior")
meta["notice"] = " · ".join(parts) or None

data_json = json.dumps({"meta": meta, "clients": clients}, ensure_ascii=True)
html = template.replace("@@DATA@@", data_json)

assert "@@DATA@@" not in html
assert all(ord(ch) < 128 for ch in html)              # pure ASCII → no mojibake
assert html.startswith("<title>Sophie Daily Check")
json.loads(data_json)                                 # round-trips
open(OUT, "w", encoding="utf-8").write(html)
print(f"OK clients={len(clients)} pending={nPend} stale={nStale} orphans={orphans}")
```

If `orphans` is non-empty, mention them once in chat (clients with a snapshot but not active in the `clients` table).

## Step 3: Deploy (once) to the PILOT url

- If `artifact_url` from Step 1c is **non-null**: deploy `OUT` to it (Artifact tool `url=artifact_url`; in Cowork, `update_artifact` on slug `sophie-daily-check-pilot-nacho`). `favicon="🧪"`, `label` like `pilot-{newest}`.
- If `artifact_url` is **null** (first run): deploy `OUT` fresh (Cowork slug `sophie-daily-check-pilot-nacho`; or Artifact tool minting a new URL), then **persist the returned URL** so future runs reuse it:
  ```sql
  update public.dashboards set artifact_url = '<returned_url>', updated = now() where id = 'daily_check';
  ```

**Never deploy to the production slug/URL** (`sophie-daily-check-pod-nacho`). If a deploy returns a URL different from a non-null stored `artifact_url`, log it loudly and do NOT overwrite the stored one:
`⚠️ Dashboard piloto: el deploy devolvió {url_nuevo} ≠ {artifact_url} guardado. Revisar ownership/url en runs headless.`

Confirm: `"Dashboard PILOTO deployado: {n con data} con data · {nPend} pendientes · {nStale} stale → {url}"`.

---

## How this differs from production `daily-check-dashboard`

| Paso | Producción (V1.1) | Piloto Supabase (V1.0) |
|---|---|---|
| Snapshots | `glob dashboard-snapshots\*.json` (disco) | `select ... from dashboard_snapshots` |
| Clientes esperados | `_active_clients.json` (disco) | `select ... from clients where active` |
| Template | `_template.html` (disco) | `select template_html from dashboards` |
| URL registry | `_dashboard.json` (disco) | `dashboards.artifact_url` |
| Slug de deploy | `sophie-daily-check-pod-nacho` | `sophie-daily-check-pilot-nacho` |
| Compose / render / ASCII-safe | idéntico | idéntico |

Todo lo demás (orden de tarjetas, stale, placeholders pending, inyección ASCII-safe, asserts) es igual al original.

## Scheduling (cuando se valide el piloto — no crear todavía)

Mismo patrón que producción: una tarea de cierre después de los feeders per-cliente, TZ ART. Prompt: `Run the daily-check-dashboard-supabase skill. Read snapshots + clients + template from Supabase, compose the pilot dashboard, deploy once to the pilot slug. Zero pulls. Don't ask for confirmation.` No requiere carpeta local conectada (esa era la restricción de la versión de disco) porque no lee del filesystem.
