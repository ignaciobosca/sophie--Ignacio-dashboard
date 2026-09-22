# INVENTORY — skills que te llevás (triage completo)

De **96 skills** en el entorno de Sophie, te llevás **42**. El resto: 43 descartadas
en la revisión, 11 duplicados/legacy/test/genéricas auto-excluidas.

**Tags:** ✅ portá tal cual (reconfig de conector) · 🔧 rebuild (cutover Sophie Hub) · 🏷️ re-brand (branding vía brand-kit)

## `skills/master-dashboard/` (6)
- `master-dashboard-supabase` ✅
- `daily-check-dashboard-supabase` ✅
- `daily-check-client-supabase` ✅
- `daily-negatives-supabase` ✅
- `daily-harvest-supabase` ✅
- `daily-restock-supabase` 🔧

## `skills/ppc-ops/` (12)
- `weekly-report` ✅ · `weekly-wins` ✅
- `search-term-harvest` ✅
- `negative-targeting` ✅ · `daily-negatives-autopush` ✅ · `weekly-negatives-review` ✅ · `shurq-push-negatives` ✅
- `biweekly-bid-optimizer` ✅
- `launch-sponsored-products` 🔧
- `kpi-quick-check` ✅ · `weekly-organic-ranks` ✅
- `ppc-audit` 🏷️

## `skills/comms-workflow/` (10)
- `client-reply-drafter` 🔧 · `client-onboarding` 🔧
- `slack-channel-review` ✅ · `inbox-triage` ✅ · `client-changelog` ✅
- `morning` ✅ · `personal-assistant-skill` ✅
- `client-call-summary` ✅ · `client-meeting-prep` ✅ · `team-meeting-summary` ✅

## `skills/reporting/` (1)
- `monthly-report` 🔧

## `skills/listing/` (3)
- `listing-juice-new` 🔧 · `amazon-title-optimizer` 🔧 · `listing-writer-v2` 🏷️

## `skills/research/` (1)
- `bundle-crosssell-finder` 🔧

## `skills/creative/` (6)
- `amazon-hero-image-v12` 🏷️ · `amazon-ab-testing-all-in-one` 🏷️ · `ab-secondary-image-creator` 🏷️
- `primary-image-hypotheses` 🏷️ · `aplus-plan-per-banner` 🏷️ · `brand-story-plan` 🏷️

## `skills/brand/` (2)
- `brand-kit` 🏷️ (base del branding por agencia) · `brand-identity-board` 🏷️

## `skills/setup/` (1)
- `keepa-smartscout-datadive-installer-experimental` ✅

---

## Resumen por esfuerzo
- **✅ Portá tal cual: 24** — solo reconfig de conector (SHURQ/Supabase/Slack/ClickUp).
- **🔧 Rebuild: 8** — cutover Sophie Hub → SHURQ/Helium10/Keepa/DataDive. Ver `rebuild-decisions.md`.
- **🏷️ Re-brand: 10** — swap branding vía `brand-kit`. Ver `rebrand-decisions.md`.

## Orden de arranque sugerido
1. **Infra:** Supabase (`../supabase/schema.sql` + `multi-tenant.sql`) + conectores.
2. **✅ Portá tal cual** — arrancan casi sin tocar; validá el master-dashboard system end-to-end.
3. **🏷️ Re-brand** — definí `brand-kit` y aplicá a las creativas.
4. **🔧 Rebuild** — de las livianas a la pesada (`listing-juice-new` al final).

## Docs relacionados
- `rebuild-decisions.md` · `rebrand-decisions.md` · `utilities-comms-decisions.md`
- `multi-tenant-spec.md` · `../MIGRATION-NOTES.md` · `../supabase/DATA-DICTIONARY.md`
