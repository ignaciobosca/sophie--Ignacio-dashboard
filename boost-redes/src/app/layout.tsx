import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Boost tus Redes — El ranking donde subís pagando",
  description:
    "Pagá para posicionar tu Instagram, TikTok, YouTube o Twitch en el ranking. Cuanto más boosteás, más arriba aparecés.",
  openGraph: {
    title: "Boost tus Redes",
    description: "El ranking donde subís pagando. Posicioná tus redes y ganá visibilidad.",
    type: "website",
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
