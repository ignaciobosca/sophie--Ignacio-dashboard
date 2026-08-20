import { NextResponse } from "next/server";
import { incrementClick } from "@/lib/store";
import { siteUrl } from "@/lib/payments";

export const dynamic = "force-dynamic";

/**
 * Redirect con conteo de clics.
 * /api/go/:id  ->  suma 1 clic al perfil y redirige a su URL destino.
 * Es el link que se usa en el ranking, así medimos el tráfico real que
 * recibe cada perfil (el gran diferencial de outbid.lol).
 */
export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const target = await incrementClick(id);

  if (!target) {
    return NextResponse.redirect(siteUrl());
  }

  // Seguridad: solo redirigimos a http/https (evita javascript:, data:, etc.)
  let safe: string;
  try {
    const u = new URL(target);
    if (!/^https?:$/.test(u.protocol)) throw new Error("bad protocol");
    safe = u.toString();
  } catch {
    return NextResponse.redirect(siteUrl());
  }

  return NextResponse.redirect(safe, { status: 302 });
}
