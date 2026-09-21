-- ============================================================================
-- Schema export — Supabase "POD 66 - Organization" (schema public)
-- ESTRUCTURA SOLAMENTE — sin data de clientes.
-- Origen: proyecto awhiobrcgghyiycxukjm · Postgres 17
-- Uso: aplicar en el proyecto Supabase nuevo (Fase 2 de la migración).
-- Aplicar con: supabase db execute / apply_migration, o el SQL editor.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- clients — config por cliente (una fila por brand). Todas las skills la leen.
-- ---------------------------------------------------------------------------
create table if not exists public.clients (
  brand       text        primary key,
  active      boolean     not null default true,
  config      jsonb,                         -- ver DATA-DICTIONARY.md (config_keys)
  actualizado timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- dashboard_snapshots — los feeders hacen upsert de 1 fila por (cliente,tipo,fecha).
-- El composer (master-dashboard-supabase) lee de acá para armar los 7 tabs.
-- ---------------------------------------------------------------------------
create table if not exists public.dashboard_snapshots (
  id          bigint      generated always as identity primary key,
  cliente     text        not null,
  tipo        text        not null,  -- daily_check | harvest | negatives | negatives_push | negatives_review | optimizations | restock
  fecha       date        not null,
  datos       jsonb       not null,
  actualizado timestamptz not null default now(),
  constraint dashboard_snapshots_uq unique (cliente, tipo, fecha)  -- clave del upsert diario
);
create index if not exists dashboard_snapshots_lookup
  on public.dashboard_snapshots using btree (cliente, tipo, fecha desc);

-- ---------------------------------------------------------------------------
-- dashboards — templates/artefactos del dashboard. Fila id='master' = master dashboard.
-- ---------------------------------------------------------------------------
create table if not exists public.dashboards (
  id            text        primary key,     -- p.ej. 'master'
  template_html text,
  artifact_url  text,
  updated       timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- relevance_profiles — perfil de relevancia por brand (ficha de producto,
-- roots, competitors, allowlist, negativos protegidos, etc.). Lo usan los
-- skills de negativos para juzgar relevancia.
-- ---------------------------------------------------------------------------
create table if not exists public.relevance_profiles (
  brand   text        primary key,
  profile jsonb       not null,              -- ver DATA-DICTIONARY.md (profile_keys)
  updated timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- organic_rank_snapshots — snapshots semanales de rank orgánico/sponsored por
-- brand/marketplace/asin/keyword (skill weekly-organic-ranks).
-- ---------------------------------------------------------------------------
create table if not exists public.organic_rank_snapshots (
  id             bigint      generated always as identity primary key,
  brand          text        not null,
  marketplace    text        not null,
  account_id     integer,
  asin           text        not null,
  asin_name      text,
  keyword        text        not null,
  organic_rank   integer,
  page           integer,
  sponsored_rank integer,
  best_rank_30d  integer,
  worst_rank_30d integer,
  data_points    integer,
  best_seller    boolean,
  amazon_choice  boolean,
  week_date      date        not null,
  created_at     timestamptz not null default now(),
  constraint uq_ors_row unique (brand, marketplace, asin, keyword, week_date)
);
create index if not exists idx_ors_brand_mkp_week
  on public.organic_rank_snapshots using btree (brand, marketplace, week_date);

-- ---------------------------------------------------------------------------
-- RLS — en el origen las 5 tablas tienen RLS habilitado y CERO policies:
-- la escritura va con la service_role key (que bypassa RLS). Mismo patrón acá.
-- (Guardá la service_role key como secret; nunca en las skills ni en git.)
-- ---------------------------------------------------------------------------
alter table public.clients                enable row level security;
alter table public.dashboard_snapshots    enable row level security;
alter table public.dashboards             enable row level security;
alter table public.relevance_profiles     enable row level security;
alter table public.organic_rank_snapshots enable row level security;
