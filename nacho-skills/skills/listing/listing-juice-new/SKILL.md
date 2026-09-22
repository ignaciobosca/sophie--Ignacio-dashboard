---
name: listing-juice-new
description: "Listing Juice by Sophie Society (v4.3, Sophie Hub mode 4). Full Amazon listing optimization audit for US, UK/EU and other marketplaces (auto-detected); invoke explicitly with 'listing juice'. Works with the Sophie Hub MCP (optional auto-pull of Amazon reports) or manual uploads, and runs a pre-run data check that flags gaps and asks before running. Combines the Category Listings Report (or a Seller Central edit-listing screenshot) with optional SQP, review, Xray, and PPC data to produce a branded HTML audit (the sole deliverable; a partial-update flat file only on request). Adds title compliance: a ~75-char keyword-led title alongside the performance title. ALWAYS-ON: every run emits three Sophie Society blocks per ASIN, a Main-Image tactics screen, a fixed 7-slot Secondary-Image sequence, and a 7-module A+ Premium plan, plus structured-attribute visibility and a product-facts image handover. Optimizes for Alexa Shopping discoverability and A9 organic rank. Explicit invocation only."
sophie-skill-format: v1
---

## ▶▶ RUN GATE — do this FIRST, before anything else (do not skip)
**STOP. Before any tool call, MCP/connector call, file read, script run, or workflow step below — halt and gather EVERYTHING you need in one upfront ask.** This is a blocking instruction to you, the runner, not a description. The goal of this gate is to collect all requirements ONCE, before any §5 step runs, and to pick the data source. The gate is one coherent pre-run flow: **acquire → data check (flag gaps) → confirm → run.** You gather requirements and acquire the data, then run a pre-run data check that shows the seller exactly what data you have and what is missing (flagging Sophie Hub gaps in particular), get their go-ahead, and only then start the §5 audit. Never auto-run past a gap silently.

1. **Open with the goal + deliverable** (keep the warm 2-3 sentence orientation from §5 "When you're invoked" — what you will do and what they get back: most important fixes first, copy-ready title in two options including the compliant ~75-char one, rewritten bullets/description, backend keywords, prioritized next steps, all cited to their own data).

2. **Then, in ONE upfront ask, gather all of this before doing anything:**
   - **(1) Target ASIN/SKU [required].** The exact child ASIN/SKU to audit. Never guess the variation (see the SKU-confirmation gate in §5).
   - **(2) The data source.** First **DETECT whether the Sophie Hub MCP tools are available** in this session (see §1 and Step 0.4 — look for the Sophie Hub tool set; do NOT assume a fixed server GUID). 
     - If Sophie Hub tools ARE present, offer the auto-pull: *"Is your store connected to Sophie Hub? If so, I can pull your Amazon reports (Category Listings Report, Search Query Performance, PPC search-term report) automatically, so you don't have to download them. Otherwise, just upload them here and I'll take it from there."*
     - If Sophie Hub tools are NOT present, do not mention MCP; present the existing manual "what to send and where to get it" upload guide (§5).
   - **(3) Marketplace**, only if it can't be auto-detected — i.e. screenshot-only or the report resolves to UNKNOWN. When a Category Listings Report will be provided, the marketplace auto-detects and you don't need to ask.
   - **(4) Optional files that sharpen the audit:** note that SQP, Helium 10 Review Insights, PPC search-term report, and Helium 10 X-Ray each make the audit deeper, and that **the Helium 10 files (Review Insights + X-Ray) are upload-only** (Sophie Hub does not carry third-party Helium 10 data), while the Amazon-native reports can come from Sophie Hub OR upload.

3. **Then STOP and wait.** Do not run any §5 step (not even Step 0.5 / Step 1 `parse_inputs.py`) until you have BOTH: (a) the confirmed exact SKU/ASIN, and (b) at least the one required input actually available — either fetched via the optional Sophie Hub auto-pull (Step 0.4, which drops files into the uploads dir) OR uploaded by the seller (Category Listings Report **or** an edit-listing screenshot). If the required input is still missing, present the friendly "what to send and where to get it" guide (§5) and STOP. Keep the "confirm the exact SKU, never guess the variation" gate from §5.

4. **Pre-run data check — flag any gaps, then confirm (do this AFTER acquire, BEFORE any analysis).** Once the required input is in hand (fetched via Sophie Hub Step 0.4 and/or uploaded) and the SKU is confirmed, but BEFORE you run the audit's §5 parse/diagnostics, show the seller exactly what data you have and what is missing, then WAIT for their go-ahead. This is a blocking checkpoint, not narration: the whole point is that the seller sees the gaps before the run, so never auto-run past a gap silently.

   **Build the checklist from what actually landed in the uploads dir.** You may run `python3 scripts/parse_inputs.py --uploads /mnt/user-data/uploads --out /tmp/parsed.json` once as a detection pass and read its `inputs_detected` block (`flat_file`, `sqp`, `reviews_count`, `xray_asins`, `xray_keywords`, `ppc_search_terms`, `screenshots_count`) — that detection output is the authoritative source of what is present (Rule 1: the script's detection is ground truth, not what anyone said they sent). `parse_inputs.py` is deterministic and idempotent, so this detection pass changes and consumes nothing; §5 Step 1 re-runs it as the authoritative audit parse. Do NOT run diagnostics or any later §5 step yet.

   **Enumerate every expected input and its status** — for each, mark it obtained ✓ (and via which source: Sophie Hub or upload) or MISSING:
   - **Category Listings Report** *(or, as a lighter substitute, an edit-listing screenshot)* — **REQUIRED.** Obtained when `inputs_detected.flat_file` is set (the report) or `screenshots_count > 0` (the screenshot).
   - **Search Query Performance (SQP)** — optional. Obtained when `inputs_detected.sqp` is set. (Sophie Hub OR upload.)
   - **Helium 10 Review Insights** — optional. Available via the **Helium 10 MCP** (`get_asin_review_analysis`) when connected; upload only if those tools are absent. Not from Sophie Hub. Obtained when `inputs_detected.reviews_count > 0`.
   - **Helium 10 X-Ray (competitor ASINs + keywords)** — optional, **upload-only**. Obtained when `inputs_detected.xray_asins` and/or `xray_keywords` is set.
   - **PPC Search Term report** — optional. Obtained when `inputs_detected.ppc_search_terms` is set. (Sophie Hub OR upload.)

   **Flag Sophie Hub gaps explicitly (MCP path only).** If Step 0.4 (Sophie Hub) was used, call out every Amazon-native report Sophie Hub was expected to provide but could NOT — for example SQP not returned for this store, a report fetch that failed or timed out, or the store simply has no data for that report. Name the gap and what it limits, per report; do not fold Sophie Hub gaps silently into a generic "optional missing" line. Example wording: *"No SQP came back from Sophie Hub for this store, so the search-term/funnel view (how many shoppers see your listing, then click, then buy) will be limited or skipped. You can upload the SQP export yourself, or we can go ahead without it."*

   **For each MISSING optional input, say in plain seller language what it would add** (and which part of the audit is degraded or skipped without it):
   - **SQP** → powers the search-term / funnel view (how many shoppers see your listing, then click, then buy) and the keyword-and-title priorities. Without it that funnel view is limited or skipped.
   - **Helium 10 Review Insights** → your customers' own words and their most common objections. Without it the review-theme read and the objection-handling in your bullets are skipped.
   - **Helium 10 X-Ray** → how you stack up against competitors (title length, number of images, review counts) and the keyword gaps you could own. Without it the competitive comparison and white-space keywords are skipped.
   - **PPC Search Term report** → the exact search terms your ads already convert on (worth doubling down on) and the ones wasting spend. Without it those ad-driven keyword signals are skipped.

   **Then flag + ask before running, and WAIT for the answer:**
   - **If the one REQUIRED input is MISSING** (no Category Listings Report and no edit-listing screenshot) → **hard stop, do not run.** Tell the seller you can't audit without it and guide them to provide it (the friendly "what to send and where to get it" guide in §5; or, in MCP mode, reconnect/authenticate Sophie Hub and re-pull). Wait for it before doing anything else.
   - **If only optional inputs are MISSING** → present the gaps above and **ask which way to go: (a) provide the missing data now** (upload the file, or reconnect Sophie Hub and re-pull the Amazon-native report), **or (b) proceed with a knowingly-limited audit** that skips the affected parts. Wait for their explicit choice; never silently auto-run past a gap.
   - **If nothing is missing**, still show a short "here's everything I have" confirmation and get the go-ahead before running.

   Keep it warm and plain-language, consistent with the intake and the friendly guide in §5 (no jargon; describe the funnel as "how many shoppers see your listing, then click, then buy").

5. Only after the data check is confirmed and both requirements are met, proceed to §5 (the original skill logic, authoritative). The data source (Sophie Hub MCP auto-pull, manual upload, or hybrid) only changes how the uploads dir gets populated; the §5 build core (parse → diagnostics → HTML/xlsx) is identical either way. Keep progress narration in plain, customer-friendly language (§5 "Progress narration").

# Listing Juice (by Sophie Society) — full Amazon listing optimization audit (branded HTML)

## §1 Overview
Listing Juice turns a seller's own Amazon data into a branded **HTML listing-optimization audit** (the sole deliverable; an upload-ready partial-update **xlsx** flat file is produced only on explicit request). It parses the Category Listings Report (or a Seller Central edit-listing screenshot) plus optional SQP, Helium 10 review, Xray, and PPC exports with bundled Python scripts, runs funnel + COSMO + competitive diagnostics, and writes per-ASIN rewrites, a compliant ~75-char title, and the three always-on Sophie Society blocks (Main-Image tactics, 7-slot Secondary-Image sequence, 7-module A+ Premium plan). `output.format: html` (primary); secondary `output.format: xlsx` (opt-in flat file).

**Modes by stage (honest):**

| Stage | MCP (Sophie Hub) | Manual | Hybrid |
|-------|-----|--------|--------|
| Acquire inputs (Amazon-native: Category Listings Report / SQP / PPC) | ✅ OPTIONAL auto-pull from Sophie Hub → saved into the uploads dir (Step 0.4) | ✅ seller uploads files | ✅ Sophie Hub for the Amazon reports + manual for the rest |
| Acquire Helium 10 (Review Insights / X-Ray) | ✅ via the **Helium 10 MCP** when connected (`get_asin_review_analysis`, `get_listing_details`, `search_competitors_by_asin`) — not from Sophie Hub | ✅ seller uploads files | ✅ MCP where available, upload otherwise |
| Build core (parse → diagnostics → HTML/xlsx) | ✅ same local Python scripts (source-agnostic) | ✅ local Python scripts | ✅ local Python scripts |
| Deliver (HTML, opt-in xlsx) | ✅ `present_files` | ✅ `present_files` | ✅ `present_files` |

**Two ways to get the Amazon-native reports in: Sophie Hub MCP (optional) OR manual upload.** The Sophie Hub MCP is a convenience auto-acquire that fetches the seller's Amazon-native reports and drops them into `/mnt/user-data/uploads/` under the filenames the detector already recognizes, so `parse_inputs.py --uploads` picks them up unchanged. It is **strictly optional and never a hard dependency**: if Sophie Hub isn't connected, isn't authenticated, or returns no store, the skill falls back to manual upload with no error (see §6 Fallback rules and Step 0.4). **Manual upload always works and is the guaranteed fallback.** Helium 10 Review Insights and X-Ray are third-party and are NOT available from Sophie Hub, so they remain upload-only in every mode. Hybrid (Sophie Hub for the Amazon reports + manual Helium 10) is fully supported. The build core is identical regardless of how the files arrived.

## §2 Dependencies
| Kind | Name | Pinned version | Per-OS fallback |
|------|------|----------------|-----------------|
| MCP  | Sophie Hub (OPTIONAL) | detect at runtime — not pinned to a GUID | falls back to manual upload if absent/unauthenticated/no store (never a hard dependency) |
| CLI  | python3 | 3.8+ | system python3 |
| Lib  | openpyxl | (see requirements.txt) | `pip install -r requirements.txt \|\| pip install openpyxl pandas numpy` |
| Lib  | pandas | (see requirements.txt) | same as above |
| Lib  | numpy | (see requirements.txt) | same as above |

Bundled scripts under `scripts/` do all parsing, diagnostics, HTML assembly, and xlsx writing — do not reimplement inline (see §5 Execution flow).

## §3 Preflight & mode select  *(THE START POINT — ask up front, required)*
1. Run `python3 scripts/sophie_skill.py probe` (if the helper is present) → OS, python, libs; otherwise confirm python3 + `pip install -r requirements.txt`.
2. **MCP/connector check (OPTIONAL):** detect whether the **Sophie Hub** MCP tools are present in this session (see Step 0.4 — do not assume a fixed server GUID). This is optional: if they are present you may offer the auto-pull of the Amazon-native reports; if they are absent, proceed with manual upload and do not attempt to connect any other connector.
3. Present the source choice (per the RUN GATE): **Sophie Hub MCP auto-pull (optional, only when its tools are detected)**, **Manual upload (always available, the guaranteed fallback)**, **Hybrid (Sophie Hub for Amazon reports + manual Helium 10)**.
4. Confirm the target SKU/ASIN and that at least the required input is available (fetched via Sophie Hub or attached), then proceed. Record the source used (MCP / Manual / Hybrid) in the run manifest.

## §4 Inputs
| Input | Type | Required | Default | If missing |
|-------|------|----------|---------|-----------|
| Target ASIN/SKU | text | yes | — | ask before auditing (never guess the variation) |
| Category Listings Report | `.xlsm`/`.xlsx` file | yes* | — | ask; *or* accept an edit-listing screenshot instead |
| Seller Central edit-listing screenshot | `.png`/`.jpg`/`.jpeg` | yes* | — | *substitute for the report; one of the two is required |
| SQP export | `.csv` | no | — | run without funnel diagnostic; note the limit in HTML |
| Helium 10 Review Insights | `.xlsx` | no | — | skip review-theme analysis |
| Helium 10 Xray (ASINs / keywords) | `.csv` | no | — | skip competitive benchmark |
| PPC Search Term Report | `.csv`/`.xlsx` | no | — | skip harvest/negate signals |

\*Exactly one of {Category Listings Report, edit-listing screenshot} is strictly required. Validate all inputs before any work; fail fast with a specific "I need X". `parse_inputs.py` mode detection is authoritative (Rule 1).

### Manual-mode inputs — "You provide"  *(shown when the user picks Manual)*
| Input | Format | Where/how to get it | Required |
|-------|--------|---------------------|----------|
| Target ASIN/SKU | text | The child ASIN/SKU you want audited (paste it) | yes |
| Category Listings Report | `.xlsm`/`.xlsx` | Seller Central → menu → Reports → Inventory Reports → Report Type: **Category Listings Report** → Request Report → Download | yes (or screenshot) |
| Edit-listing screenshot | `.png`/`.jpg`/`.jpeg` | Seller Central → Inventory → Manage All Inventory → **Edit** (screenshot the page) | yes (if no report) |
| SQP export | `.csv` | Brand Registry → Brands → Brand Analytics → **Search Query Performance** → ASIN view → last 3 months → Generate Download | recommended |
| Helium 10 Review Insights | `.xlsx` (2 files) | Amazon product page with Helium 10 on → **Analyze Reviews** (product) + **Category Reviews & Returns** → download both | recommended |
| PPC Search Term Report | `.csv`/`.xlsx` | Advertising → Sponsored Products → Reports → **Search Term** report → 60 days → download | recommended |
| Helium 10 X-Ray | `.csv` | Helium 10 on a search results page → **X-Ray** → Export | optional |

**How these inputs arrive.** The **Amazon-native** reports (Category Listings Report, SQP / Search Query Performance, PPC Search Term report) can be pulled automatically from the **Sophie Hub MCP** when it's connected (Step 0.4) OR uploaded by hand — either way they land in `/mnt/user-data/uploads/` and the scripts auto-detect each by filename/content. The **Helium 10** inputs (Review Insights, X-Ray) are third-party and have **no Sophie Hub equivalent**, so they are always manual uploads. Manual upload is the guaranteed fallback for everything (default location `/mnt/user-data/uploads/`).

## §6 Fallback rules
- **Sophie Hub MCP is optional — always fall back to manual, never hard-fail.** The full graceful-fallback ladder (applies throughout, hard requirement):
  - (a) Sophie Hub tools **not available at all** in the session → go straight to manual mode, no error, don't mention MCP.
  - (b) Sophie Hub present but **session not authenticated** (`verify_session` fails/expired) → manual mode.
  - (c) Authenticated but **zero stores/profiles** from `list_stores` → tell the seller: *"Sophie Hub is connected but returns no store for this login, finish connecting Amazon to Sophie Hub, or just upload your reports,"* then fall back to manual.
  - (d) **Any MCP tool error or timeout** (discover/fetch/S3) → fall back to manual for that file, never hard-fail the run.
  - (e) **Never substitute a different (non-Sophie-Hub) connector's tools** to source data. If it isn't the Sophie Hub tool set, it isn't used.
  - The skill must **always be completable via manual upload alone.** If a seller asks to "pull it from Sophie Hub" and Sophie Hub isn't available, say so plainly and ask them to upload the reports instead.
- **Missing required input** → present the friendly guide (in the body below) and STOP; do not audit.
- **`ModuleNotFoundError`** → `pip install -r requirements.txt || pip install openpyxl pandas numpy` and retry (Step 0.5 in the body).
- **`mode: null`** from `parse_inputs.py` → ask the seller for a Category Listings Report or an edit-listing screenshot; do not guess.
- **Partial data** (some optional files missing) → run with what's present and state the limitation honestly in the HTML; never fabricate a diagnostic that lacks its data source.
- **Missing output at verify** → `check_outputs.py` exit 2 / Step 9 grep fails → fix and rebuild before `present_files`; never ship a half file.

## §7 Output contract  (`output.format: html`; secondary `xlsx` opt-in)
Primary deliverable: a **self-contained branded HTML audit** at `/mnt/user-data/outputs/Listing Juice - [ASIN] - [Brand] - [YYYY-MM-DD].html`. Optional secondary: partial-update **xlsx** (opt-in only).
- Built by `scripts/build_html_report.py` from a report JSON — never hand-write HTML. Fails (exit 2) on any unsubstituted `{{PLACEHOLDER}}`.
- Deterministic output dir + filename (ASIN/Brand/date slots; `Portfolio` for multi-ASIN).
- Run `check_outputs.py` (Rule 3) + the Step 9 grep (three always-on Sophie blocks present) before `present_files`.
- Embed the run manifest (`python3 scripts/sophie_skill.py manifest ...`) recording the data source used (MCP / Manual / Hybrid) and the hardenings applied.
- Finish with the delivery card (`python3 scripts/sophie_skill.py card ...`) → clickable `file://` link to the HTML (and xlsx if generated).

**Determinism flags for the author (⚠️ — not auto-fixed):**
- **Clock:** filename/date uses `$(date +%Y-%m-%d)` in the body and `date` fields inside `build_html_report.py`. Clock was hardened where the helper could pin `datetime.now()/date.today()`; the shell-`$(date ...)` in the bash examples still reads the live clock — run with `SOPHIE_RUN_TS` and set the report `date` field from it for reproducibility.
- **Locale leaks:** verify any number/currency formatting in `build_html_report.py` does not depend on system locale (`toLocaleString`/locale-formatted dates) — FLAG for review.
- **Fonts / CDN:** the HTML must embed fonts and inline any CDN/JS so it renders in a sandbox; confirm no external `src`/font URLs remain — FLAG for review.

## §8 Gates
- **No outward action:** the only MCP use is the OPTIONAL, read-only Sophie Hub fetch of the seller's own Amazon reports (Step 0.4); the skill posts nothing to Slack/Notion/email and applies nothing to any live listing. It reads uploaded/fetched files and writes local output files, then presents them.
- Before generating the **opt-in xlsx**, confirm the seller explicitly asked for an upload-ready flat file, and which title (performance vs ~75-char) to write (Step 8b in the body).
- Do not auto-apply anything to a live listing — every rewrite is a proposal the seller applies themselves.

---

## §5 Run procedure — original skill logic (verbatim, authoritative)

> **Mode:** Sophie Hub MCP (optional) OR Manual, with Hybrid supported (see RUN GATE + Step 0.4). The files in §4 arrive either via the optional Sophie Hub auto-pull (Amazon-native reports only) or by manual upload (always available; the only source for Helium 10). Everything below is the original skill body, unchanged and authoritative. Where it references upload paths and `present_files`, those are the acquire/deliver ends of the narrow waist; the build core (parse → diagnostics → HTML/xlsx) is deterministic and identical regardless of how the files got into the uploads dir.

# Listing Juice (by Sophie Society)

## When you're invoked (intake)

The people running this skill are sellers who are often less experienced than the Sophie Society team. Greet them warmly, in plain language, with no jargon, and behave adaptively: if the files are already attached, move quickly; if something is missing, slow down and guide them. Open by telling the seller what it does and what they get, THEN deal with the inputs. Lead with the goal and the deliverable, in one or two clean lines, before any file list. Keep it warm and consumer-ready, not like an internal checklist.

**Always open with a short orientation (2-3 sentences):** what you will do and what they will get back, the most important fixes first, copy-ready title, bullets and description, two title options including a compliant ~75-character one for Amazon's July 27 title rule, and prioritized next steps, all cited to their own data.

Say something close to this (adapt the wording, keep the order: goal + deliverable, then inputs):

> I'll turn your Amazon listing data into a branded HTML listing-optimization audit: a clear, shareable report that leads with the most important fixes, then gives you a compliant title (in two options, a full one and a shorter one that's safe under Amazon's new July 27 title rule), rewritten bullets and description you can copy with one click, backend keywords, and prioritized next steps, all cited to your own data.
>
> To get started, send me:
> - The **ASIN** (or SKU) you want me to audit (so I focus on the right product, even if your report covers a whole catalog)
> - Your **Category Listings Report** (`.xlsm`/`.xlsx` from Seller Central), or a clear **screenshot** of the Seller Central edit-listing page
> - Optional, for a deeper audit: Search Query Performance (SQP) export, Helium 10 Review Insights, a PPC search term report, and Helium 10 X-Ray

**Marketplace support.** This skill works for **US, UK/EU, and other Amazon marketplaces**. The marketplace is detected automatically from the Category Listings Report and stated in the report. If the seller only sends a screenshot (no report to detect from), or detection is unclear, ask which marketplace the listing is on before auditing. See "Marketplace support" below. Note that the built-in regulatory/claims examples are US-based, so for a non-US marketplace the report flags that claims must be verified against the local rules.

**Recommended vs optional inputs.** The Category Listings Report (or, as a lighter substitute, an edit-listing screenshot) is the only strictly required input. Search Query Performance (SQP), Helium 10 Review Insights (your product and the category), and the PPC Search Term Report are all recommended, they make the audit noticeably sharper. Competitor data (a Helium 10 X-Ray export, and competitor Review Insights) is optional.

**Always request the target ASIN/SKU upfront**, in this same opening list, alongside the files. Then, **before auditing, always confirm the exact SKU (or child ASIN)** you'll review, and never guess the variation. The Category Listings Report usually lists the whole catalog, one listing can have several child ASINs (sizes, colors, packs), and the same ASIN can appear more than once. If the seller did not name a SKU and the report has more than one, ask which one before continuing rather than raising it as a later follow-up.

**If the required input is missing** (no Category Listings Report and no edit-listing screenshot), present the friendly "what to send and where to get it" guide below, then STOP and wait. Do not start auditing until you have at least the required input. **If files are already attached**, skip the full guide: briefly confirm what you detected and what each file unlocked, confirm the SKU, and continue.

Present this guide when the required input is missing (adapt the wording, keep it friendly):

> **Hi! I'm going to audit your Amazon listing and hand you a clear report: the most important fixes first, a rewritten title, bullets, and description you can copy with one click, and two title options (a full one and a shorter one that's safe under Amazon's new July 27 title rule). It takes a few minutes once I have your files.**
>
> **Here's exactly what to send and where to get it. The first one is the only must-have, the rest make the audit sharper.**
>
> **1. Category Listings Report (required, the main one).** In Seller Central, click the menu (top-left) then under Reports choose Inventory Reports, in the Report Type dropdown pick Category Listings Report, click Request Report, wait a minute, then Download. It downloads as an .xlsm or .xlsx file. Don't see it in the dropdown? Message Seller Support and ask them to turn on the Category Listings Report; they usually enable it within a day for about a week. No time for that? You can instead send a screenshot of your listing's Edit page (Inventory, Manage All Inventory, Edit). It's a lighter version but still works.
>
> **2. Search Query Performance, SQP (recommended).** This powers your keyword and title recommendations. You'll need Brand Registry. Go to Brands, Brand Analytics, Search Query Performance, switch to ASIN view, set the date range to the last 3 months (one full quarter), click Generate Download, and save the file.
>
> **3. Helium 10 Review Insights (recommended, two downloads).** Open your product's page on Amazon with the Helium 10 extension on. Near the top you'll see two separate Analyze Reviews buttons: one for your product's reviews and one for Category Reviews & Returns. Download both (two files). Optionally, open a few closely-related competitor product pages and download their review insights the same way (Amazon's categories can be broad, so a handful of close competitors you pick yourself is more useful than the whole category).
>
> **4. Search Term Report, PPC (recommended).** Go to Advertising, Sponsored Products, Reports, create a Search Term report, set it to the maximum 60 days, and download it.
>
> **5. Helium 10 X-Ray (optional, competitors).** With the Helium 10 extension, search your main keyword on Amazon, open X-Ray on the results page, and click Export to get the competitor file.
>
> **One important thing before I start:** tell me the exact SKU (or child ASIN) you want me to review. Your report usually lists your whole catalog, and one listing can have several versions, sometimes under the same ASIN. Paste or highlight the SKU you care about and I'll confirm I have the right one before I begin. Not sure which it is? Send it over and I'll help you find it.
>
> **Send whatever you have and I'll tell you what each file added. The more you include, the deeper the audit, but the Category Listings Report alone is enough to get started.**

The branded HTML audit is the one and only output of the normal flow, do not ask the seller to choose between output formats, and do not pitch an uploadable file as a headline benefit during intake. (Advanced, not a question to ask during intake: the skill can also generate an upload-ready partial-update xlsx for Seller Central's Listing Loader from the same analysis; only produce it if a seller explicitly requests it. See Step 8b.)

## Progress narration (how you talk while the skill runs)

This applies to every step/progress line you emit WHILE the skill is running, not just the final report. The seller is a small business owner watching the chat, not an engineer. Narrate each step in plain, customer-friendly language that tells them what you are doing FOR THEM, not the internal mechanism, the script names, or the data-pipeline jargon.

Say what the seller gets out of the step, in everyday words. Keep each line short and human. Describe the benefit or the action in their terms.

Good (use language like this):
- "Reading your reports"
- "Checking how your listing performs against the market"
- "Finding what shoppers actually search for"
- "Writing your new title and bullet points"
- "Putting your audit together"

Avoid (never narrate like this):
- "Orchestrated diagnostic workflow across multiple data sources"
- "Parsed multiple datasets to extract and format specific product analysis"
- "Analyzed product metrics and identified performance discrepancies"
- "Diagnosed listing performance gaps and strategized title optimization"

Rule of thumb: if a non-technical seller would not instantly understand the line, rewrite it. No "parsed", "datasets", "diagnostic workflow", "orchestrated", "metrics", "discrepancies", "strategized". Talk about their reports, their listing, their shoppers, their title and bullets, their audit.

## What this skill does

Takes seller-accessible data, parses whatever is available, runs a full listing audit enriched with funnel diagnostics and customer vocabulary, and produces:

1. **A branded HTML analysis report** — the single deliverable of the normal flow. Sellers share it, save it as a PDF, or use it as a working doc. Every recommendation is cited with its data source.

**Advanced capability (not part of the normal flow, never offered as a choice during intake):** the skill can also generate an upload-ready partial-update Amazon flat file (xlsx for Seller Central's Listing Loader) from the same analysis. Produce it ONLY when a seller explicitly asks for an upload-ready xlsx, Listing Loader file, or partial-update file. It contains only the changes the skill is confident about; the seller reviews and uploads it via Listing Loader. See Step 8b.

Present via `present_files`. HTML opens first; xlsx (if a seller explicitly requested one) opens second.

**ALWAYS-ON / NON-NEGOTIABLE, Sophie Society image + A+ Premium recommendations.** Every run MUST produce three additional Sophie-Society-sourced blocks per ASIN, sourced from `references/sophie-society-image-and-aplus-sops.md`. These are part of the core deliverable, same tier as the title rewrite, not a feature to offer or gate on the seller's permission:

1. **Main image recommendations** — screen the 15 Sophie Main-Image CTR tactics against the current main image, rank the top 3 to 6 with product-specific mockup direction.
2. **Secondary image sequence** — Sophie's fixed 7-slot sequence (2 lifestyle bookends + main + 4 infographics, 3 chosen from the 20-type taxonomy).
3. **A+ Premium module plan** — Sophie's 7-module Pro structure with exact Seller Central module names, plus the 5-module Limited fallback.

Do NOT ask the seller whether to include them, do NOT mark them as optional add-ons, do NOT skip them in screenshot mode, and never emit an empty block (if a listing has no obvious opportunity, still emit the block with a "current stack is on target because X" line). See Step 4b for how to build them and Step 9 for the enforcement check.

**Copy buttons:** every proposed edit in the HTML (title, each bullet, description, backend, the compliant ~75-char title, and each proposed structured-attribute value) renders with a one-click Copy button. This is automatic in the templates, no action needed when assembling the report JSON.

**Dual optimization goal:** every recommendation must not degrade Alexa Shopping COSMO coverage or A9 keyword coverage — enforced by the Step 5 validation gate. Track and surface two scores per ASIN in the HTML: **Alexa Shopping score** (COSMO 15-dimension coverage) and **A9-relevant score** (priority keyword presence + backend coverage + structured completeness + CVR-signal quality).

**What this skill does NOT do:** auto-apply changes to live listings. Every rewrite is a proposal — the seller reviews the HTML and either copy-pastes into Seller Central edit-listing or, if they asked for the xlsx, uploads the partial-update file.

**Title compliance layer (additive).** On top of the normal title rewrite, the skill also produces a shorter Amazon-compliant title (around 75 characters) for each ASIN and shows both options. The longer performance title stays the recommended option for ranking and coverage today; the ~75-char version is included because, from July 27, Amazon can auto-rewrite over-length titles. This layer adds an option, it changes nothing else in the run. See `references/title-compliance.md`.

## Critical rules (do not violate)

These rules fix failure modes observed in past runs. They override intuition, user framing, and defensive thoroughness.

### Rule 1 — The script's mode detection is authoritative

`scripts/parse_inputs.py` programmatically detects the input mode. **Its output is the ground truth**, not what the user said, not what the filename looks like, not what the primary-looking file seems to be.

- If a flat file (`.xlsm`/`.xlsx` matching `Category_Listings_Report*`) is present, the script will report `mode: 2` (flat-file mode). That label applies **even if the user's message described their input as "a screenshot" or mentioned a PDF or image**. The user's framing is a hint, not a decision.
- If only images are present, the script reports `mode: 3` (screenshot mode).
- If neither, the script reports `mode: null` and you stop and ask.

When in doubt, trust the JSON. The user does not always know what they uploaded or how it classifies.

### Rule 2 — Numerical facts come from the diagnostics JSON, not from images

All listing-state numbers — title character count, bullet lengths, image count, populated structured attribute count, price, reviews, rating — come from `diagnostics.json` produced by `scripts/run_diagnostics.py`. **Do not visually estimate or eyeball-count from a PDF, screenshot, or image when the JSON has the exact number.**

This has been a real failure mode: Claude reading a title off an image and reporting "83 chars" when `len(title)` on the same string from the flat file is 104. Every number in the HTML must trace to a JSON field, not to visual inspection.

### Rule 3 — Output checklist before `present_files`

Before calling `present_files`, verify outputs exist:

1. HTML report at `/mnt/user-data/outputs/Listing Juice - [ASIN] - [Brand] - [YYYY-MM-DD].html` (always required). Use the audited ASIN for single-ASIN runs; use `Portfolio` in the [ASIN] slot for multi-ASIN runs.
2. Partial-update xlsx at `/mnt/user-data/outputs/Category_Listings_Report_[Brand]_Tier2_Updated_[YYYY-MM-DD].xlsx` — **only required if the seller explicitly asked for it**. HTML-only is the default.

The xlsx output is opt-in to keep single-chat runs inside tool budget. Ship HTML by default; generate the xlsx only when the seller asked for an "upload-ready flat file", "Listing Loader file", "partial update file", "xlsx I can upload", or a similarly explicit request. When in doubt, ship HTML and mention in the chat summary that the xlsx can be generated on request. A screenshot-mode run never produces an xlsx regardless of ask (screenshot mode has no source flat file).

### Rule 4 — Writing voice in all Claude-authored seller-facing strings

Every Claude-authored string that ends up in the HTML (opportunity-card bodies, one-thing summaries, evidence paragraphs, rewrite text, all headlines) follows these rules:

- **No em-dashes (`—`) or en-dashes (`–`) anywhere.** Use commas, periods, parentheses, or colons instead. Em-dashes are the #1 AI-tell and the seller specifically flagged them. The build script warns on any em-dashes detected in the body; treat that warning as a hard failure and fix before shipping.
- **No AI-typical phrases.** Avoid: "delve into", "let's", "it is worth noting", "in summary", "seamless", "utilize", "leverage", "unlock the power of", "navigate the landscape", "dive deep". Write like a human talking to another human.
- **Match the current listing's voice for all rewrite copy.** Before writing any title/bullet/description rewrite, read the current listing from `listing_state.title` + `bullet_1..5` + `description` in diagnostics.json. Note sentence length, warmth, vocabulary, how bullet headers are capitalised, how the seller addresses the buyer. The rewrite must read like it was written by the same person, only optimised. If the current bullets start with an ALL-CAPS lead like `KEY BENEFIT HEADER:`, preserve that convention. If bullets are sentence-case or use emoji leads, match that. The voice-matching step is concrete: read the actual current copy first, then write rewrites that could plausibly be the seller's own next draft.
- **No curly-quote HTML entities.** Write curly quotes as the actual Unicode characters (`"` `"` `'` `'`) directly in the report JSON, never as `&ldquo;` / `&rdquo;` / `&lsquo;` / `&rsquo;`. The HTML builder passes JSON strings through `html.escape()` for safety, which turns `&ldquo;` into `&amp;ldquo;`, which renders as literal text in the browser. Straight quotes (`"` `'`) are always safe. Prefer straight quotes when unsure.
- **Seller-level language in explanations.** The seller is a small business owner, not a PPC strategist. No internal jargon: no "COSMO", no "validation gate", no "dual north star", no "funnel diagnostic" (call it "how many times shoppers see your listing, then click, then buy"). Alexa Shopping and A9 can appear by name (they're Amazon's terms) and are briefly defined in the optional "A quick explanation of Alexa Shopping vs A9" section at the bottom.

### Rule 5 — Backend keyword de-duplication

Every token in the proposed backend search terms must NOT appear as a whole word in the proposed title, bullets, or description. Amazon already indexes copy terms; repeating them in backend wastes bytes.

Before writing the `backend_rewrite.proposed_value`, build a single string concatenating the proposed title + all 5 proposed bullets + proposed description, lowercase, and scan it. Every backend token you're about to add must fail a whole-word match against that concatenated string. The build script does not enforce this automatically, so do the dedup check during the per-ASIN semantic-work step (Step 4) before writing the report JSON. Hyphenated compound terms ("mother-in-law") are safe because they don't match single tokens ("mother") via whole-word regex.

Target under 240 bytes for safety (Amazon caps at 250). Prioritise high-volume SQP bucket 5 expansion queries, related recipient roles not mentioned elsewhere, and affinity/style terms from competitive white-space analysis.

## Input modes

### Mode 4 — Sophie Hub listing pull (no upload)

Runner assembles a listing payload from Sophie Hub + Keepa and passes `--listing-json`. Zero seller effort. Produces the HTML audit only — never an upload-ready xlsx, and backend search terms are unavailable. See Step 0.4 and `references/sophie-hub-pull.md`. The parser labels this `mode: 4`.

## Two upload-based input modes

The skill auto-detects which mode applies based on what's uploaded.

### Flat-file mode (primary for most sellers)

The seller downloads the Category Listings Report from Seller Central and uploads it.

- Required input: `Category_Listings_Report*.xlsm` or `.xlsx`
- Optional supporting inputs: SQP CSV, review XLSX, Xray CSV (ASINs and/or keywords), PPC search term report
- Produces: HTML audit by default; upload-ready partial-update flat file only if the seller asks for one
- Full portfolio support (up to 10 ASINs per run — see drift safeguards below)

This is the richest mode and the one most documentation focuses on. Internally the script labels this `mode: 2`.

### Screenshot mode (quick single-ASIN look)

For sellers who don't have (or don't want to download) the flat file. They screenshot the Seller Central edit-listing page and drop the image.

- Required input: clear screenshot of the edit-listing page
- Optional supporting inputs: SQP CSV for that ASIN, review XLSX for that ASIN
- Produces: HTML audit only, with copy-paste rewrite proposals
- Single ASIN only — doesn't scale to portfolio audits

Internally the script labels this `mode: 3`.

**Limitations of screenshot mode (MUST be surfaced in the HTML report):**
- OCR transcription may misread numbers, special characters, or small text
- Collapsed sections of the edit-listing page aren't captured
- Structured attributes hidden behind "Show more" tabs may appear empty when they're actually filled
- Cannot produce an upload-ready flat file — seller applies changes manually

### Mode auto-detection

Run `scripts/parse_inputs.py` (Step 1 below) and read the `mode` field from its output. That is the authoritative answer — do not decide yourself.

If the script returns `mode: null`, stop and ask the seller to provide one of the input types (Category Listings Report xlsm/xlsx, a Seller Central edit-listing screenshot, or — when Sophie Hub is connected — a listing pull via `--listing-json`, Step 0.4).

## Inputs supported (per mode)

| Input | File pattern | What it unlocks | Applies to |
|---|---|---|---|
| **Category Listings Report** | `Category_Listings_Report*.xlsm` or `.xlsx` | Base for structured-attribute audit + flat file output | Flat-file mode only |
| **Seller Central screenshot** | `.png`, `.jpg`, `.jpeg` | Single-ASIN audit input (OCR) | Screenshot mode only |
| **SQP export** | `<CC>_Search_Query_Performance*.csv` (any 2-letter marketplace prefix: `US_`, `UK_`, `DE_`, ...) | Full 5-bucket funnel diagnostic + SQP-weighted COSMO priorities | Both modes |
| **Helium 10 Review Insights** | `Helium_10_Review_Analysis_-_*.xlsx` (one per ASIN) | Customer vocabulary, objection map, star-rating impact | Both modes |
| **Helium 10 Xray (ASINs)** | `Helium_10_Xray*.csv` | Competitive benchmark, white-space positioning | Both modes |
| **Helium 10 Xray (keywords)** | `Xray_Keyword*.csv` | Market-level search volume context | Both modes |
| **PPC Search Term Report** | Campaign Manager CSV export | Account-proven converting phrases | Both modes |

All file detection happens by inspecting filenames and content. Don't ask the seller which file is which — parse whatever's there.

## Marketplace support (US, UK/EU, and others)

This skill supports **US, UK/EU, and other Amazon marketplaces**, not just the US. `parse_inputs.py` detects the marketplace from the Category Listings Report's `marketplace_id` (e.g. `A1F83G8C2ARO7P` = UK, `A1PA6795UKMFR9` = DE) and threads a `marketplace` code through the parsed JSON; `run_diagnostics.py` exposes it as `global.marketplace`. Detection **never blocks**: an unknown or missing `marketplace_id` becomes a WARNING and the marketplace is set to the raw id or `UNKNOWN`, and the audit still runs.

- **Thread it into the report.** Set the report JSON's `marketplace` field from `diagnostics.global.marketplace`. `build_html_report.py` prints it in the header meta and, for any non-US (or UNKNOWN) marketplace, renders a caveat that the US-based regulatory examples and picklists must be re-checked locally.
- **Screenshot-only mode has no `marketplace_id`.** When there is no flat file to detect from, **ASK the seller which Amazon marketplace this listing is on** before auditing, and set the report `marketplace` from their answer.
- **When detection yields `UNKNOWN`** (or an unrecognized id, surfaced as a parse warning), **ask the seller to confirm the marketplace** rather than silently assuming US.
- **Regulatory / claims caveat (non-US).** The regulatory framing throughout `references/category-families.md` and `references/amazon-picklist-values.md` (FDA, USDA organic, CPSC, FTC, FCC/UL, AAFCO) is **US-based**. Do NOT map these to invented foreign equivalents. For any non-US marketplace, flag in the report that the seller must verify benefit and compliance claims against **their own marketplace's rules and regulators** (for example UK FSA/MHRA, EU CE/UKCA marking, EU cosmetics and food regulations) rather than applying the US bodies verbatim. Keep this a caveat, never a hard block. `build_html_report.py` renders this caveat automatically for non-US marketplaces; reinforce it in any category-specific claim guidance you write.

## Execution flow

The skill ships helper scripts in `scripts/` that consolidate the heavy data work.
**Use them — don't write parsing, diagnostics, HTML assembly, or xlsx-writing code inline.**
Inline parsing/HTML assembly is what historically caused single-chat runs to exhaust tool budget.

| Script | What it does | Inputs | Output |
|---|---|---|---|
| `scripts/parse_inputs.py` | Walks `/mnt/user-data/uploads/`, detects every input type, parses the flat file (row-4 vs row-5 auto-detect), SQP (flat OR two-level header auto-detect), Reviews, Xray (ASINs and keywords), and PPC search terms. Populates `image_count` from the flat file's image URL columns. Emits one consolidated JSON. | `--uploads <dir> --out <path>` (optional `--asin <ASIN>`) | `parsed.json` |
| `scripts/run_diagnostics.py` | SQP 5-bucket funnel with correct impression-CTR math, review theme prioritization, competitive benchmark (median + percentiles + own-row exact match), white-space token analysis, PPC harvest/negate buckets, category family detection. Populates `review_count` from Xray if own ASIN is in the competitive set. | `--parsed <path> --out <path>` (optional `--asin`) | `diagnostics.json` |
| `scripts/summarize_diagnostics.py` | **One-shot dump of every load-bearing field** from diagnostics.json — listing state, SQP buckets with top 6 queries each, all differentiated review themes, competitive benchmarks + deltas, white-space + saturated terms. Replaces 4-5 exploratory JSON inspection calls with one. | `--diagnostics <path> [--asin <ASIN>]` | stdout |
| `scripts/write_flat_file.py` | Seller's flat file + rewrites JSON → PartialUpdate xlsx. Strict structured fills use anchored column match (no silent writes to the wrong column). Enforces length/byte caps; verifies after write. | `--flat-file <path> --rewrites <path> --out <path>` | updated xlsx |
| `scripts/build_html_report.py` | Report JSON → branded Sophie Society HTML. **Fails with exit 2 if any `{{PLACEHOLDER}}` is left unsubstituted** (pass `--allow-unsubstituted` only for debug). | `--report <path> --out <path>` | HTML file |
| `scripts/check_outputs.py` | Verifies deliverables exist and are well-formed. Run before `present_files`. Enforces Rule 3. Pass `--xlsx-requested` only when the seller explicitly asked for the xlsx. | `--parsed <path> --outputs-dir <dir>` | exit 0 / 2 |

### Budgeted execution loop

A single-ASIN flat-file-mode HTML-only run should fit inside **~13 bash calls** (+1 over the base for the always-on Sophie SOP read in Step 4b). Target allocation:

| Phase | Bash calls | Purpose |
|---|---|---|
| 1. Parse + diagnostics | 2 | `parse_inputs.py`, `run_diagnostics.py` |
| 2. One-shot JSON inspection | 1 | The consolidated `summarize_diagnostics.py` snippet in Step 2 below — dumps every field Claude needs for semantic work in one pass |
| 3. Reference read (detected family only) | 1 | `view` the family section in `category-families.md` using its line-range index |
| 4. Per-ASIN semantic work | 0 | Pure reasoning over the JSON and family section — no bash calls |
| 5. Assemble report JSON | 1-2 | `create_file` for `/tmp/report.json` (and `/tmp/rewrites.json` only if xlsx was asked for) |
| 6. Build HTML (+ xlsx if asked) | 1-2 | `build_html_report.py` (and `write_flat_file.py` if opt-in triggered) |
| 7. Verify + present | 1 | `check_outputs.py` |

Remaining headroom (~3 calls) is reserved for recovery — re-inspecting a specific JSON field, re-reading a reference if a borderline COSMO dimension is ambiguous, fixing a placeholder leak. **If you find yourself 8 calls in and still exploring the diagnostics JSON, stop exploring — write the report with what you have.** Defensive reading is the #1 cause of budget exhaustion.

Multi-ASIN runs add ~2 calls per extra ASIN (extra inspection + extra report-JSON assembly). Hard cap 10 ASINs per run.

### Step 0.4 — Optional: pull the listing from Sophie Hub (MCP mode)

**This step is OPTIONAL and never blocks the run.** It is model-facing prose: YOU (the runner) make these MCP calls. It is not part of any Python script. If anything goes wrong at any point, fall back to manual upload with no error (§6 ladder).

**The full procedure, with the exact tool calls and the traps, is in `references/sophie-hub-pull.md`. Read it before running this step.** What follows is the summary.

**Detect availability first (do not assume a GUID).** Look for the Sophie Hub tool set by tool NAME — `list_stores`, `discover_amazon_reports`, `get_amazon_report_data`, `get_product_catalog`, `get_sqp_metrics`, `query_ppc`. The server prefix changes per session. If they are absent, silently use manual mode and skip this step (case (a)).

> `verify_session` appears in older references but was NOT present in the Sophie Hub tool set as of September 2026. **Do not gate the flow on it.** Call `list_stores` first; an auth error there is your case (b) signal.

#### There is no Category Listings Report in Sophie Hub

This is the thing to understand before writing any code against this path. `parse_inputs.py` mode 2 requires a Seller Central **Listing Loader workbook** (`::record_action` in row 4/5, `contribution_sku`, `item_name[...]`, `bullet_point[...]#n`). **No S3 report produces that shape.** The closest, `GET_MERCHANT_LISTINGS_ALL_DATA`, is a flat 30-column TSV with no bullets, no `generic_keyword` and no structured attributes; handing it to the parser returns `No template sheet found`.

So MCP mode does **not** save a fake CLR into the uploads dir. It assembles a **listing payload** and passes it via `--listing-json` (**mode 4**).

#### The pull

1. **`list_stores(compact=true)`** — match the brand. Zero stores → case (c), fall back to manual. Several → ask which.
2. **Pick the ASIN.** If the seller named one, use it. Otherwise rank by revenue with `list_top_products(store, days=30, limit=5, compact=true)` and confirm the pick before auditing. Never guess a variation — `relationships` in the catalog payload gives the parent.
3. **Listing content:**
   - `get_product_catalog(seller_id, asin, marketplace_id, fields=["attributes","summaries","salesRanks","relationships"])` for title, description, structured attributes, BSR, parentage.
   - `keepa_get_product(asins=[ASIN])` for **the bullets**. ⚠️ **`get_product_catalog` flattens `bullet_point` to a single value.** On a live test it returned 1 bullet where the listing had 6, and the missed bullets contained a compliance risk. Always take bullets from Keepa. `parse_inputs.py` warns on ≤1 bullet; do not rely on the warning.
4. **SQP:** `list_sqp_windows(store)` first — most stores carry BOTH weekly and monthly, and `get_sqp_metrics` returns `needs_selection` if you omit `cadence`. Then `get_sqp_metrics(store, asin, cadence="MONTH", start_date, end_date)`. **Compute the CTR-vs-market comparison (see §Step 4.1 below).**
5. **PPC:** `query_ppc(store, view="search_terms", asins=[ASIN], days=60)`. Rows flagged `shared: true` are full ad-group metrics across `co_asins`, not the ASIN's split — say so before quoting one.
6. **Reviews:** `Helium10:get_asin_review_analysis(asin, marketplace)` — see the correction below.
7. **Competitors:** `Helium10:get_listing_details` / `search_competitors_by_asin` / `compare_listings`. Normalise the result into the competitors-JSON contract (`references/sophie-hub-pull.md`) and pass `--competitors-json`. It feeds the SAME benchmark code an uploaded X-Ray feeds, so no analysis changes. An uploaded X-Ray always wins if both are present. **Do not skip this** — without it there is no title-length, price-percentile or review-count benchmark, which was the largest quality gap in MCP-mode runs before v4.3.
8. **Write the listing JSON** (contract in `references/sophie-hub-pull.md`) and run:

```bash
python3 scripts/parse_inputs.py \
    --uploads /mnt/user-data/uploads \
    --listing-json /tmp/listing.json \
    --asin B0XXXXXXXX \
    --out /tmp/parsed.json
```

`--uploads` is still scanned, so anything the seller uploaded is parsed alongside the pull. **Hybrid is the normal case.** An uploaded Category Listings Report beats the listing JSON (it carries backend terms and supports the xlsx) and the parser warns when both are present.

#### CORRECTION — Helium 10 is NOT upload-only

Earlier text in this skill says Helium 10 Review Insights and X-Ray are unavailable via MCP. **That is true of Sophie Hub and false of the session.** The Helium 10 MCP is normally connected alongside Sophie Hub and exposes `get_asin_review_analysis` (the Review Insights export: topics, mention counts, star-rating impact, snippets, ~6-month trend) and the competitor tools listed above. Skipping them is the single biggest quality gap in an MCP-mode run. Ask for uploads only if the Helium 10 tools are absent.

#### Two hard gaps — surface BOTH in the pre-run data check

1. **Backend search terms are not exposed by any surface** — not Catalog Items, not the merchant-listings TSV, not Keepa. You cannot audit the current value, and a proposed backend has no baseline to dedupe against. Tell the seller to check Seller Central before overwriting. This is real: a CLR-based run on the same ASIN found 282 bytes against a 250-byte cap with two misspellings, all invisible via MCP.
2. **No upload-ready flat file.** SP-API has no Listing Loader template to partial-update. `write_flat_file.py` hard-exits in mode 4. If the seller wants the xlsx, ask them to download the Category Listings Report and re-run in mode 2.

**Graceful-fallback rules (unchanged, hard requirement):** (a) tools absent → manual, no error; (b) not authenticated → manual; (c) zero stores → the message in §6 + manual; (d) any tool error or timeout → manual for that file, never hard-fail; (e) never substitute a non-Sophie-Hub connector for Amazon-native data (the Helium 10 MCP is not a substitute — it is the documented source for third-party data). **The skill must always be completable via manual upload alone.**

### Step 0.5 — Ensure dependencies

Before running any script, install the Python deps the scripts need (`openpyxl`, `pandas`, `numpy`):

```bash
pip install -r requirements.txt || pip install openpyxl pandas numpy
```

If a script later fails with `ModuleNotFoundError`, run the command above and retry.

### Step 1 — Inventory and parse all inputs (one bash call)

```bash
python3 scripts/parse_inputs.py \
    --uploads /mnt/user-data/uploads \
    --out /tmp/parsed.json
```

(Add `--asin B0XXXXXXXX` to filter the flat file to a single target ASIN — useful when auditing one product out of a large catalog.)

The script prints a mode + input summary to stdout. Read that to confirm expected inputs were found. If mode is `null` or errors are reported, stop and ask the seller to provide the missing inputs (Category Listings Report or edit-listing screenshot).

### Step 2 — Run diagnostics (one bash call)

```bash
python3 scripts/run_diagnostics.py \
    --parsed /tmp/parsed.json \
    --out /tmp/diagnostics.json
```

The script prints a per-ASIN summary with bucket counts, review theme counts, and the title-chars-vs-median gap.

**Do not reimplement the SQP bucketing, review prioritization, or competitive benchmarking inline.** If a bucket looks wrong, the bug is in `run_diagnostics.py` — fix the script once, not every run.

**Next — the one-shot inspection call (do not skip this).** Immediately after diagnostics, run:

```bash
python3 scripts/summarize_diagnostics.py \
    --diagnostics /tmp/diagnostics.json \
    --asin B0XXXXXXXX    # omit for all ASINs; include for single-target runs
```

This dumps everything Claude needs for semantic work — listing state, structured attribute summary, SQP funnel with top queries per bucket, all differentiated review themes, competitive benchmarks with deltas, white-space + saturated terms, and PPC signals if present — in one pass. Read the output once, and all subsequent work is reasoning over what's already in context.

**Do not** follow this with exploratory `python3 -c "import json; ..."` calls to re-inspect fields. Everything load-bearing is in the summarize output. If you find yourself wanting more detail than the summary showed, either (a) the summarize script should be improved — note it for feedback, or (b) you're exploring defensively and should stop.

### Step 3 — Reconcile ASINs and confirm audit set

Print a reconciliation table before analysis:

```
Input coverage by ASIN:
  B0XXXXXXXX: flat file ✓ | SQP ✓ | reviews ✓ | PPC (via ads report) ✓
  
⚠️ Mismatches detected:
  - SQP data only covers B0XXXXXXXX. Other ASINs will get COSMO + structured audit only.
```

The diagnostics JSON's `global.asins_processed` is the authoritative list. Continue with warnings — don't block on reconciliation issues.

### Step 4 — Per-ASIN analysis (semantic work Claude does over the JSON)

#### Step 4.1 — Click-rate vs market (MANDATORY whenever SQP is present)

**`run_diagnostics.py` already computes this** — it is in the diagnostics output as `overall_impr_ctr_pct`, `market_overall_impr_ctr_pct`, `overall_click_cvr_pct` and `market_overall_click_cvr_pct`, and it prints on the diagnostics summary line. Nothing here is a new calculation. What goes wrong is that the runner reads the share columns instead and never surfaces these, so the report tells the seller to chase different keywords when the actual problem is the main image and the first 40 characters of the title. **Surface them.**

The four figures, and how to recompute them per query if you need the detail:

| | formula |
|---|---|
| your CTR | `asin_click_count / asin_impression_count` |
| market CTR | `click_through_rate` (already the market's) |
| your CVR | `asin_purchase_count / asin_click_count` |
| market CVR | `conversion_rate` (already the market's) |

Then aggregate across the top queries by impressions and report **both ratios**.

Verified on a live run: mode 4 on B08W2H1PNM returned **0.481% CTR against a market 1.228%** (0.39x) and **4.441% CVR against a market 3.791%** (1.17x). Shown often, converts above market, loses everything at the click. An independent CLR-based run on the same ASIN two months earlier reached the same conclusion from different windows (0.81% vs 1.66%), which is the strongest available evidence that the MCP path lands on the right diagnosis.

State the aggregate in the report's opening section, in plain language ("about half the clicks the market gets, on searches where you actually convert better than average").



For each ASIN in the diagnostics JSON, Claude does the **judgment** work — the parts that can't be scripted:

0. **Read the current listing first, then match its voice.** Before anything else, look at `listing_state.title`, `listing_state.bullet_1` through `bullet_5`, and `listing_state.description` in the diagnostics JSON for this ASIN. Note: sentence length, warmth, use of ALL-CAPS headers on bullets, how the seller addresses the buyer ("she", "you", "her"), vocabulary level, how specific they are. Every rewrite you write must sound like it could have been the seller's own next draft. This is a hard requirement, per Rule 4. If the current bullet 1 starts with "NEW BEGINNINGS GIFTS FOR WOMEN:" in ALL CAPS, your proposed bullet 1 starts with an ALL CAPS header too, just a better one.
1. `view` the detected category family section in `category-families.md` (use the line-range index at the top of that file). Don't read the whole file.
2. Score the COSMO 15 dimensions semantically against the listing state. `cosmo.md` has colocated definitions + rubric. Judgment work — no script can replace it. In the report JSON, use seller-friendly names for each dimension (e.g. `"Who it's for"`, not `"Audience (COSMO dim 3)"`).
3. Reason over the 5 SQP buckets to identify priority rewrite targets:
   - Bucket 4 vocabulary = defend in title
   - Bucket 2 CTR problems = title/image-level fix (copy helps at margin)
   - Bucket 3 CVR problems = bullets + description fix (this is where rewrites move the needle)
   - Bucket 5 expansion = backend search terms + new structured-attribute coverage (often the biggest wins)
4. Reason over review themes: lean into `positive_differentiated`, pre-empt `negative_differentiated` (paraphrase snippets, never lift verbatim).
5. Reason over competitive benchmark: title length vs median, image count vs median, white-space terms to claim, saturated terms to avoid leading with.
6. Reason over PPC (if present): `ppc.harvest` terms are account-proven converters — prioritize them in backend and title; `ppc.negate` terms are wasted spend — surface them in the HTML.
7. Generate rewrite proposals (title, 5 bullets, description, backend, strict-tier structured fills). Use the category family's bullet structure from `category-families.md` as a starting frame, but defer to the current listing's voice over the abstract structure.
7b. **Emit the structured product-facts block (for downstream image generation).** The hero-image and secondary-image skills that run after this audit need deterministic product facts, not prose they have to re-parse. Build a `product_facts` object on the ASIN with `pack_count`, `colour`, `material`, and `on_pack_text`. Pull `colour` and `material` from `listing_state.structured` (the raw Category Listings Report attribute values), using the full value, never the truncated cell text (the report sometimes stores a cut-off value such as `Non` for what is really `Non-toxic silicone`; correct it from the copy and note the correction). `on_pack_text` is the one fact that CANNOT be derived from listing or report data: it is vision-only, read off the actual product photo. Always emit `on_pack_text: null` and put a `STUB:` note in `product_facts.notes.on_pack_text` telling the image skill to read it from the hero photo and never fabricate it. Never invent any value, emit `null` plus a note when a fact is genuinely missing. The script renders this object as both a human-readable table and a copy-pasteable JSON object.

   **Pack-count reconciliation (do this at the source, surface it, never resolve silently).** The Category Listings Report carries a unit-count attribute (look in `listing_state.structured` for `unit_count`, `item_package_quantity`, or `number_of_items`). The title and bullets carry an implied pack count (for example "2 Pack", "Set of 3", "Pack of 2"). Compare the two:
   - If they agree, set `pack_count` to that value and `has_conflict: false`.
   - If they disagree (for example `unit_count = 1` in the report but the title says "2 Pack"), DO NOT silently pick one. Set `has_conflict: true`, set `pack_count` to the value you judge correct, write a one-sentence `rationale` for why, and write a `conflict_note` that names BOTH values and tells the seller which detail-page field to fix.
   - **Default reconciliation rule:** the pack count stated in the title and bullets wins over the report's `unit_count`, because the title is the buyer-facing promise of what ships and is the harder thing to get wrong. The exception is when the title number is plainly a measurement or model number rather than a quantity (for example "2 inch", "Model 3"), in which case it is not a pack count and the report value stands. When neither source states a pack count, emit `pack_count: null` with a note. State whichever rule you applied in `pack_count_source`.

8. **Title compliance and the shorter-title option** (see `references/title-compliance.md`). Run the hard title lint on the proposed title: 200-char cap, no ALL-CAPS words (acronyms, units, and size codes excepted), no word more than twice (prepositions, articles, conjunctions exempt), no banned characters (`! $ ? _ { } ^ ¬ ¦`) unless inside the brand name, conditional characters (`~ # < > *`) only for product IDs or measurements. Fix any breach in the performance title. Then build a second compliant title that uses as much of the 75 characters as it productively can. Decide brand placement from SQP brand demand: by default keep the brand first, but if branded queries (query text contains the brand name) drive negligible purchases, raise an advisory to de-emphasize or drop the brand to free space for the top generic keyword (never drop it automatically, and always keep it when there is no SQP file, Brand Registry and category rules often require brand-first and SQP is backward-looking). Then give the single most important generic (non-branded) keyword the most prominent position and its full phrasing (pull that lead keyword from SQP bucket 4, PPC harvest terms, or the highest-volume relevant query). Add one differentiator and size or variant, then keep adding value-bearing terms until you approach 75 characters. Budget vs quality gate: push toward 75 only while each added token increases keyword coverage, shopper clarity, or relevance; stop and accept a shorter title if the next token would repeat a word beyond the twice limit, read as filler, hurt readability or CTR, or dilute the lead keyword. Never pad to hit 75, quality and keyword efficiency beat raw length. Attach it to the ASIN via `has_title_compliance` + the `title_compliance_*` fields (put the final char count in `title_compliance_chars`). Both titles must pass the lint. This is additive, the performance title is unchanged.
9. **De-duplicate the backend search terms** per Rule 5: concatenate the proposed title + all 5 proposed bullets + proposed description, lowercase it, then check every proposed backend token against that string with a whole-word match. Drop any duplicates. Target under 240 bytes.
10. **Run the Step 5 validation gate** per field. Only pass fields with `passed_gate: true` to the xlsx writer (if generated).

**Reminder — Rule 2:** every number in the HTML traces to the diagnostics JSON (`listing_state.title_chars`, `listing_state.bullet_lengths`, `competitive.benchmarks.*`, etc.). Never eyeball-count from images.

### Step 4b — Sophie Society image + A+ Premium recommendations (ALWAYS-ON, NO EXCEPTIONS)

Every ASIN in the HTML MUST include three additional blocks, in this order, rendered after the rewrite section and before the structured attributes block. Source of truth is `references/sophie-society-image-and-aplus-sops.md`. Read it on every run.

**Block 1 — Main image recommendations.** Screen Sophie's 15 CTR tactics against the current main image + review themes + competitive title vocabulary. A tactic fits when (a) the current main image is missing it, (b) it matches a review-driven positive or a competitor-title-vocab signal, and (c) it doesn't conflict with Amazon's strict main-image rules (85%+ product fill, pure white background, no CTA text). Rank the top 3 to 6 with product-specific mockup direction. Emit as an HTML table with columns: Rank / Sophie tactic / Product-specific mockup / Why this ASIN. Include a "run as an A/B test via Amazon Manage Your Experiments" line at the bottom.

**Block 2 — Secondary image sequence.** Emit Sophie's fixed 7-slot table exactly. Slot 1 = primary image (references block 1). Slots 2 and 7 = lifestyle bookends (opening emotional hook + closing bookend). Slots 3, 4, 5, 6 = infographics; slot 3 is always Main Features/Benefits. For slots 4, 5, 6 choose 3 infographic types from Sophie's 20-type taxonomy that answer the top-3 purchase questions implied by review themes + competitive signals. Write per-slot content with product-specific detail, every text overlay under 8 words. Include the consistency style note at the bottom (one font, one icon set, warm neutral + 1 accent).

**Block 3 — A+ Premium module plan.** Draft the 7-module Sophie Pro structure with exact Seller Central module names (Premium Full Image, Premium Full Video, Premium Navigation Carousel, Premium Hotspots 1, Premium Q&A, Premium Comparison Table 1 or 3). Pull Q&A questions from the negative-review themes. Pull Comparison Table columns from the top-5 comps in Xray OR from the seller's own catalog if cross-sell is more valuable. Enforce Sophie's per-module character limits. Emit as an HTML table with columns: # / Sophie module + Seller Central name / Product-specific content plan / Copy limits. Include the Limited Premium A+ 5-module fallback note at the bottom.

**Where these blocks land in the report JSON (IMPORTANT, placement fix).** Combine all three blocks, in order Main → Secondary → A+, into a single raw-HTML string and emit it in the dedicated `sophie_recommendations_html` field on the ASIN (documented in the Step 8 schema). The build script renders it in its own always-present slot after the rewrites and before the structured attributes. **Do NOT prepend or route these into `strict_structured_block`.** In this skill `strict_structured_block` is only a fallback: whenever `strict_structured_rows` is present (the preferred path), the build script overwrites `STRICT_STRUCTURED_BLOCK` and any raw HTML you put there is silently dropped. Use `sophie_recommendations_html` so the blocks always render.

Use these exact `<h4>` headings inside the string so the Step 9 enforcement grep can confirm all three are present: `Main image recommendations`, `Secondary image sequence`, `A+ Premium module plan`.

**Do not skip. Do not ask.** These blocks run every time, silently, without consulting the seller. If any block would otherwise be empty, write "current stack is on target because X, no changes recommended" and cite the reason from diagnostics. Empty sections read as skipped work. There is no scenario where the skill omits any of the three blocks, not for time budget, not because the seller's message was short, not because the ASIN is well-optimized, not because the seller didn't name the blocks. Enforcement: the Step 9 grep check fails the run if any of the three headings is missing from the built HTML.

### Step 5 — Pre-shipping validation gate

For each proposed rewrite (title, each bullet, description, backend search terms, each structured attribute):

1. Score the current field on relevant COSMO dimensions + A9-relevant metrics
2. Score the proposed field on the same
3. **Ship to flat file only if:**
   - Proposed scores strictly higher on COSMO, OR
   - Fills a confirmed structured-attribute gap (empty field getting populated with verified value), OR
   - Fixes a specific SQP-identified funnel problem (addresses a CTR-problem or CVR-problem query)
   - AND does not degrade A9-relevant score (priority keyword coverage maintained, title still includes high-volume head terms, backend terms not shorter than before)
4. If proposed rewrite fails the gate: leave current copy in the flat file; surface the proposed rewrite in the HTML under "Alternative phrasing to consider — current copy retained for better overall score"

Show before/after scores in the HTML for every rewrite. "Title: current 14/30, proposed 20/30, +6 intent dimensions covered. A9 keyword coverage maintained (8 priority keywords → 9)."

### Step 6 — Handle "nothing to change" gracefully

Before generating rewrites for an ASIN, check if the listing is already strong:

- COSMO score >= 25/30 (or equivalent for N/A-adjusted max), AND
- No SQP funnel problems worth flagging (no queries in Buckets 1-3 above threshold), AND
- No review-driven objections above the "differentiated weakness" bar, AND
- No structured attribute gaps

If all four are true, produce the HTML with methodology and scorecards but a "No changes recommended — this listing is already well-optimized" summary per ASIN. Don't force synthetic rewrites. Unlikely case in practice but important for credibility when it happens.

### Step 7 — Structured attribute strict vs advisory tiers

Every structured attribute recommendation gets classified:

**Strict tier (auto-filled in flat file):** only when the exact word or value is unambiguously present in the title or bullets (not buried in description). Examples: `dosage_form: Gummy` requires "gummy" or "gummies" in title. `diet_type: Vegan` requires "vegan" as a standalone word in title or bullets. These are observable facts, not claims. In the report JSON, emit these as `strict_structured_rows` (`{field, current, proposed, evidence}`) so the HTML renders the Field/Current/Proposed/Evidence table reliably, do not hand-write the table HTML.

**Advisory tier (HTML only, NOT written to flat file):** any value that involves health/benefit claims, safety certifications, or product attributes requiring seller verification. Examples: `recommended_uses_for_product: Sleep Aid`, `material_feature: Non-GMO` (unless already claimed in copy).

For advisory-tier suggestions, the HTML must:
- List the suggested values clearly under "Structured fields to add manually — seller to confirm before applying"
- Call out the risk associated with each (FDA for supplement uses, false advertising for unverified material claims, etc.)
- Explicitly note "these are NOT in the flat file — seller must add them via Seller Central if relevant"

**Verified / not-relevant tier (informational only):** emit the REMAINING category-relevant attributes — the ones that are already correct on the listing, and the ones that are not relevant for this category — as `verified_structured_rows`, a list of `{field, current, status}` objects. `status` is a short label such as `"Already correct"` or `"Not relevant for this category"`, optionally with a brief reason (e.g. `"Already correct — 'vegan' present in title"` or `"Not relevant for this category"`). These rows are purely informational: no `proposed` value, no Copy buttons. They render inside the same structured-attributes section but in a collapsed-by-default accordion the seller can expand. The intent is that the report shows the FULL category-relevant attribute set split across the three buckets — safe-to-apply (`strict_structured_rows`), needs-verification (advisory), and already-correct/not-relevant (`verified_structured_rows`) — so nothing silently disappears. The strict and advisory buckets keep their existing behavior unchanged. Backward compatible: if you emit no `verified_structured_rows`, the accordion does not render.

See `references/category-families.md` for which attributes are strict vs advisory per family.

### Step 8 — Write outputs

Produce two files (flat-file mode) or one (screenshot mode):

**8a. Branded HTML report** — built by the HTML report script. Assemble a report JSON with all the judgment content (COSMO scores, rewrites, evidence annotations, top opportunities, priority rankings, pre-built SQP/review/competitive HTML blocks), write it to `/tmp/report.json`, then invoke:

```bash
python3 scripts/build_html_report.py \
    --report /tmp/report.json \
    --out "/mnt/user-data/outputs/Listing Juice - [ASIN] - [Brand] - $(date +%Y-%m-%d).html"
```

The script handles all HTML scaffolding, CSS, conditional blocks, per-ASIN layout, and Sophie Society branding. You don't write HTML directly; you write JSON. See the docstring of `build_html_report.py` for the full report JSON schema and an example.

**Inputs to the report JSON that you must produce (judgment work):**

Top-level report fields:
- `brand`, `date`, `mode`, `is_screenshot_mode`, `has_flat_file_output`
- `header_subtitle`: free-form product-type + ASIN string for the header subtitle
- `headline_pill_class`, `headline_pill_text`: the short pill above the one-liner (use `"ctr"` for orange, `""` for navy). Text like `"CTR is the issue"` or `"Healing claims need to go"`.
- `headline_one_liner`: one punchy sentence (seller-friendly, no jargon, no em-dashes)
- `headline_plain`: 2-4 sentences of plain-language summary with the key numbers
- `top_opportunities`: array of **exactly 3** objects `{rank, primary, category, title, body, why_this_one}` — Claude writes the text, script renders the cards. `primary: true` on the #1 opportunity makes it orange.
- `sample_alexa_queries`: 5 example seller-voice queries to test in Alexa Shopping (plain strings, no quotes inside)
- `apply_steps`: array of `<strong>...</strong> Plain sentence continues.` strings, ordered. Each step is one ordered-list `<li>`.
- `input_inventory`: array of `{source, status (ok|med|low), status_label, unlocked}` rows

Per ASIN (in `asins` array):
- `asin`, `product_name_short`, `asin_chip_text` (optional orange chip on the summary), `nothing_to_change`
- `one_thing_headline`, `one_thing_body`, `one_thing_lever`: the peach-gradient "What matters for this listing" card
- `has_compliance_flag` + `compliance_flag_title` + `compliance_flag_body`: optional critical-red callout at the top of the ASIN body
- Funnel fields (`funnel_impressions`, `funnel_clicks`, `funnel_ctr`, etc.) with `_class` fields controlling orange/green colouring: `"problem"`/`"warn"` for below-market, `"strength"`/`"good"` for above-market, `""` for neutral
- `what_we_see_rows`: pre-built `<li>` block for the "What we're looking at" kv-list. Claude assembles this from diagnostics JSON (title, category, price, reviews, rating, BSR, images, bullet lengths, backend byte count).
- Optional title-compliance layer: `has_title_compliance`, `title_compliance_intro`, `title_compliance_chars`, `title_compliance_value`, `title_compliance_note`. The shorter ~75-char title shown alongside the performance title. Omit all to keep prior behavior.
- Optional structured product-facts layer: `product_facts` (object with `pack_count`, `pack_count_source`, `colour`, `material`, `on_pack_text` (always `null`), `has_conflict`, `conflict_note`, `rationale`, and `notes`). Deterministic facts for the downstream hero/secondary image skills, emitted by the script as both a human table and a copy-pasteable JSON object. `on_pack_text` is vision-only, always `null` here with a `STUB:` note. The pack-count conflict between the report `unit_count` and the title is reconciled per Step 4 item 7b and surfaced visibly. Omit the whole object to keep prior behavior.
- `title_rewrite`, `bullet_rewrites` (list of 5), `description_rewrite`, `backend_rewrite`: rewrite objects with `{field_name, current_value, current_meta, proposed_value, proposed_meta, evidence_text, has_assumption, assumption_text, tier_class, did_not_ship}`. `current_meta` / `proposed_meta` is an optional parenthetical like `"104 chars"` or `"207 bytes, no repetition of title/bullet/description words"`.
- `sophie_recommendations_html`: ALWAYS-ON (Step 4b). A single raw-HTML string containing all three Sophie Society blocks in order, Main image recommendations, then Secondary image sequence, then A+ Premium module plan, each under its exact `<h4>` heading (`Main image recommendations`, `Secondary image sequence`, `A+ Premium module plan`). The script renders it in a dedicated slot after the rewrites and before the structured attributes, gated by `HAS_SOPHIE_BLOCKS`. Do NOT put these blocks in `strict_structured_block` (it is overwritten when `strict_structured_rows` is present). Required on every run.
- `strict_structured_rows`: PREFERRED for the "safe to apply now" attributes. A list of `{field, current, proposed, evidence}` objects, the script renders the Field/Current/Proposed/Evidence table (with a copy button on each proposed value) every run. Use this so the table never regresses to free-form text. `strict_structured_block` (pre-built HTML) is a legacy fallback only used when no rows are supplied.
- `advisory_structured_block`, `claims_to_verify_list`: pre-built HTML fragments (the advisory callout and `<ul>` list)
- `verified_structured_rows`: OPTIONAL informational bucket — the category-relevant attributes that are already correct or not relevant for the category. A list of `{field, current, status}` objects (`status` is a short label like `"Already correct"` or `"Not relevant for this category"`, optionally with a brief reason). The script renders these as a Field/Current/Status table (no proposed column, no Copy buttons) inside a collapsed-by-default accordion in the same structured-attributes section. Omit or leave empty to render nothing (backward compatible).
- `sqp_bucket_tables`, `review_analysis`, `competitive_analysis`: pre-built HTML for the three diagnostic "More detail" sections
- `cosmo_rows`: 15 rows with friendly dimension names (e.g. `"Function / what it does"`, `"Who it's for"`, not `"Dimension 3 — Audience"`). Use `null` for N/A scores.
- `alexa_score` (current), `alexa_proposed_score`, `alexa_total` (denominator, 26 or 30)

See the docstring of `build_html_report.py` for the full schema (the docstring is a schema template with placeholder values, not a specific prior run).

**8b. Partial-update flat file** (OPT-IN — only run when the seller explicitly asked for an upload-ready xlsx; otherwise skip this step entirely) — built by the writer script. A flat file holds one title per ASIN, so first ask the seller which title to write: the performance title or the compliant ~75-char title. If they do not say, default to the performance title and note in the HTML that the short version is available on request. Then assemble a rewrites JSON with Claude's decisions:

```json
{
  "brand": "<Brand>",
  "asins": {
    "<ASIN>": {
      "title":       {"value": "<new title>", "passed_gate": true},
      "bullets":     [{"value": "<b1>", "passed_gate": true}, ...5 total],
      "description": {"value": "<new desc>", "passed_gate": true},
      "backend":     {"value": "<backend terms>", "passed_gate": true},
      "strict_structured_fills": {
        "<attr_id_substring>": "<value>",
        ...
      }
    }
  }
}
```

Write this JSON to `/tmp/rewrites.json`, then invoke the writer:

```bash
python3 scripts/write_flat_file.py \
    --flat-file /mnt/user-data/uploads/Category_Listings_Report_*.xlsm \
    --rewrites /tmp/rewrites.json \
    --out "/mnt/user-data/outputs/Category_Listings_Report_[Brand]_Tier2_Updated_$(date +%Y-%m-%d).xlsx"
```

The script enforces all the field-length, byte-limit, strict-tier-only-if-empty, and forbidden-column rules. It also verifies the output after writing. You don't reimplement any of that inline.

Fields with `passed_gate: false` are omitted — those cells stay blank, PartialUpdate preserves the existing value. Advisory-tier structured fills must NOT be in the JSON (surface them only in the HTML).

**Screenshot mode only:** no flat file available regardless of ask. The HTML includes a "How to apply these changes" section with step-by-step Seller Central navigation.

**Default (flat-file mode, the normal flow):** same treatment — the HTML closes with a "How to apply these changes" section walking the seller through Seller Central → Edit Listing. Do not prompt the seller to choose an xlsx; the branded HTML is the stated deliverable.

### Step 9 — Verify outputs, present files, short summary

Run the output completeness check (enforces Rule 3). Pass `--xlsx-requested` only if
the seller explicitly asked for the partial-update xlsx this run:

```bash
python3 scripts/check_outputs.py \
    --parsed /tmp/parsed.json \
    --outputs-dir /mnt/user-data/outputs
    # add --xlsx-requested if the seller asked for the upload-ready flat file
```

Exit 0 = safe to call `present_files`. Exit 2 = missing HTML, undersized HTML, or
unsubstituted placeholders (and, if `--xlsx-requested`, a missing xlsx). Fix the gap
before ending the chat.

Additionally, before calling `present_files`, run this grep-based sanity check to enforce the always-on Step 4b rule (the three Sophie blocks now always render via the dedicated `sophie_recommendations_html` slot). Point it at the HTML you just built:

```bash
python3 -c "
import glob, sys
files = sorted(glob.glob('/mnt/user-data/outputs/Listing Juice*.html'))
if not files:
    sys.stderr.write('FATAL: no Listing Juice HTML found\n'); sys.exit(2)
t = open(max(files)).read()
required = ['Main image recommendations', 'Secondary image sequence', 'A+ Premium module plan']
missing = [r for r in required if r not in t]
if missing:
    sys.stderr.write(f'FATAL: Sophie SOP blocks missing from HTML: {missing}\n'); sys.exit(2)
print('Sophie always-on blocks: OK')
"
```

If any block is missing, do not present. Return to Step 4b, add the missing block to `sophie_recommendations_html`, rebuild, and re-check.

Once the check passes, call `present_files` with the HTML first (so it opens by default).
If the xlsx was generated, pass it second.

Then write a brief chat summary (under 300 words):
- Total ASINs audited, data sources used, detected mode (report the script's `mode` value)
- **State that each ASIN section includes Sophie's Main-Image screen, 7-slot Secondary-Image sequence, and 7-module A+ Premium plan.** Report these as a matter-of-fact part of the deliverable, not an add-on the seller lucked into or an optional extra; do not phrase it as "I also included..." or "would you like me to add...".
- Top 3 highest-impact recommendations across the portfolio
- How to apply, picking the line that matches what was produced:
  - HTML only (the normal flow): "Open the HTML for full context. Copy-paste the proposed rewrites into Seller Central → Edit Listing for each ASIN." Do not turn this into a question about output formats.
  - HTML + xlsx: "Open the HTML for full context. When ready, open the xlsx, review rows marked PartialUpdate, and upload via Seller Central → Catalog → Add Products via Upload."

## Portfolio drift safeguards (multi-ASIN runs only)

Skip this section on single-ASIN runs (`--asin` filter set). For 2+ ASINs:

- Process each ASIN fully before starting the next (don't batch COSMO scoring up-front)
- Hard cap of 10 ASINs per run
- Before final HTML write: scan proposed rewrites for duplicate/near-identical bullets across ASINs; flag affected ASINs in the HTML as "rewrites may need additional evidence — review before applying"

## Critical constraints

- **Evidence-grounded only.** Every recommendation in the HTML must cite its data source inline — which SQP query drove the title change, which review theme drove the bullet 4 rewrite, which category-family rule drove the structured attribute fill. No unexplained changes.
- **Partial update mode only.** When the xlsx is generated it is always `PartialUpdate`, never `Create or Replace`. Cannot accidentally overwrite populated fields the seller cares about.
- **Voice authenticity.** Paraphrase review snippets — don't lift full sentences. Listing copy should sound like the brand, not like a customer. Customer sentences include markers ("I tried...", "my husband...") that read oddly in product copy.
- **Category-regulatory softening** per `references/category-families.md`. FDA softening for supplements ("supports," not "treats"), cosmetics-safe language for beauty, CPSC safety framing for children's products, no medical/healing claims on jewelry accessories.
- **Honest about data limits.** If a data source is missing, the HTML says so — no pretending a funnel diagnostic exists without SQP.
- **Graceful per-ASIN skip.** If one ASIN has review data but another doesn't, analyze each with what's available. Don't hold up the portfolio for one missing file.
- **Never invent product facts.** Every claim in the rewrite must be traceable to the current listing or input data. Unverifiable claims go to the "Claims to verify before applying" section in the HTML, not into the flat file.

> Note for the HTML report: surface measurement honesty (A9 is trackable via SQP reruns, Alexa Shopping is directional via Sponsored Prompts growth + manual query testing) and run-to-run variance (structural numbers are stable; rewrite copy is semantic and may vary) in the HTML preamble. These are seller-facing disclosures handled by `build_html_report.py`, not execution instructions for Claude.

## References — read only what's needed

**Sections marked ALWAYS-ON must be loaded on every run, no matter the mode.** Other references are on-demand.

**ALWAYS-ON:**
- `references/sophie-society-image-and-aplus-sops.md` — consolidated Sophie Society SOPs for Main Image, Secondary Image, and Premium A+ content. Feeds Step 4b (required every run, both modes). Snapshotted from Sophie Society Notion; refresh when the SOP changes.

**Default reading pattern for flat-file mode (most runs):**
1. `references/flat-file.md` — only if you hit a flat-file validation issue or need the column-map
2. `references/category-families.md` — ONLY the detected family's section via the line-range index at the top of that file, then `view(path, view_range=[start, end])`. Do not read the whole file.
3. `references/diagnostic-rules.md` — only if a bucket result looks wrong and you need to sanity-check the math
4. `references/cosmo.md` — only for borderline dimension scoring
5. `references/rewrite-rules.md` — optional voice + strict/advisory tier refresher
6. `references/input-parsing.md` — only if a non-flat-file input parses oddly
7. `references/amazon-picklist-values.md` — only when filling a picklist attribute and you need to validate the value
8. `references/title-compliance.md` — the hard title rules (the lint applied to every proposed title) plus the optional shorter ~75-char title layer. Read whenever writing or checking a title.

**Screenshot mode:** `input-parsing.md` § OCR limitations + detected family section. Skip `flat-file.md`.

Defensive reading of the full reference set is the #1 cause of budget exhaustion — skip anything not triggered by the list above.

> HTML templates live at `scripts/html_templates/{base,per_asin,rewrite}.html`. Report JSON schema is in the `build_html_report.py` docstring. You write the report JSON, not the HTML.

## Related skills

`rufus-discoverability-audit` — lighter sibling for when the seller has only listing copy. This skill supersedes it when data is richer. Self-contained — no runtime dependency on other Sophie Society skills.
