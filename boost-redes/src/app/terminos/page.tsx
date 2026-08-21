import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Términos y Condiciones · Boost tus Redes",
};

export default function TerminosPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <Link href="/" className="text-sm text-white/40 hover:text-white">
        ← Volver
      </Link>
      <h1 className="mt-4 text-3xl font-extrabold tracking-tight">Términos y Condiciones</h1>
      <p className="mt-1 text-xs text-white/40">Última actualización: agosto 2026</p>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-white/70">
        <section>
          <h2 className="mb-1 font-semibold text-white">1. Qué es Boost tus Redes</h2>
          <p>
            Boost tus Redes es un ranking público donde los usuarios pagan para posicionar el
            enlace a su perfil de redes sociales. La posición depende del monto total pagado.
            Es un servicio de visibilidad y entretenimiento: <strong>no garantizamos seguidores,
            ventas ni resultados</strong>, ni tenemos relación con Instagram, TikTok, YouTube,
            Twitch u otras plataformas.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">2. Pagos</h2>
          <p>
            Los pagos se procesan a través de MercadoPago en pesos argentinos (ARS). Al pagar,
            tu perfil sube en el ranking según el monto acreditado. El boost es un servicio
            digital que se presta de inmediato.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">3. Reembolsos</h2>
          <p>
            Por tratarse de un servicio digital de acreditación inmediata,{" "}
            <strong>los pagos no son reembolsables</strong>, salvo error de cobro comprobable.
            Si un perfil es ocultado o eliminado por incumplir estos términos, no corresponde
            reembolso.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">4. Contenido del usuario</h2>
          <p>
            Sos responsable del usuario, enlace, texto e imagen que cargás. Está prohibido
            subir contenido ilegal, que incite al odio o la violencia, sexual explícito, que
            involucre a menores, o que viole derechos de terceros o de las plataformas.
            Podemos <strong>ocultar o eliminar</strong> cualquier perfil, con o sin reporte
            previo, sin derecho a reembolso.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">5. Responsabilidad</h2>
          <p>
            El servicio se ofrece "tal cual". No nos responsabilizamos por el uso que terceros
            hagan de los enlaces publicados ni por caídas temporales del servicio.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">6. Cambios y contacto</h2>
          <p>
            Podemos actualizar estos términos en cualquier momento. Ante cualquier duda o
            reclamo, escribinos a <strong>contacto@boost-tus-redes.com</strong>. Se aplica la
            legislación de la República Argentina.
          </p>
        </section>
      </div>

      <div className="mt-10 flex gap-4 text-xs text-white/40">
        <Link href="/privacidad" className="hover:text-white">Privacidad</Link>
        <Link href="/" className="hover:text-white">Inicio</Link>
      </div>
    </main>
  );
}
