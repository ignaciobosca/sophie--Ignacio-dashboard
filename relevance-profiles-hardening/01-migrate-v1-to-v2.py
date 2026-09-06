"""
Migración de perfiles de relevancia  v1 → v2  (tabla Supabase public.relevance_profiles).

POR QUÉ PYTHON Y NO .sql PURO
  La migración no es un cambio de columnas (la tabla sigue siendo brand + profile JSONB +
  updated). Es una transformación DENTRO del JSONB: envolver roots/competitors de strings a
  objetos, derivar `scope` del texto del `reason`, e inicializar `product_fiche`. Eso en SQL
  puro queda ilegible; en Python es una función pura, testeable y auditable.

CÓMO SE CORRE (desde una sesión con el Supabase MCP, p.ej. esta misma):
  1) DRY-RUN — leer todos los perfiles, aplicar migrate_profile() en memoria e imprimir un
     diff por marca. NO escribir nada.
         rows = execute_sql("select brand, profile from public.relevance_profiles")
         for r in rows: print(diff(r["profile"], migrate_profile(r["profile"])))
  2) VALIDAR — mirar 1–2 perfiles reales con Nacho antes de escribir (sobre todo que
     ningún `root`/`competitor` v1 haya perdido info y que los `scope` derivados sean correctos).
  3) APPLY — por cada fila, upsert del profile migrado:
         update public.relevance_profiles
            set profile = <migrated jsonb>, updated = now()
          where brand = <brand>;

IDEMPOTENTE: si el perfil ya es v2, migrate_profile() lo devuelve igual (no re-envuelve ni
re-agrega change_log). Se puede correr las veces que haga falta.
"""

from datetime import date

MIGRATION_NOTE = f"{date.today().isoformat()}: migrado v1→v2 (roots/competitors→objetos, scope explícito, product_fiche inicializada)."


# ── helpers de derivación ────────────────────────────────────────────────────

def _derive_scope(reason: str, term: str = "") -> str:
    """protected_relevant sin `scope` → derivarlo replicando el DEFAULT del sistema v1:
       1) el reason manda si es explícito;
       2) si no, raíz suelta (una sola palabra) → contención; descriptor multi-palabra → igualdad.
       (v1: 'raíz suelta de marca/atributo propio → contención; descriptor de categoría → igualdad'.)"""
    r = (reason or "").lower()
    # 1) marcadores explícitos en el reason
    if "solo igualdad" in r or "equality only" in r or "igualdad exacta" in r:
        return "equals"
    if ("todo lo que incluya" in r or "contenc" in r or "contiene" in r
            or "cualquier" in r or "wildcard" in r or "raíz" in r or "raiz" in r):
        return "contains"
    # 2) default v1 por forma del término: 1 palabra → contains ; multi-palabra → equals
    if term and len(term.split()) == 1:
        return "contains"
    return "equals"


def _wrap_root(item) -> dict:
    """root v1 (string) o v2 (dict) → dict v2 normalizado. Preserva lo que ya venga."""
    if isinstance(item, str):
        return {
            "root": item, "match": "phrase", "reason": "(migrado v1)",
            "confidence": "high", "evidence": "(migrado v1)", "basis": "profile",
            "added_by": "migration", "added_on": date.today().isoformat(), "confirmations": 1,
        }
    it = dict(item)
    it.setdefault("match", "phrase")
    it.setdefault("reason", "(migrado v1)")
    it.setdefault("confidence", "high")          # ya confirmado en el perfil
    it.setdefault("evidence", "(migrado v1)")
    it.setdefault("basis", "profile")
    it.setdefault("added_by", "migration")
    it.setdefault("added_on", date.today().isoformat())
    it.setdefault("confirmations", 1)
    return it


def _wrap_competitor(item) -> dict:
    """competitor v1 (string) o v2 (dict) → dict v2 normalizado."""
    if isinstance(item, str):
        return {
            "name": item, "reason": "(migrado v1)",
            "confidence": "high", "evidence": "(migrado v1)", "basis": "profile",
            "added_by": "migration", "added_on": date.today().isoformat(),
            "confirmations": 1, "monitor_only": False,
        }
    it = dict(item)
    # soportar tanto {"name":...} como {"competitor":...} por si algún perfil viejo usó otra key
    if "name" not in it and "competitor" in it:
        it["name"] = it.pop("competitor")
    it.setdefault("reason", "(migrado v1)")
    it.setdefault("confidence", "high")
    it.setdefault("evidence", "(migrado v1)")
    it.setdefault("basis", "profile")
    it.setdefault("added_by", "migration")
    it.setdefault("added_on", date.today().isoformat())
    it.setdefault("confirmations", 1)
    it.setdefault("monitor_only", False)
    return it


def _wrap_protected(item) -> dict:
    """protected v1: puede ser {term, reason} (lo normal) O un string suelto (data vieja inconsistente).
    String → separar term de la anotación entre corchetes/paréntesis; el resto es el reason.
    Marca `_needs_scope_review` para que un humano fije el scope (equals vs contains)."""
    if isinstance(item, str):
        s = item.strip()
        cuts = [p for p in (s.find(" ["), s.find(" (")) if p != -1]
        if cuts:
            i = min(cuts)
            term = s[:i].strip()
            reason = s[i:].strip().strip("[]()").strip()
        else:
            term, reason = s, "(migrado v1 — era string suelto)"
        return {"term": term, "reason": reason, "scope": _derive_scope(reason, term),
                "_needs_scope_review": True}
    it = dict(item)
    if not it.get("scope"):
        it["scope"] = _derive_scope(it.get("reason", ""), it.get("term", ""))
    return it


# ── transformación principal (pura) ──────────────────────────────────────────

def migrate_profile(profile: dict) -> dict:
    """v1 → v2. Idempotente: un perfil que ya es v2 vuelve igual (salvo defaults faltantes)."""
    p = dict(profile or {})
    already_v2 = p.get("schema") == "relevance-profile-v2"

    p["schema"] = "relevance-profile-v2"
    p["roots"] = [_wrap_root(x) for x in p.get("roots", [])]
    p["competitors"] = [_wrap_competitor(x) for x in p.get("competitors", [])]
    p["protected_relevant"] = [_wrap_protected(x) for x in p.get("protected_relevant", [])]

    # product_fiche: inicializar vacía si no existe. NUNCA pisar una ficha ya cargada.
    if "product_fiche" not in p:
        p["product_fiche"] = {"updated": None, "updated_by": None, "items": []}

    # change_log: agregar la nota de migración una sola vez.
    log = list(p.get("change_log", []))
    if not already_v2 and not any(l.startswith(MIGRATION_NOTE[:10]) and "migrado v1→v2" in l for l in log):
        log.append(MIGRATION_NOTE)
    p["change_log"] = log

    p.setdefault("updated_by", "migration")
    return p


# ── mini test de humo (correr con: python 01-migrate-v1-to-v2.py) ────────────

if __name__ == "__main__":
    v1 = {
        "brand_name": "Demo", "config_stem": "Demo", "schema": "relevance-profile-v1",
        "roots": ["bamboo", {"root": "weighted", "match": "phrase"}],
        "competitors": ["little unicorn"],
        "protected_relevant": [
            {"term": "comforter", "reason": "el producto puede considerarse un comforter (SOLO igualdad exacta)"},
            {"term": "woodland",  "reason": "tema propio; todo lo que incluya woodland no negar"},
            "dark rum",  # data vieja: protected como STRING suelto (caso real Every Cloud)
            "laurel [essence/scent used in Hekaya soap — NEVER negate; confirmed by Facundo 2026-08-17]",
        ],
        "change_log": ["2026-07-04: perfil creado."],
    }
    out = migrate_profile(v1)
    assert out["schema"] == "relevance-profile-v2"
    assert out["roots"][0]["root"] == "bamboo" and out["roots"][0]["confidence"] == "high"
    assert out["competitors"][0]["name"] == "little unicorn"
    assert out["protected_relevant"][0]["scope"] == "equals"     # "SOLO igualdad exacta"
    assert out["protected_relevant"][1]["scope"] == "contains"   # "todo lo que incluya"
    # protected que venían como STRING suelto → parseados a {term, reason, scope} + flag de revisión
    assert out["protected_relevant"][2]["term"] == "dark rum"
    assert out["protected_relevant"][2]["scope"] == "equals"     # multi-palabra → igualdad
    assert out["protected_relevant"][2].get("_needs_scope_review") is True
    assert out["protected_relevant"][3]["term"] == "laurel"      # term separado de la anotación
    assert out["protected_relevant"][3]["scope"] == "contains"   # una palabra (raíz propia) → contención (default v1)
    assert "NEVER negate" in out["protected_relevant"][3]["reason"]
    assert out["product_fiche"]["items"] == []
    assert migrate_profile(out)["change_log"] == out["change_log"]  # idempotente
    print("OK — migración v1→v2 pasa el smoke test (incluye protected como string suelto).")
