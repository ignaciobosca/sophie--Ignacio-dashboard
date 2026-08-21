import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Política de Privacidad · Boost tus Redes",
};

export default function PrivacidadPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <Link href="/" className="text-sm text-white/40 hover:text-white">
        ← Volver
      </Link>
      <h1 className="mt-4 text-3xl font-extrabold tracking-tight">Política de Privacidad</h1>
      <p className="mt-1 text-xs text-white/40">Última actualización: agosto 2026</p>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-white/70">
        <section>
          <h2 className="mb-1 font-semibold text-white">1. Qué datos guardamos</h2>
          <p>
            Guardamos lo que cargás al sumar tu perfil: usuario, plataforma, enlace, una frase
            opcional y una foto opcional. También registramos datos de uso anónimos (visitas y
            clics) para las estadísticas del sitio.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">2. Contenido público</h2>
          <p>
            El usuario, enlace, frase y foto que cargás <strong>son públicos</strong> y se
            muestran en el ranking a cualquier visitante. No subas información que no quieras
            hacer pública.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">3. Pagos</h2>
          <p>
            Los pagos los procesa <strong>MercadoPago</strong>. No almacenamos datos de tu
            tarjeta ni credenciales de pago; esa información la maneja MercadoPago según su
            propia política.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">4. Proveedores</h2>
          <p>
            Usamos servicios de terceros para funcionar: Supabase (base de datos y
            almacenamiento de fotos), Vercel (hosting y analítica de tráfico) y unavatar (para
            traer fotos públicas de perfil). Cada uno trata los datos según sus propias
            políticas.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">5. Cookies</h2>
          <p>
            Usamos una cookie técnica de sesión para contar visitantes de forma agregada y
            evitar conteos duplicados. No la usamos para publicidad.
          </p>
        </section>

        <section>
          <h2 className="mb-1 font-semibold text-white">6. Tus derechos y contacto</h2>
          <p>
            Podés pedir la eliminación de tu perfil y tu foto escribiéndonos a{" "}
            <strong>contacto@boost-tus-redes.com</strong>.
          </p>
        </section>
      </div>

      <div className="mt-10 flex gap-4 text-xs text-white/40">
        <Link href="/terminos" className="hover:text-white">Términos</Link>
        <Link href="/" className="hover:text-white">Inicio</Link>
      </div>
    </main>
  );
}
