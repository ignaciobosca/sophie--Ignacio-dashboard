---
name: master-dashboard-supabase
description: >
  Composer for the 6-tab Sophie Master Dashboard (Daily / Negatives / Push / Review / Harvest / Restock).
  Reads EVERYTHING from Supabase: the dashboard_snapshots (by type) and the template from the
  dashboards table (id='master'). Rebuilds the 6-tab DATA, injects ASCII-safe, validates the
  JS with node --check, and PUBLISHES by writing index.html to the attached GitHub repo and pushing
  straight to main (served by GitHub Pages). Notifies Slack (#pod-66-team) with the fixed Pages link.
  ZERO data pulls, ZERO local files, ZERO artifact (therefore ZERO permission tap) —
  runs headless with the machine off. It is the closing pair of the 4 Supabase feeders. Trigger:
  "run the master dashboard supabase", "compose the master", "refresh del master dashboard",
  "refresh the master dashboard", "actualizá el master dashboard", "update the master dashboard".
---

# Master Dashboard — Supabase → GitHub Pages (compose & publish, 5 tabs)

**Versión:** V2.2 (2026-09-04). Igual que V2.1, pero **agrega el tab Review** (`DATA.review`), alimentado desde los snapshots `tipo='negatives_review'` (escritos por `weekly-negatives-review`, schema `negatives-review-v1`) y renderizado por `renderReview()` en el template. Antes el Weekly Review escribía a Supabase pero el composer no lo leía → no había superficie que lo mostrara. V2.1 restauró el tab Push (`DATA.push`) que había quedado sin alimentar; ver `memory/dashboard_cloud_migration.md`.

> **Publicación = GitHub Pages.** URL fija del dashboard:
> **`https://ignaciobosca.github.io/sophie--Ignacio-dashboard/`** (ojo la `I` mayúscula — las URLs de Pages son case-sensitive).
> Repo adjunto: **`ignaciobosca/sophie--Ignacio-dashboard`**, branch **`main`**, archivo **`index.html`** en la raíz.

Tu trabajo: query a Supabase → armar el `DATA` de 5 tabs → inyectar ASCII-safe → validar → **escribir index.html + git push a main**. **No pulls, no disco local, no artifact.**

> **Regression guard (obligatorio antes de publicar):** el `DATA` compuesto debe tener las 6 keys `meta, daily, negatives, push, review, harvest, restock`. Si falta cualquiera → **STOP, no publiques** — es exactamente el bug del 2026-09-02 (tab Push vacío) repitiéndose.

---

## Fuentes en Supabase (conector Supabase MCP, proyecto POD 66)

```
dashboard_snapshots  → los 6 feeds por tipo: 'daily_check' | 'negatives' | 'negatives_push' | 'negatives_review' | 'harvest' | 'restock'
dashboards           → id='master'  → template_html (token @@DATA@@ 1 vez; empieza con <title>Sophie Master Dashboard)
                       id='daily_check' → artifact_url (link al daily-check dashboard, para el tab Daily; puede ser null)
Timezone: America/Argentina/Buenos_Aires (ART)
```

**Failure rule:** log UNA línea específica y parar; nunca loopear. `⚠️ Master: {what failed} — publish {ok|skipped}`.

---

## Step 1: Fetch de Supabase (2 queries) → guardar en scratchpad

Corré con el conector Supabase `execute_sql`. Guardá los resultados en el scratchpad de la sesión (viven en el workspace del task de nube, NO en el disco de Nacho).

**1a — las 5 fuentes + el link del daily** (un solo query):
```sql
select json_build_object(
  'daily', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
            from (select distinct on (cliente) cliente, datos from public.dashboard_snapshots
                  where tipo='daily_check' order by cliente, fecha desc, actualizado desc) d),
  'negatives', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
                from (select cliente, datos, fecha from public.dashboard_snapshots
                      where tipo='negatives' and fecha >= (current_date - 7)
                      order by cliente, fecha desc) n),
  'push', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
           from (select cliente, datos, fecha from public.dashboard_snapshots
                 where tipo='negatives_push' and fecha >= (current_date - 7)
                 order by cliente, fecha desc) p),
  'review', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
             from (select cliente, datos, fecha from public.dashboard_snapshots
                   where tipo='negatives_review' and fecha >= (current_date - 7)
                   order by cliente, fecha desc) rv),
  'harvest', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
              from (select distinct on (cliente) cliente, datos from public.dashboard_snapshots
                    where tipo='harvest' order by cliente, fecha desc, actualizado desc) h),
  'restock', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
              from (select distinct on (cliente) cliente, datos from public.dashboard_snapshots
                    where tipo='restock' order by cliente, fecha desc, actualizado desc) r),
  'daily_link', (select artifact_url from public.dashboards where id='daily_check')
) as payload;
```
Guardá el `payload` como JSON en `<scratchpad>/master_payload.json`.

**Nota sobre `push`:** las filas de `tipo='negatives_push'` (escritas por `daily-negatives-autopush`) son **planas** — `datos` NO viene envuelto en `client`/`day` como `negatives`; sus keys están todas al mismo nivel: `brand`, `marketplace`, `currency_prefix`, `date_iso`, `data_window`, `summary`, `applied`, `held`, `asins_skipped`, `dropped`, `generated_at_iso`. El Step 2 reagrupa eso en la forma `client_obj` que el template espera.

**Nota sobre `review`:** las filas de `tipo='negatives_review'` (escritas por `weekly-negatives-review`, schema `negatives-review-v1`) también son **planas**: keys al mismo nivel `brand`, `date_iso`, `proposal[]`, `proposed_count`, `reviewed_count`, `archived_count`, `excluded_root_conflicts_kept[]`, y una nota (`note` | `discovery_notes` | `notes`, según la corrida). Cada `proposal[i]` trae `{texto, match|kind, confidence, product, reason, status}`. El Step 2 lo reagrupa a `{brand_name, days[]}` como el push (corre semanal, normalmente 1 día).

**1b — el template del master:**
```sql
select template_html from public.dashboards where id='master';
```
Guardá `template_html` en `<scratchpad>/master_template.html`. Si no hay template → STOP + log.

## Step 2: Compose + render (Python — determinístico, auto-ASCII)

`json.dumps(..., ensure_ascii=True)` escapa TODO char >127 (incluidos emojis/flechas del daily y negatives) a `\uXXXX`, así el DATA inyectado es ASCII puro y la página publicada nunca mojibakea.

```python
import json
from collections import OrderedDict
from datetime import datetime, timezone, timedelta

SCRATCH = r"<scratchpad>"
payload  = json.load(open(SCRATCH + r"\master_payload.json", encoding="utf-8"))
template = open(SCRATCH + r"\master_template.html", encoding="utf-8").read()
OUT      = SCRATCH + r"\index.html"

assert template.count("@@DATA@@") == 1
assert template.startswith("<title>Sophie Master Dashboard")

now_art = datetime.now(timezone(timedelta(hours=-3)))   # ART = UTC-3 fijo (Argentina sin DST); robusto, no depende de zoneinfo

# ── DAILY (último por cliente) ────────────────────────────────
daily_snaps = [r["datos"] for r in payload["daily"]]
daily_meta, daily_clients = {}, []
if daily_snaps:
    newest = sorted(daily_snaps, key=lambda s: s["generated_at_iso"], reverse=True)[0]
    daily_meta = dict(newest["meta"])
    newest_short = newest["meta"]["short_date"]
    for s in daily_snaps:
        c = dict(s["client"])
        c["as_of_label"] = s["meta"]["short_date"] + " - " + s["meta"]["pull_time"]
        c["stale"] = s["meta"]["short_date"] != newest_short
        daily_clients.append(c)

# ── NEGATIVES (últimos 7 días por cliente → reconstruir days[]) ─
neg_by_client = OrderedDict()   # rows vienen ordenadas por cliente, fecha desc (más nuevo primero)
for r in payload["negatives"]:
    neg_by_client.setdefault(r["cliente"], []).append(r["datos"])
neg_clients, neg_window_label = [], ""
for cli, snaps in neg_by_client.items():
    client_obj = dict(snaps[0]["client"])                 # contexto de la fila más nueva
    client_obj["days"] = [s["day"] for s in snaps if "day" in s]   # cada fila aporta su día (nuevo→viejo)
    neg_clients.append(client_obj)
    if not neg_window_label:
        neg_window_label = snaps[0].get("meta", {}).get("window_label", "")

# ── PUSH (últimos 7 días por cliente → reconstruir days[]) ─────
# Filas planas (tipo='negatives_push'): NO tienen 'client'/'day' anidado como 'negatives'.
push_by_client = OrderedDict()   # rows vienen ordenadas por cliente, fecha desc (más nuevo primero)
for r in payload.get("push", []):
    push_by_client.setdefault(r["cliente"], []).append(r["datos"])
push_clients = []
for cli, snaps in push_by_client.items():
    newest = snaps[0]                                  # fila más nueva → contexto del cliente
    push_clients.append({
        "brand_name": newest.get("brand", cli),
        "marketplace": newest.get("marketplace", ""),
        "currency_prefix": newest.get("currency_prefix", "$"),
        "days": [
            {
                "date_iso": s.get("date_iso"),
                "data_window": s.get("data_window"),
                "summary": s.get("summary", {}),
                "applied": s.get("applied", []),
                "held": s.get("held", []),
                "asins_skipped": s.get("asins_skipped", []),
                "dropped": s.get("dropped", []),
            }
            for s in snaps
        ],
    })

# ── REVIEW (últimos 7 días por cliente → reconstruir days[]) ──
# Filas planas (tipo='negatives_review'): keys al mismo nivel; corre semanal (normalmente 1 fila).
review_by_client = OrderedDict()
for r in payload.get("review", []):
    review_by_client.setdefault(r["cliente"], []).append(r["datos"])
review_clients = []
for cli, snaps in review_by_client.items():
    newest = snaps[0]
    review_clients.append({
        "brand_name": newest.get("brand", cli),
        "marketplace": newest.get("marketplace", ""),
        "days": [
            {
                "date_iso": s.get("date_iso", ""),
                "reviewed": s.get("reviewed_count"),
                "proposed": s.get("proposed_count"),
                "archived": s.get("archived_count", 0),
                "proposal": s.get("proposal", []),
                "excluded_kept": s.get("excluded_root_conflicts_kept", []),
                "note": s.get("note") or s.get("discovery_notes") or s.get("notes") or "",
            }
            for s in snaps
        ],
    })

# ── HARVEST (último por cliente) ──────────────────────────────
harvest_clients = [r["datos"]["client"] for r in payload["harvest"]]

# ── RESTOCK (último por cliente) ──────────────────────────────
restock_clients = [r["datos"]["client"] for r in payload["restock"]]
restock_snapshot_date = (payload["restock"][0]["datos"]["meta"].get("snapshot_date", "")
                         if payload["restock"] else "")

# ── DATA de 5 tabs (misma forma que el master original + push) ─
DATA = {
    "meta": {"generated": now_art.isoformat()},
    "daily":     {"link": payload.get("daily_link"), "meta": daily_meta, "clients": daily_clients},
    "negatives": {"window_label": neg_window_label, "clients": neg_clients},
    "push":      {"clients": push_clients},
    "review":    {"clients": review_clients},
    "harvest":   {"clients": harvest_clients},
    "restock":   {"snapshot_date": restock_snapshot_date, "clients": restock_clients},
}

data_json = json.dumps(DATA, ensure_ascii=True)
html = template.replace("@@DATA@@", data_json)

assert "@@DATA@@" not in html
assert all(ord(ch) < 128 for ch in html)          # ASCII puro → sin mojibake
assert html.startswith("<title>Sophie Master Dashboard")
json.loads(data_json)                               # round-trips
# Regression guard — ver nota al principio del skill: el bug del 2026-09-02 fue exactamente
# publicar con esta key faltante. No debilitar este assert.
assert set(DATA.keys()) == {"meta", "daily", "negatives", "push", "review", "harvest", "restock"}, \
    f"DATA le falta una tab — keys: {sorted(DATA.keys())}"
open(OUT, "w", encoding="utf-8").write(html)
print(f"OK daily={len(daily_clients)} neg={len(neg_clients)} push={len(push_clients)} review={len(review_clients)} harvest={len(harvest_clients)} restock={len(restock_clients)}")
```

**Validá el JS antes de publicar (obligatorio — un error de sintaxis deja el dashboard en pantalla negra para todo el equipo):** extraé el contenido del `<script>` del HTML compuesto a un archivo temporal `.js` y corré `node --check`. Si falla → STOP + log, **no publicar**.

## Step 3: Publicar → escribir index.html + git push directo a main

El repo **`ignaciobosca/sophie--Ignacio-dashboard`** está **adjunto** a la Routine (clonado en tu working tree). Publicá así:

1. Asegurate de que exista un archivo **`.nojekyll`** vacío en la raíz del repo (creálo si falta — desactiva el procesamiento Jekyll, así el HTML se sirve verbatim sin que `{{ }}`/`{% %}` en el JS lo rompan).
2. Copiá/escribí el contenido de `OUT` (`<scratchpad>\index.html`) a **`index.html` en la raíz del repo adjunto** (overwrite).
3. `git add index.html .nojekyll` → `git commit -m "dashboard update {now_art:%b %d %H:%M} ART"` → **`git push origin main`** (push DIRECTO a main; **NO** abras un Pull Request, **NO** crees una branch nueva).
4. Si `git commit` dice "nothing to commit" (el HTML salió idéntico al del día anterior), está OK: no hay cambios, saltá el push y seguí al Step 4. No es un error.

**No pidas confirmación para nada.** GitHub Pages reconstruye solo (~30-60s) y sirve el nuevo `index.html` en la URL fija.

Confirmá: `"Master published to GitHub Pages: {D} daily · {N} negatives · {P} push · {RV} review · {H} harvest · {R} restock → https://ignaciobosca.github.io/sophie--Ignacio-dashboard/ (commit {hash})"`.

## Step 4: Avisar a Slack (#pod-66-team)

Después de publicar OK, mandá UN mensaje **directo** (no draft) al canal `#pod-66-team` (`C0ATMQRFNUF`) vía `slack_send_message`. **La URL va EMBEBIDA como hyperlink de Slack** (formato `<url|texto>`) — NUNCA como URL cruda, porque Slack la corta. Y terminá con un salto de línea para que no se pegue el footer de Slack. La URL es **fija** (ya no cambia entre corridas). Formato:
```
🎛️ *Master Dashboard updated* · <date ART, e.g. Aug 12 · 10:02 ART>
📊 <https://ignaciobosca.github.io/sophie--Ignacio-dashboard/|Open the dashboard>
<D> daily · <N> negatives · <H> harvest · <R> restock
```
Ejemplo de llamada (ojo el formato `<url|texto>` de Slack y el `\n` final):
`slack_send_message(channel="C0ATMQRFNUF", text="🎛️ *Master Dashboard updated* · Aug 12 · 10:02 ART\n📊 <https://ignaciobosca.github.io/sophie--Ignacio-dashboard/|Open the dashboard>\n19 daily · 19 negatives · 1 harvest · 1 restock\n")`
La fecha/hora sale de `now_art` (Step 2, ART UTC-3).

> **No-bloqueante (importante):** si el envío a Slack falla (Slack caído, permisos, etc.) NO reintentes ni rompas la corrida — el dashboard YA quedó publicado en Pages. Logueá UNA línea (`⚠️ Master: dashboard published OK but the Slack notification failed: {reason}`) y terminá OK. El push a git es lo que importa; el Slack es el último paso.

---

## Cómo difiere de V1.0 (artifact) y del compose original (disco)

| Fuente / destino | Original (disco) | V1.0 (Supabase + artifact) | **V2.0 (Supabase + GitHub Pages)** |
|---|---|---|---|
| daily | `..\dashboard-snapshots\*.json` | `select ... tipo='daily_check'` | igual que V1.0 |
| negatives | `negatives\*.json` (days[]) | `select ... tipo='negatives' fecha>=hoy-7` → days[] | igual que V1.0 |
| harvest / restock | `harvest\*.json` / `restock\*.json` | `select ... tipo='harvest'|'restock'` | igual que V1.0 |
| template | `_template.html` | tabla `dashboards` id='master' | igual que V1.0 |
| compose / ASCII-safe / node --check | idéntico | idéntico | idéntico |
| **publicación** | deploy artifact a slug prod | deploy artifact a slug piloto (**pedía tap**) | **git push index.html a main → Pages (sin tap)** |
| **URL** | slug de artifact | slug de artifact (dinámica) | **fija: `ignaciobosca.github.io/sophie--Ignacio-dashboard/`** |

## Scheduling (Routine de nube)
Una Routine de cierre, después de que corran los feeders del día (daily ~9:30; negatives 6am; restock/harvest semanales). Ej. Daily ~10:00 ART. Prompt: `Run the master-dashboard-supabase skill: read the 4 sources from Supabase, compose the 4-tab master dashboard, write index.html to the attached repo and push directly to main. Zero pulls, no local files, no artifact. Post the Slack notification at the end. Don't ask for confirmation.`
**Config de la Routine:**
- **Repo adjunto:** `ignaciobosca/sophie--Ignacio-dashboard` (obligatorio — es el destino de publicación).
- **Connectors:** **Supabase** (leer los snapshots + template) + **Slack** (aviso del Step 4).
- Sin carpeta local. Sin conector de GitHub (se publica por git nativo con el repo adjunto).
