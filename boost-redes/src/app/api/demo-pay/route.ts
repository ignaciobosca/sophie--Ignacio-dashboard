import { NextResponse } from "next/server";
import { approvePayment } from "@/lib/store";
import { usingMercadoPago, siteUrl } from "@/lib/payments";

export const dynamic = "force-dynamic";

/**
 * Ruta SOLO para modo demo (sin MercadoPago configurado).
 * Simula que el pago fue aprobado y redirige a la pantalla de éxito.
 */
export async function GET(req: Request) {
  const base = siteUrl();
  if (usingMercadoPago) {
    // En producción esta ruta no debe usarse.
    return NextResponse.redirect(`${base}/failure`);
  }
  const url = new URL(req.url);
  const paymentId = url.searchParams.get("payment_id");
  if (!paymentId) return NextResponse.redirect(`${base}/failure`);

  await approvePayment(paymentId);
  return NextResponse.redirect(`${base}/success?payment_id=${paymentId}&demo=1`);
}
