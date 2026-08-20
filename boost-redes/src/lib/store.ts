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

type MemStore = { entries: Map<string, Entry>; payments: Map<string, Payment> };

const g = globalThis as unknown as { __boostStore?: MemStore };
function mem(): MemStore {
  if (!g.__boostStore) {
    g.__boostStore = { entries: new Map(), payments: new Map() };
    seedDemo(g.__boostStore);
  }
  return g.__boostStore;
}

function uid() {
  return "id_" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

function seedDemo(store: MemStore) {
  const demo: Omit<Entry, "id" | "created_at">[] = [
    { handle: "@lucia.crea", platform: "instagram", url: "https://instagram.com/lucia.crea", message: "Diseño y hago reels que rompen 🔥", avatar_url: null, total_amount: 12500, boosts: 9 },
    { handle: "@martin.gg", platform: "twitch", url: "https://twitch.tv/martin_gg", message: "Streamer de Valorant, seguime que subo clips", avatar_url: null, total_amount: 8300, boosts: 6 },
    { handle: "@sofi.beats", platform: "spotify", url: "https://open.spotify.com/artist/demo", message: "Nuevo single afuera, dale play 🎧", avatar_url: null, total_amount: 6100, boosts: 4 },
    { handle: "@eltoto", platform: "tiktok", url: "https://tiktok.com/@eltoto", message: "Humor argento diario", avatar_url: null, total_amount: 3400, boosts: 3 },
    { handle: "@dev.nacho", platform: "youtube", url: "https://youtube.com/@devnacho", message: "Tutoriales de código en español", avatar_url: null, total_amount: 1500, boosts: 2 },
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

export async function rejectPayment(id: string): Promise<void> {
  if (usingSupabase) {
    await sb().from("payments").update({ status: "rejected" }).eq("id", id);
    return;
  }
  const p = mem().payments.get(id);
  if (p && p.status === "pending") p.status = "rejected";
}
