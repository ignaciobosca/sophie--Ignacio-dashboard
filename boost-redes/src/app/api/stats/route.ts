import { NextResponse } from "next/server";
import { getPublicStats } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const stats = await getPublicStats();
    return NextResponse.json(stats);
  } catch (err) {
    console.error("GET /api/stats", err);
    return NextResponse.json({ error: "No se pudieron cargar las estadísticas" }, { status: 500 });
  }
}
