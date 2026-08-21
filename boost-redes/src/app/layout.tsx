import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://boost-tus-redes.com"),
  title: "Boost tus Redes — El ranking donde subís pagando",
  description:
    "Pagá para posicionar tu Instagram, TikTok, YouTube o Twitch en el ranking. Cuanto más boosteás, más arriba aparecés.",
  openGraph: {
    title: "Boost tus Redes",
    description: "El ranking donde subís pagando. Posicioná tus redes y ganá visibilidad.",
    url: "https://boost-tus-redes.com",
    siteName: "Boost tus Redes",
    type: "website",
    locale: "es_AR",
  },
  twitter: {
    card: "summary_large_image",
    title: "Boost tus Redes",
    description: "El ranking donde subís pagando. Posicioná tus redes y ganá visibilidad.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="antialiased">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
