-- ============================================================
-- Boost tus Redes — esquema de base de datos (Supabase / Postgres)
-- Ejecutar en: Supabase -> SQL Editor -> New query -> Run
-- ============================================================

create extension if not exists "pgcrypto";

-- Perfiles en el ranking
create table if not exists public.entries (
  id            uuid primary key default gen_random_uuid(),
  handle        text not null,
  platform      text not null,
  url           text not null,
  message       text default '',
  avatar_url    text,
  total_amount  numeric not null default 0,
  boosts        integer not null default 0,
  created_at    timestamptz not null default now()
);

create index if not exists entries_rank_idx
  on public.entries (total_amount desc, created_at asc);

-- Pagos (cada boost individual)
create table if not exists public.payments (
  id            uuid primary key default gen_random_uuid(),
  entry_id      uuid not null references public.entries(id) on delete cascade,
  amount        numeric not null,
  currency      text not null default 'ARS',
  status        text not null default 'pending', -- pending | approved | rejected
  provider_ref  text,
  created_at    timestamptz not null default now()
);

create index if not exists payments_entry_idx on public.payments (entry_id);

-- Incremento atómico del total al aprobar un pago
create or replace function public.increment_boost(p_entry_id uuid, p_amount numeric)
returns public.entries
language plpgsql
as $$
declare
  updated public.entries;
begin
  update public.entries
     set total_amount = total_amount + p_amount,
         boosts = boosts + 1
   where id = p_entry_id
  returning * into updated;
  return updated;
end;
$$;

-- ============================================================
-- Row Level Security
-- El servidor usa la SERVICE ROLE KEY (bypassa RLS), así que solo
-- exponemos lectura pública del ranking para el cliente anon.
-- ============================================================
alter table public.entries enable row level security;
alter table public.payments enable row level security;

drop policy if exists "ranking legible por todos" on public.entries;
create policy "ranking legible por todos"
  on public.entries for select
  using (true);

-- payments: sin políticas públicas -> solo accesible con service role.
