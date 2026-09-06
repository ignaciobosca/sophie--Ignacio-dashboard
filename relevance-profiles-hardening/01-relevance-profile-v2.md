# `relevance-profile-v2` — schema del perfil de relevancia

> Contrato del que dependen `client-onboarding`, `daily-negatives-supabase` (motor + learn),
> `daily-negatives-autopush` (gate + MODE=approved) y el dashboard.
> Fuente de verdad: tabla Supabase `public.relevance_profiles` (columna `profile` JSONB, key = `brand`).

---

## Qué cambia vs. v1

| v1 (`relevance-profile-v1`) | v2 (`relevance-profile-v2`) |
|---|---|
| `roots: ["bamboo", ...]` (strings) | `roots: [{root, match, reason, confidence, evidence, basis, added_by, added_on, confirmations}]` |
| `competitors: ["little unicorn", ...]` (strings) | `competitors: [{name, reason, confidence, evidence, basis, added_by, added_on, confirmations, monitor_only}]` |
| `protected_relevant: [{term, reason}]` (scope escondido en el texto del `reason`) | `protected_relevant: [{term, reason, scope}]` (`scope` explícito: `equals` \| `contains`) |
| — | **`product_fiche`** — la vara de atributos del producto (copia del listing + atributos derivados), por ASIN |
| `roots`/`competitors` disparan Irrelevante sin gradiente | cada decisión lleva **`confidence` + `evidence` + `basis`** → alimenta el gate del autopush |

La forma de la tabla NO cambia (sigue siendo `brand` + `profile` JSONB + `updated`). Todo el cambio vive **dentro** del JSONB.

---

## Estructura completa

```jsonc
{
  "brand_name": "Natchiketa",
  "config_stem": "Natchiketa",
  "schema": "relevance-profile-v2",

  // ─────────────────────────────────────────────────────────────────────────
  // LA VARA: qué ES / qué TIENE / qué NO TIENE el producto.
  // Se toma una sola vez en el onboarding (auto-jalado del listing) y se
  // refresca a mano con "actualizar ficha de [producto] de [Brand]".
  // ─────────────────────────────────────────────────────────────────────────
  "product_fiche": {
    "updated": "2026-09-06",
    "updated_by": "onboarding",          // onboarding | manual-refresh
    "items": [
      {
        "asin": "B0XXXXXXXX",
        "name": "Woodland Nursery Comforter",   // label corto (del config)
        "line": "Comforters",                   // línea/parent (para ruteo del push)
        "status": "ok",                         // ok | no_fiche  (ver "Robustez")
        "source": "helium10:get_listing_details", // de dónde salió la copia
        "fetched_on": "2026-09-06",

        // Copia cruda del listing (para auditar de dónde salió cada atributo).
        "source_listing": {
          "title": "Woodland Nursery Crib Comforter, 100% Cotton, Reversible Forest Animal Baby Blanket",
          "bullets": ["100% cotton shell ...", "Reversible woodland print ...", "..."],
          "description": "..."
        },

        // Atributos PRESENTES — derivados del listing + campos estructurados si están.
        "attributes_present": {
          "ingredients_actives": [],
          "scents_flavors": [],
          "sizes_formats": ["crib", "toddler"],
          "materials": ["cotton"],
          "audience": ["baby", "nursery"],
          "use_cases": ["crib bedding", "nursery decor"],
          "features": ["woodland theme", "reversible"]
        },

        // Atributos AUSENTES — SOLO ausencia clara (nunca inferencia agresiva).
        // Son los que habilitan attribute-mismatch → confidence high. Ver rúbrica.
        "attributes_absent": [
          { "attr": "bamboo",   "evidence": "material declarado = 100% cotton; bamboo no aparece" },
          { "attr": "weighted", "evidence": "no figura en title/bullets/description ni en attrs estructurados" }
        ],

        // Variaciones que SÍ existen en la familia (para no negar variaciones propias).
        // Opcional; si el catalog no las trae, queda {}.
        "variations": {
          "sizes_formats": ["crib", "toddler"],
          "scents_flavors": []
        }
      }
    ]
  },

  // ─────────────────────────────────────────────────────────────────────────
  // LO APRENDIDO: familias/marcas ya confirmadas como irrelevantes.
  // Cada entry es basis=profile → cuando un término matchea, el juicio es HIGH
  // por consistencia (ya pasó por el ojo de Nacho alguna vez).
  // ─────────────────────────────────────────────────────────────────────────
  "roots": [
    {
      "root": "bamboo",
      "match": "phrase",
      "reason": "material ajeno (el producto es cotton)",
      "confidence": "high",
      "evidence": "bamboo ∈ attributes_absent del ASIN B0XXXXXXXX",
      "basis": "profile",
      "added_by": "learn",
      "added_on": "2026-07-14",
      "confirmations": 2
    }
  ],
  "competitors": [
    {
      "name": "little unicorn",
      "reason": "marca competidora de nursery bedding",
      "confidence": "high",
      "evidence": "marca reconocida; confirmada por Nacho",
      "basis": "profile",
      "added_by": "learn",
      "added_on": "2026-07-04",
      "confirmations": 3,
      "monitor_only": false          // true = competidor a monitorear, NO negar (equivale a protegido)
    }
  ],

  // ─────────────────────────────────────────────────────────────────────────
  // LA RED DE SEGURIDAD: excepciones que NUNCA se negativizan. Última palabra.
  // ─────────────────────────────────────────────────────────────────────────
  "protected_relevant": [
    { "term": "comforter", "reason": "el producto puede considerarse un comforter", "scope": "equals" },
    { "term": "woodland",  "reason": "tema propio; todo lo que incluya woodland no negar", "scope": "contains" }
  ],

  "updated": "2026-09-06",
  "updated_by": "nacho",
  "change_log": [
    "2026-09-06: migrado v1→v2; ficha de producto cargada en onboarding (3 ASINs).",
    "2026-07-14: 'little unicorn' protegido — removido de roots+competitors; gana la excepción."
  ]
}
```

---

## Campos nuevos — definición

### `confidence` — `high` | `medium` | `low`
El gradiente que gobierna el autopush. **Regla de oro:** si la irrelevancia no se puede
fundamentar con evidencia concreta, NO es `high`.

| Nivel | Cuándo | Autopush |
|---|---|---|
| **high** | Verificable sin criterio opinable: (a) matchea un `root`/`competitor` del perfil (`basis=profile`), (b) marca ajena **reconocida con certeza**, (c) off-category inequívoco (palabra clara de otra categoría: `furniture`, `diapers`), (d) attribute-mismatch donde el atributo pedido está en `attributes_absent` de la ficha (**ausencia explícita**). | ✅ sí |
| **medium** | Probable pero apoyada en inferencia: (a) *"parece"* nombre de marca no reconocido, (b) equivalencia de dominio aplicada (declararla), (c) attribute-mismatch donde el atributo **no está** ni en present ni en absent (no confirmable), (d) la ficha del ASIN es `no_fiche` (juicio sin vara → nunca high). | ✅ sí |
| **low** | Señal débil / ambiguo: el modelo se inclina a irrelevante pero con dudas. | ❌ va a review |

### `evidence` — string corto y **verificable**
El hecho que disparó la decisión, no prosa. Ej: `"bamboo ∈ attributes_absent"`,
`"marca reconocida de nursery bedding"`, `"off-category: furniture"`. Es lo que Nacho lee de
un vistazo en el dashboard para decidir un LOW.

### `basis` — `profile` | `model` | `rule`
De dónde viene la decisión: `profile` (root/competitor ya confirmado en el perfil),
`model` (juicio semántico del turno), `rule` (determinístico: marca propia, ASIN, char especial).
`basis=profile` ⇒ `confidence=high` automático.

### `product_fiche.items[].status` — `ok` | `no_fiche`
`no_fiche` cuando el auto-jalado falló o vino vacío para ese ASIN. **No se inventa ficha.**
El motor juzga ese ASIN con la lógica conservadora de hoy y ningún juicio suyo llega a `high`
por attribute-mismatch (no hay `attributes_absent` confiable).

### `protected_relevant[].scope` — `equals` | `contains`
Formaliza la regla que en v1 vivía escondida en el texto del `reason`:
- `contains` (wildcard): raíz de **marca/atributo propio** → protege todo término que la contenga
  (ej. `woodland` protege `woodland animal theme nursery`).
- `equals` (igualdad exacta): **descriptor de categoría** multi-palabra → protege solo la búsqueda
  pelada, no blinda productos de competidor que lo contengan
  (ej. `spiced rum` protege la búsqueda genérica pero `liverpool lost dock spiced rum` **sí** se niega).
- **Ante la duda → `equals`** (conservador).

---

## Retrocompatibilidad (lectura de perfiles v1 sin migrar)

Todo consumidor del perfil debe leer v1 y v2 indistintamente:

- `roots` string `"bamboo"` → `{root:"bamboo", match:"phrase", confidence:"high", basis:"profile", evidence:"(migrado v1)"}`.
- `competitors` string `"little unicorn"` → `{name:"little unicorn", confidence:"high", basis:"profile", evidence:"(migrado v1)"}`.
- `protected_relevant` sin `scope` → derivar replicando el default v1: (1) `reason` con `"SOLO igualdad"`/`"equality only"` → `equals`; (2) `reason` con `"todo lo que incluya"`/`"contención"`/`"cualquier"` → `contains`; (3) sin marcador → **raíz suelta (una sola palabra) → `contains`; descriptor multi-palabra → `equals`**. (Un `protected` que venga como string suelto —data vieja— se parsea: term = lo previo al `[`/`(`, el resto = reason; se marca `_needs_scope_review`.)
- `product_fiche` ausente → tratarlo como `{items:[]}` (el motor cae a la lógica de hoy hasta que se corra el onboarding/refresh de ficha).

La **migración** (`01-migrate-v1-to-v2.py`) hace esta transformación una vez y de forma persistente;
la retrocompat de lectura es la red por si queda algún perfil sin migrar.
