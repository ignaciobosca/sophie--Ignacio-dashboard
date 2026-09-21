-- ============================================================================
-- Add-on MULTI-TENANT (Fase 3) — aplicar DESPUÉS de schema.sql.
-- Objetivo: servir a varias agencias con la misma base de skills, sin forks.
-- Idea: keyear la config por (agency_id, brand) y parametrizar el branding.
-- Revisar antes de correr — es un rediseño, no un copy/paste.
-- ============================================================================

-- 1) Agencias -----------------------------------------------------------------
create table if not exists public.agencies (
  agency_id   text        primary key,     -- p.ej. 'acme', 'nacho-direct'
  name        text        not null,
  active      boolean     not null default true,
  -- credenciales/settings por agencia (SHURQ, ClickUp, Slack, Drive, etc.)
  -- guardar solo IDs/refs no sensibles acá; los tokens van a secrets del entorno.
  connectors  jsonb,
  created_at  timestamptz not null default now()
);

-- 2) clients: agregar agency_id ----------------------------------------------
-- La PK actual es brand (global). Multi-tenant: un mismo brand podría existir
-- en dos agencias, así que la identidad pasa a ser (agency_id, brand).
alter table public.clients
  add column if not exists agency_id text references public.agencies(agency_id);

-- Backfill para las filas existentes (si migrás alguna estructura de prueba):
-- update public.clients set agency_id = 'default' where agency_id is null;

-- Cuando esté backfilleado y sin nulls, promover la PK compuesta:
--   alter table public.clients drop constraint clients_pkey;
--   alter table public.clients add primary key (agency_id, brand);
-- (Si hacés esto, replicá agency_id en dashboard_snapshots.cliente / las FKs.)

-- 3) brand_kit por agencia (branding parametrizado) --------------------------
-- Reemplaza el branding Sophie hardcodeado en las skills 🏷️.
create table if not exists public.brand_kits (
  agency_id  text        not null references public.agencies(agency_id),
  name       text        not null default 'default',
  kit        jsonb       not null,   -- { palette:{}, fonts:{}, logo_url, voice, footer, ... }
  updated    timestamptz not null default now(),
  primary key (agency_id, name)
);

-- 4) RLS igual que el resto ---------------------------------------------------
alter table public.agencies   enable row level security;
alter table public.brand_kits enable row level security;

-- ----------------------------------------------------------------------------
-- Refactor de skills (fuera de SQL):
--  * clients: resolver config por (agency_id, brand) en vez de brand solo.
--  * skills 🏷️: leer brand_kit(agency_id) por parámetro; nada de "Sophie" fijo.
--  * canales Slack / repo Pages: mover de hardcode a clients.config / agencies.connectors.
-- ----------------------------------------------------------------------------
