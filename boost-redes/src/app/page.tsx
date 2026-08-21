import Ranking from "@/components/Ranking";
import { listEntries, usingSupabase } from "@/lib/store";
import { usingMercadoPago } from "@/lib/payments";

export const dynamic = "force-dynamic";

export default async function Home() {
  const entries = await listEntries();
  const demo = !usingMercadoPago || !usingSupabase;

  return (
    <main className="min-h-screen">
      {demo && (
        <div className="bg-brand/20 px-4 py-2 text-center text-xs text-brand-glow">
          ⚙️ Modo demo — los pagos son simulados{!usingSupabase ? " y los datos se guardan en memoria" : ""}.
          Configurá las credenciales para pasar a producción.
        </div>
      )}

      {/* Hero */}
      <header className="mx-auto max-w-3xl px-4 pt-14 pb-10 text-center sm:pt-20">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60">
          🔥 El ranking donde subís pagando
        </div>
        <h1 className="text-balance text-4xl font-extrabold tracking-tight sm:text-6xl">
          Boost tus{" "}
          <span className="bg-gradient-to-r from-brand-glow to-gold bg-clip-text text-transparent">
            Redes
          </span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-pretty text-white/60 sm:text-lg">
          Posicioná tu Instagram, TikTok, YouTube o Twitch en el ranking público.
          Cuanto más boosteás, más arriba aparecés — y más gente te descubre.
        </p>
        <div className="mt-7 flex items-center justify-center gap-3">
          <a
            href="#ranking"
            className="btn-brand rounded-full px-6 py-3 font-semibold text-white"
          >
            Ver el ranking ↓
          </a>
        </div>
      </header>

      <Ranking initialEntries={entries} />

      <footer className="border-t border-white/5 px-4 py-8 text-center text-xs text-white/30">
        Boost tus Redes · Hecho con Next.js + MercadoPago · Subí de forma responsable.
      </footer>
    </main>
  );
}
