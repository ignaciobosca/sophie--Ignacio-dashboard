import Link from "next/link";

export const dynamic = "force-dynamic";

export default function PendingPage() {
  return (
    <main className="grid min-h-screen place-items-center px-4">
      <div className="card w-full max-w-md rounded-3xl p-8 text-center">
        <div className="mb-3 text-5xl">⏳</div>
        <h1 className="text-2xl font-bold">Pago pendiente</h1>
        <p className="mt-2 text-white/60">
          Estamos esperando la confirmación de MercadoPago. Apenas se acredite,
          tu perfil sube automáticamente.
        </p>
        <Link
          href="/#ranking"
          className="btn-brand mt-6 inline-block rounded-full px-6 py-3 font-semibold text-white"
        >
          Volver al ranking
        </Link>
      </div>
    </main>
  );
}
