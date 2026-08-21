import { NextResponse } from "next/server";
import { reportEntry, checkRateLimit } from "@/lib/store";
import { clientIp, dedupKey } from "@/lib/bot";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => null);
    const entryId = body?.entryId;
    if (!entryId || typeof entryId !== "string") {
      return NextResponse.json({ error: "Falta el perfil" }, { status: 400 });
    }

    // Anti-abuso: máx 10 reportes por IP por hora.
    const ipKey = "report:" + dedupKey(clientIp(req.headers), "");
    if (!(await checkRateLimit(ipKey, 10, 3600))) {
      return NextResponse.json({ error: "Demasiados reportes." }, { status: 429 });
    }

    await reportEntry(entryId);
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("POST /api/report", err);
    return NextResponse.json({ error: "No se pudo reportar" }, { status: 500 });
  }
}
