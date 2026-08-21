import { MercadoPagoConfig, Preference } from "mercadopago";

const ACCESS_TOKEN = process.env.MERCADOPAGO_ACCESS_TOKEN;

export const usingMercadoPago = Boolean(ACCESS_TOKEN);

export function siteUrl(): string {
  // 1) Si la definís a mano, mandamos esa (ideal en producción con MercadoPago).
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL;
  // 2) En Vercel, usamos su dominio automáticamente (no hay que configurar nada).
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL)
    return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  // 3) Desarrollo local.
  return "http://localhost:3000";
}

/**
 * Crea una preferencia de pago en MercadoPago y devuelve la URL de checkout.
 * En modo demo (sin ACCESS_TOKEN) devuelve una URL local que simula el pago.
 */
export async function createCheckout(params: {
  paymentId: string;
  entryId: string;
  handle: string;
  amount: number;
}): Promise<{ checkoutUrl: string; providerRef: string | null; demo: boolean }> {
  const base = siteUrl();

  if (!usingMercadoPago) {
    // MODO DEMO: mandamos al usuario a una ruta que confirma el pago simulado.
    const url = `${base}/api/demo-pay?payment_id=${encodeURIComponent(params.paymentId)}`;
    return { checkoutUrl: url, providerRef: null, demo: true };
  }

  const client = new MercadoPagoConfig({ accessToken: ACCESS_TOKEN! });
  const preference = new Preference(client);

  const result = await preference.create({
    body: {
      items: [
        {
          id: params.entryId,
          title: `Boost para ${params.handle}`,
          description: "Posicioná tu perfil en el ranking de Boost tus Redes",
          quantity: 1,
          unit_price: params.amount,
          currency_id: "ARS",
        },
      ],
      external_reference: params.paymentId,
      back_urls: {
        success: `${base}/success?payment_id=${params.paymentId}`,
        pending: `${base}/pending?payment_id=${params.paymentId}`,
        failure: `${base}/failure?payment_id=${params.paymentId}`,
      },
      auto_return: "approved",
      notification_url: `${base}/api/webhook`,
      metadata: { payment_id: params.paymentId, entry_id: params.entryId },
    },
  });

  const checkoutUrl = result.init_point || result.sandbox_init_point;
  if (!checkoutUrl) throw new Error("MercadoPago no devolvió init_point");
  return { checkoutUrl, providerRef: result.id ?? null, demo: false };
}

/**
 * Consulta el estado de un pago en MercadoPago por su id.
 */
export async function fetchMercadoPagoPayment(
  mpPaymentId: string
): Promise<{ status: string; externalReference: string | null } | null> {
  if (!usingMercadoPago) return null;
  const res = await fetch(`https://api.mercadopago.com/v1/payments/${mpPaymentId}`, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  const data = await res.json();
  return {
    status: data.status,
    externalReference: data.external_reference ?? null,
  };
}
