import { NextResponse } from "next/server";
import { listEntries } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const entries = await listEntries();
    return NextResponse.json({ entries });
  } catch (err) {
    console.error("GET /api/entries", err);
    return NextResponse.json({ error: "No se pudo cargar el ranking" }, { status: 500 });
  }
}
