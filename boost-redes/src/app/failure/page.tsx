import Link from "next/link";

export const dynamic = "force-dynamic";

export default function FailurePage() {
  return (
    <main className="grid min-h-screen place-items-center px-4">
      <div className="card w-full max-w-md rounded-3xl p-8 text-center">
        <div className="mb-3 text-5xl">😕</div>
        <h1 className="text-2xl font-bold">No se pudo procesar el pago</h1>
        <p className="mt-2 text-white/60">
          No te preocupes, no se te cobró nada. Podés intentarlo de nuevo cuando quieras.
        </p>
        <Link
          href="/#ranking"
          className="btn-brand mt-6 inline-block rounded-full px-6 py-3 font-semibold text-white"
        >
          Intentar de nuevo
        </Link>
      </div>
    </main>
  );
}
