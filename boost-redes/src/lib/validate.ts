import type { Platform } from "./types";
import { PLATFORMS } from "./types";

const MIN = Number(process.env.NEXT_PUBLIC_MIN_BOOST_ARS || 500);
const MAX = 5_000_000;

export interface CheckoutInput {
  entryId?: string;
  handle: string;
  platform: Platform;
  url: string;
  message: string;
  amount: number;
  photo?: string;
}

// Filtro de contenido: bloquea insultos de odio / slurs / explícito.
// (No bloquea puteadas leves; apunta a lo realmente ofensivo/ilegal.)
const BLOCKLIST = [
  // slurs / odio (es/en)
  "puto", "putos", "puta que", "trolo", "trava", "negro de mierda", "negra de mierda",
  "sudaca", "villero de mierda", "mogolico", "mogólico", "retrasado", "down de mierda",
  "faggot", "nigger", "nigga", "retard", "tranny", "kike", "spic", "chink",
  // sexual explícito / abuso
  "pornhub", "onlyfans.com", "xvideos", "xnxx", "child", "menor", "pedofil", "zoofil",
  "cp ", "cepe ", "violacion", "violación",
];

function hasBlockedContent(text: string): boolean {
  const t = text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, ""); // saca acentos
  return BLOCKLIST.some((w) => t.includes(w));
}

function validPhoto(v: unknown): string | undefined {
  if (typeof v !== "string") return undefined;
  if (!/^data:image\/(jpeg|png|webp);base64,/.test(v)) return undefined;
  if (v.length > 900_000) return undefined; // ~600 KB en base64
  return v;
}

export function parseCheckoutInput(body: any): { ok: true; value: CheckoutInput } | { ok: false; error: string } {
  if (!body || typeof body !== "object") return { ok: false, error: "Body inválido" };

  const amount = Math.floor(Number(body.amount));
  if (!Number.isFinite(amount) || amount < MIN) {
    return { ok: false, error: `El monto mínimo es $${MIN}` };
  }
  if (amount > MAX) return { ok: false, error: "Monto demasiado alto" };

  // Si viene entryId, es un boost sobre un perfil existente.
  if (body.entryId && typeof body.entryId === "string") {
    return {
      ok: true,
      value: { entryId: body.entryId, handle: "", platform: "otro", url: "", message: "", amount },
    };
  }

  const handleRaw = String(body.handle || "").trim();
  if (!handleRaw || handleRaw.length > 40) return { ok: false, error: "Usuario inválido" };
  const handle = handleRaw.startsWith("@") ? handleRaw : "@" + handleRaw.replace(/^@+/, "");

  const platform = String(body.platform || "").trim() as Platform;
  if (!PLATFORMS.some((p) => p.id === platform)) return { ok: false, error: "Plataforma inválida" };

  const url = String(body.url || "").trim();
  try {
    const u = new URL(url);
    if (!/^https?:$/.test(u.protocol)) throw new Error();
  } catch {
    return { ok: false, error: "Poné un link válido (https://...)" };
  }

  const message = String(body.message || "").trim().slice(0, 140);

  if (hasBlockedContent(`${handle} ${message}`)) {
    return { ok: false, error: "Ese contenido no está permitido." };
  }

  return { ok: true, value: { handle, platform, url, message, amount, photo: validPhoto(body.photo) } };
}
