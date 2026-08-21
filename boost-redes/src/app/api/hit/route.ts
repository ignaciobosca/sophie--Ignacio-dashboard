import { NextResponse } from "next/server";
import { recordVisit, getVisitorStats } from "@/lib/store";
import { isBot, newSessionId } from "@/lib/bot";

export const dynamic = "force-dynamic";

const SID_COOKIE = "bid_sid";

/**
 * Ping de presencia. El front lo llama al entrar y cada ~20s.
 * Registra la sesión (si no es bot) y devuelve { online, lastHour }.
 */
export async function POST(req: Request) {
  const cookieHeader = req.headers.get("cookie") || "";
  const match = cookieHeader.match(/(?:^|;\s*)bid_sid=([^;]+)/);
  let sid = match?.[1];
  const isNewSid = !sid;
  if (!sid) sid = newSessionId();

  const ua = req.headers.get("user-agent");

  let stats;
  try {
    stats = isBot(ua) ? await getVisitorStats() : await recordVisit(sid);
  } catch (err) {
    console.error("POST /api/hit", err);
    stats = { online: 0, lastHour: 0 };
  }

  const res = NextResponse.json(stats);
  if (isNewSid) {
    res.cookies.set(SID_COOKIE, sid, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: 60 * 60 * 24 * 365,
      path: "/",
    });
  }
  return res;
}
