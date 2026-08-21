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
  clicks        integer not null default 0,
  created_at    timestamptz not null default now()
);

-- Si ya tenías la tabla creada, agregá la columna de clics:
alter table public.entries add column if not exists clicks integer not null default 0;

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
security definer
set search_path = public
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

-- Registro de clics para deduplicación por visitante (IP + sesión, hasheado)
create table if not exists public.click_log (
  entry_id   uuid not null references public.entries(id) on delete cascade,
  dedup_key  text not null,
  last_seen  timestamptz not null default now(),
  primary key (entry_id, dedup_key)
);

create index if not exists click_log_seen_idx on public.click_log (last_seen);

-- Registra un clic solo si el mismo visitante no contó dentro de la ventana.
-- Devuelve true si se contó, false si se ignoró (dedup).
create or replace function public.register_click(
  p_entry_id uuid,
  p_dedup_key text,
  p_window_seconds integer
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  existing timestamptz;
begin
  select last_seen into existing
    from public.click_log
   where entry_id = p_entry_id and dedup_key = p_dedup_key;

  if existing is not null and existing > now() - make_interval(secs => p_window_seconds) then
    return false; -- clic reciente del mismo visitante → no contamos
  end if;

  insert into public.click_log (entry_id, dedup_key, last_seen)
  values (p_entry_id, p_dedup_key, now())
  on conflict (entry_id, dedup_key) do update set last_seen = now();

  update public.entries set clicks = clicks + 1 where id = p_entry_id;
  return true;
end;
$$;

-- ============================================================
-- Row Level Security
-- El servidor usa la SERVICE ROLE KEY (bypassa RLS), así que solo
-- exponemos lectura pública del ranking para el cliente anon.
-- ============================================================
alter table public.entries enable row level security;
alter table public.payments enable row level security;
alter table public.click_log enable row level security;

drop policy if exists "ranking legible por todos" on public.entries;
create policy "ranking legible por todos"
  on public.entries for select
  using (true);

-- payments y click_log: sin políticas públicas -> solo accesible con service role.

-- ============================================================
-- Blindaje de las RPC: solo el servidor (service_role) puede ejecutarlas.
-- Sin esto, cualquiera con la llave pública podría treparse al #1 sin pagar
-- (increment_boost) o inflar clics (register_click) vía /rest/v1/rpc/...
-- ============================================================
revoke execute on function public.increment_boost(uuid, numeric) from public, anon, authenticated;
revoke execute on function public.register_click(uuid, text, integer) from public, anon, authenticated;
grant execute on function public.increment_boost(uuid, numeric) to service_role;
grant execute on function public.register_click(uuid, text, integer) to service_role;

-- ============================================================
-- Presencia de visitantes (contador "en línea / última hora")
-- Una fila por sesión; se actualiza last_seen en cada ping.
-- ============================================================
create table if not exists public.visits (
  session    text primary key,
  last_seen  timestamptz not null default now()
);

create index if not exists visits_seen_idx on public.visits (last_seen);

alter table public.visits enable row level security;
-- Sin políticas públicas: solo el servidor (service_role) escribe y lee.

-- ============================================================
-- Estadísticas públicas agregadas (página /stats)
-- Devuelve un JSON con totales seguros para mostrar en público.
-- La llama el servidor (service_role); el front la consume vía /api/stats.
-- ============================================================
create or replace function public.public_stats()
returns json
language sql
security definer
set search_path = public
as $$
  select json_build_object(
    'profiles', (select count(*) from entries),
    'boosts',   (select coalesce(sum(boosts), 0) from entries),
    'raised',   (select coalesce(sum(total_amount), 0) from entries),
    'clicks',   (select coalesce(sum(clicks), 0) from entries),
    'online',   (select count(*) from visits where last_seen > now() - interval '5 minutes'),
    'lastHour', (select count(*) from visits where last_seen > now() - interval '60 minutes'),
    'last24h',  (select count(*) from visits where last_seen > now() - interval '24 hours'),
    'recent',   (select coalesce(json_agg(r), '[]'::json) from (
        select e.handle, e.platform, p.amount, p.created_at
        from payments p
        join entries e on e.id = p.entry_id
        where p.status = 'approved'
        order by p.created_at desc
        limit 8
      ) r)
  );
$$;

revoke execute on function public.public_stats() from public, anon, authenticated;
grant execute on function public.public_stats() to service_role;
