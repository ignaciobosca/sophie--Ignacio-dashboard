import { NextResponse } from "next/server";
import { approvePayment, rejectPayment } from "@/lib/store";
import { fetchMercadoPagoPayment } from "@/lib/payments";

export const dynamic = "force-dynamic";

/**
 * Webhook de MercadoPago. MP notifica con { type: "payment", data: { id } }.
 * Buscamos el pago real en la API, leemos el external_reference (nuestro paymentId)
 * y aprobamos/rechazamos según el estado.
 */
export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const body = await req.json().catch(() => ({} as any));

    const type = body?.type || url.searchParams.get("type");
    const mpPaymentId =
      body?.data?.id || url.searchParams.get("data.id") || url.searchParams.get("id");

    if (type !== "payment" || !mpPaymentId) {
      // Otros eventos (merchant_order, etc.) los reconocemos pero no actuamos.
      return NextResponse.json({ received: true });
    }

    const mp = await fetchMercadoPagoPayment(String(mpPaymentId));
    if (!mp || !mp.externalReference) {
      return NextResponse.json({ received: true });
    }

    if (mp.status === "approved") {
      await approvePayment(mp.externalReference);
    } else if (mp.status === "rejected" || mp.status === "cancelled") {
      await rejectPayment(mp.externalReference);
    }

    return NextResponse.json({ received: true });
  } catch (err) {
    console.error("POST /api/webhook", err);
    // Devolvemos 200 igual para que MP no reintente en loop por errores nuestros.
    return NextResponse.json({ received: true });
  }
}

export async function GET() {
  return NextResponse.json({ ok: true });
}
