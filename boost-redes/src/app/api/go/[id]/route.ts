import { NextResponse } from "next/server";
import { getEntry, countClick } from "@/lib/store";
import { siteUrl } from "@/lib/payments";
import { isBot, clientIp, dedupKey, newSessionId } from "@/lib/bot";

export const dynamic = "force-dynamic";

const WINDOW_SECONDS = Number(process.env.CLICK_DEDUP_WINDOW_SECONDS || 3600);
const SID_COOKIE = "bid_sid";

/**
 * Redirect con conteo de clics deduplicado.
 * /api/go/:id → cuenta 1 clic (por visitante y ventana) y redirige al perfil.
 *
 * Reglas de conteo:
 *  - No cuenta si el User-Agent parece bot / crawler / preview de link.
 *  - No cuenta si el mismo visitante (IP + sesión) ya sumó un clic a este
 *    perfil dentro de la ventana (default 1h).
 * El redirect SIEMPRE funciona, aunque el clic no se cuente.
 */
export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const entry = await getEntry(id);
  if (!entry) return NextResponse.redirect(siteUrl());

  // Seguridad: solo redirigimos a http/https (evita javascript:, data:, etc.)
  let safe: string;
  try {
    const u = new URL(entry.url);
    if (!/^https?:$/.test(u.protocol)) throw new Error("bad protocol");
    safe = u.toString();
  } catch {
    return NextResponse.redirect(siteUrl());
  }

  const res = NextResponse.redirect(safe, { status: 302 });

  // Sesión del visitante (cookie httpOnly de 1 año).
  const cookieHeader = req.headers.get("cookie") || "";
  const match = cookieHeader.match(/(?:^|;\s*)bid_sid=([^;]+)/);
  let sid = match?.[1];
  if (!sid) {
    sid = newSessionId();
    res.cookies.set(SID_COOKIE, sid, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: 60 * 60 * 24 * 365,
      path: "/",
    });
  }

  // Contamos solo tráfico humano y deduplicado.
  const ua = req.headers.get("user-agent");
  if (!isBot(ua)) {
    const key = dedupKey(clientIp(req.headers), sid);
    try {
      await countClick(id, key, WINDOW_SECONDS);
    } catch (err) {
      console.error("countClick", err);
    }
  }

  return res;
}
