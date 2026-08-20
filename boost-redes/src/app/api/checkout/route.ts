import { NextResponse } from "next/server";
import { createEntry, createPayment, getEntry, setPaymentProviderRef } from "@/lib/store";
import { createCheckout } from "@/lib/payments";
import { parseCheckoutInput } from "@/lib/validate";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => null);
    const parsed = parseCheckoutInput(body);
    if (!parsed.ok) return NextResponse.json({ error: parsed.error }, { status: 400 });
    const input = parsed.value;

    // 1) Resolver el perfil: existente (boost) o nuevo.
    let entry;
    if (input.entryId) {
      entry = await getEntry(input.entryId);
      if (!entry) return NextResponse.json({ error: "El perfil no existe" }, { status: 404 });
    } else {
      entry = await createEntry({
        handle: input.handle,
        platform: input.platform,
        url: input.url,
        message: input.message,
      });
    }

    // 2) Crear el pago pendiente.
    const payment = await createPayment({ entry_id: entry.id, amount: input.amount });

    // 3) Crear el checkout (MercadoPago o demo).
    const checkout = await createCheckout({
      paymentId: payment.id,
      entryId: entry.id,
      handle: entry.handle,
      amount: input.amount,
    });

    if (checkout.providerRef) {
      await setPaymentProviderRef(payment.id, checkout.providerRef);
    }

    return NextResponse.json({
      checkoutUrl: checkout.checkoutUrl,
      paymentId: payment.id,
      entryId: entry.id,
      demo: checkout.demo,
    });
  } catch (err) {
    console.error("POST /api/checkout", err);
    return NextResponse.json({ error: "No se pudo iniciar el pago" }, { status: 500 });
  }
}
