import { createClient, SupabaseClient } from "@supabase/supabase-js";
import type { Entry, Payment, Platform } from "./types";

/**
 * Capa de almacenamiento con dos backends:
 *  - Supabase (producción), si están las variables de entorno.
 *  - En memoria (demo), si no lo están. Se reinicia al reiniciar el server.
 */

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

export const usingSupabase = Boolean(SUPABASE_URL && SUPABASE_SERVICE_KEY);

let _sb: SupabaseClient | null = null;
function sb(): SupabaseClient {
  if (!_sb) {
    _sb = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!, {
      auth: { persistSession: false },
    });
  }
  return _sb;
}

// ---------------------------------------------------------------------------
// Store en memoria (modo demo)
// ---------------------------------------------------------------------------

type MemStore = {
  entries: Map<string, Entry>;
  payments: Map<string, Payment>;
  clickLog: Map<string, number>; // dedupKey -> último clic contado (ms)
  visits: Map<string, number>; // session -> last_seen (ms)
};

const g = globalThis as unknown as { __boostStore?: MemStore };
function mem(): MemStore {
  if (!g.__boostStore) {
    g.__boostStore = { entries: new Map(), payments: new Map(), clickLog: new Map(), visits: new Map() };
    seedDemo(g.__boostStore);
  }
  return g.__boostStore;
}

function uid() {
  return "id_" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

function seedDemo(store: MemStore) {
  const demo: Omit<Entry, "id" | "created_at">[] = [
    { handle: "@lucia.crea", platform: "instagram", url: "https://instagram.com/lucia.crea", message: "Diseño y hago reels que rompen 🔥", avatar_url: null, total_amount: 12500, boosts: 9, clicks: 3128 },
    { handle: "@martin.gg", platform: "twitch", url: "https://twitch.tv/martin_gg", message: "Streamer de Valorant, seguime que subo clips", avatar_url: null, total_amount: 8300, boosts: 6, clicks: 1974 },
    { handle: "@sofi.beats", platform: "spotify", url: "https://open.spotify.com/artist/demo", message: "Nuevo single afuera, dale play 🎧", avatar_url: null, total_amount: 6100, boosts: 4, clicks: 1245 },
    { handle: "@eltoto", platform: "tiktok", url: "https://tiktok.com/@eltoto", message: "Humor argento diario", avatar_url: null, total_amount: 3400, boosts: 3, clicks: 862 },
    { handle: "@dev.nacho", platform: "youtube", url: "https://youtube.com/@devnacho", message: "Tutoriales de código en español", avatar_url: null, total_amount: 1500, boosts: 2, clicks: 391 },
  ];
  const base = Date.now() - demo.length * 1000;
  demo.forEach((d, i) => {
    const id = uid();
    store.entries.set(id, { ...d, id, created_at: new Date(base + i * 1000).toISOString() });
  });
}

// ---------------------------------------------------------------------------
// API pública del store
// ---------------------------------------------------------------------------

export async function listEntries(): Promise<Entry[]> {
  if (usingSupabase) {
    const { data, error } = await sb()
      .from("entries")
      .select("*")
      .order("total_amount", { ascending: false })
      .order("created_at", { ascending: true });
    if (error) throw error;
    return (data ?? []) as Entry[];
  }
  return Array.from(mem().entries.values()).sort(
    (a, b) => b.total_amount - a.total_amount || a.created_at.localeCompare(b.created_at)
  );
}

export async function getEntry(id: string): Promise<Entry | null> {
  if (usingSupabase) {
    const { data } = await sb().from("entries").select("*").eq("id", id).maybeSingle();
    return (data as Entry) ?? null;
  }
  return mem().entries.get(id) ?? null;
}

export async function createEntry(input: {
  handle: string;
  platform: Platform;
  url: string;
  message: string;
  avatar_url?: string | null;
}): Promise<Entry> {
  const now = new Date().toISOString();
  if (usingSupabase) {
    const { data, error } = await sb()
      .from("entries")
      .insert({
        handle: input.handle,
        platform: input.platform,
        url: input.url,
        message: input.message,
        avatar_url: input.avatar_url ?? null,
        total_amount: 0,
        boosts: 0,
        clicks: 0,
      })
      .select("*")
      .single();
    if (error) throw error;
    return data as Entry;
  }
  const entry: Entry = {
    id: uid(),
    handle: input.handle,
    platform: input.platform,
    url: input.url,
    message: input.message,
    avatar_url: input.avatar_url ?? null,
    total_amount: 0,
    boosts: 0,
    clicks: 0,
    created_at: now,
  };
  mem().entries.set(entry.id, entry);
  return entry;
}

export async function createPayment(input: {
  entry_id: string;
  amount: number;
  currency?: string;
  provider_ref?: string | null;
}): Promise<Payment> {
  const now = new Date().toISOString();
  if (usingSupabase) {
    const { data, error } = await sb()
      .from("payments")
      .insert({
        entry_id: input.entry_id,
        amount: input.amount,
        currency: input.currency ?? "ARS",
        status: "pending",
        provider_ref: input.provider_ref ?? null,
      })
      .select("*")
      .single();
    if (error) throw error;
    return data as Payment;
  }
  const payment: Payment = {
    id: uid(),
    entry_id: input.entry_id,
    amount: input.amount,
    currency: input.currency ?? "ARS",
    status: "pending",
    provider_ref: input.provider_ref ?? null,
    created_at: now,
  };
  mem().payments.set(payment.id, payment);
  return payment;
}

export async function getPayment(id: string): Promise<Payment | null> {
  if (usingSupabase) {
    const { data } = await sb().from("payments").select("*").eq("id", id).maybeSingle();
    return (data as Payment) ?? null;
  }
  return mem().payments.get(id) ?? null;
}

export async function setPaymentProviderRef(id: string, ref: string): Promise<void> {
  if (usingSupabase) {
    await sb().from("payments").update({ provider_ref: ref }).eq("id", id);
    return;
  }
  const p = mem().payments.get(id);
  if (p) p.provider_ref = ref;
}

/**
 * Marca un pago como aprobado e incrementa el total del perfil.
 * Es idempotente: si el pago ya estaba aprobado, no vuelve a sumar.
 */
export async function approvePayment(id: string): Promise<Entry | null> {
  if (usingSupabase) {
    const { data: pay } = await sb().from("payments").select("*").eq("id", id).maybeSingle();
    if (!pay) return null;
    if (pay.status === "approved") return getEntry(pay.entry_id);
    await sb().from("payments").update({ status: "approved" }).eq("id", id);
    // Incremento atómico vía RPC (ver supabase/schema.sql)
    const { data, error } = await sb().rpc("increment_boost", {
      p_entry_id: pay.entry_id,
      p_amount: pay.amount,
    });
    if (error) throw error;
    return (data as Entry) ?? getEntry(pay.entry_id);
  }
  const store = mem();
  const p = store.payments.get(id);
  if (!p) return null;
  if (p.status === "approved") return store.entries.get(p.entry_id) ?? null;
  p.status = "approved";
  const e = store.entries.get(p.entry_id);
  if (e) {
    e.total_amount += p.amount;
    e.boosts += 1;
  }
  return e ?? null;
}

/**
 * Registra un clic con deduplicación por visitante.
 * Solo cuenta si ese `dedupKey` no contó un clic sobre este perfil dentro de
 * los últimos `windowSeconds`. Devuelve true si se contó, false si se ignoró.
 */
export async function countClick(
  entryId: string,
  dedupKey: string,
  windowSeconds: number
): Promise<boolean> {
  if (usingSupabase) {
    const { data, error } = await sb().rpc("register_click", {
      p_entry_id: entryId,
      p_dedup_key: dedupKey,
      p_window_seconds: windowSeconds,
    });
    if (error) throw error;
    return Boolean(data);
  }
  const store = mem();
  const e = store.entries.get(entryId);
  if (!e) return false;
  const key = `${entryId}:${dedupKey}`;
  const now = Date.now();
  const last = store.clickLog.get(key);
  if (last && now - last < windowSeconds * 1000) return false;
  store.clickLog.set(key, now);
  e.clicks += 1;
  cleanupClickLog(store, windowSeconds);
  return true;
}

function cleanupClickLog(store: MemStore, windowSeconds: number) {
  if (store.clickLog.size <= 5000) return;
  const cutoff = Date.now() - windowSeconds * 1000;
  for (const [k, t] of store.clickLog) if (t < cutoff) store.clickLog.delete(k);
}

// ---------------------------------------------------------------------------
// Presencia de visitantes (contador "en línea / última hora")
// ---------------------------------------------------------------------------

const ONLINE_MS = 5 * 60 * 1000; // "en línea" = visto en los últimos 5 min
const HOUR_MS = 60 * 60 * 1000;

export interface VisitorStats {
  online: number;
  lastHour: number;
}

/** Registra la presencia de una sesión y devuelve las métricas actualizadas. */
export async function recordVisit(session: string): Promise<VisitorStats> {
  const now = Date.now();
  if (usingSupabase) {
    await sb()
      .from("visits")
      .upsert({ session, last_seen: new Date(now).toISOString() }, { onConflict: "session" });
    return getVisitorStats();
  }
  const m = mem().visits;
  m.set(session, now);
  for (const [k, t] of m) if (now - t > HOUR_MS) m.delete(k); // limpieza
  return computeMemStats(now);
}

/** Devuelve las métricas sin registrar (para bots o solo lectura). */
export async function getVisitorStats(): Promise<VisitorStats> {
  const now = Date.now();
  if (usingSupabase) {
    const onlineCut = new Date(now - ONLINE_MS).toISOString();
    const hourCut = new Date(now - HOUR_MS).toISOString();
    const [onlineRes, hourRes] = await Promise.all([
      sb().from("visits").select("session", { count: "exact", head: true }).gte("last_seen", onlineCut),
      sb().from("visits").select("session", { count: "exact", head: true }).gte("last_seen", hourCut),
    ]);
    return { online: onlineRes.count ?? 0, lastHour: hourRes.count ?? 0 };
  }
  return computeMemStats(now);
}

function computeMemStats(now: number): VisitorStats {
  let online = 0;
  let lastHour = 0;
  for (const t of mem().visits.values()) {
    if (now - t <= ONLINE_MS) online++;
    if (now - t <= HOUR_MS) lastHour++;
  }
  return { online, lastHour };
}

export interface PublicStats {
  profiles: number;
  boosts: number;
  raised: number;
  clicks: number;
  online: number;
  lastHour: number;
  last24h: number;
  recent: { handle: string; platform: string; amount: number; created_at: string }[];
}

/** Estadísticas públicas agregadas para la página /stats. */
export async function getPublicStats(): Promise<PublicStats> {
  if (usingSupabase) {
    const { data, error } = await sb().rpc("public_stats");
    if (error) throw error;
    const d = (data ?? {}) as Record<string, unknown>;
    return {
      profiles: Number(d.profiles) || 0,
      boosts: Number(d.boosts) || 0,
      raised: Number(d.raised) || 0,
      clicks: Number(d.clicks) || 0,
      online: Number(d.online) || 0,
      lastHour: Number(d.lastHour) || 0,
      last24h: Number(d.last24h) || 0,
      recent: Array.isArray(d.recent) ? (d.recent as PublicStats["recent"]) : [],
    };
  }
  const store = mem();
  const now = Date.now();
  const entries = Array.from(store.entries.values());
  let online = 0;
  let lastHour = 0;
  let last24h = 0;
  for (const t of store.visits.values()) {
    if (now - t <= ONLINE_MS) online++;
    if (now - t <= HOUR_MS) lastHour++;
    if (now - t <= 24 * 60 * 60 * 1000) last24h++;
  }
  const recent = Array.from(store.payments.values())
    .filter((p) => p.status === "approved")
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 8)
    .map((p) => {
      const e = store.entries.get(p.entry_id);
      return {
        handle: e?.handle ?? "@?",
        platform: e?.platform ?? "otro",
        amount: p.amount,
        created_at: p.created_at,
      };
    });
  return {
    profiles: entries.length,
    boosts: entries.reduce((s, e) => s + e.boosts, 0),
    raised: entries.reduce((s, e) => s + e.total_amount, 0),
    clicks: entries.reduce((s, e) => s + e.clicks, 0),
    online,
    lastHour,
    last24h,
    recent,
  };
}

export async function rejectPayment(id: string): Promise<void> {
  if (usingSupabase) {
    await sb().from("payments").update({ status: "rejected" }).eq("id", id);
    return;
  }
  const p = mem().payments.get(id);
  if (p && p.status === "pending") p.status = "rejected";
}
