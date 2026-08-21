"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import type { PublicStats } from "@/lib/store";
import type { Platform } from "@/lib/types";
import Avatar from "./Avatar";

function money(n: number) {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);
}
function nf(n: number) {
  return new Intl.NumberFormat("es-AR").format(n);
}
function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "recién";
  if (m < 60) return `hace ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h} h`;
  const d = Math.floor(h / 24);
  return `hace ${d} d`;
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="card rounded-2xl p-4 text-center">
      <div className={`text-2xl font-black ${accent ? "text-brand-glow" : ""}`}>{value}</div>
      <div className="mt-1 text-[11px] uppercase tracking-wide text-white/40">{label}</div>
    </div>
  );
}

export default function StatsView({ initial }: { initial: PublicStats }) {
  const [s, setS] = useState<PublicStats>(initial);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/stats", { cache: "no-store" });
      const data = await res.json();
      if (data && typeof data.raised === "number") setS(data);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    const t = setInterval(refresh, 8000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <div className="mb-8 text-center">
        <Link href="/" className="text-sm text-white/40 hover:text-white">
          ← Volver
        </Link>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">📊 Estadísticas en vivo</h1>
        <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-400" />
          </span>
          <span className="font-semibold text-green-400">{nf(s.online)} en línea ahora</span>
        </div>
      </div>

      {/* Plata recaudada — el número estrella */}
      <div className="card mb-4 rounded-3xl border border-brand/30 bg-gradient-to-b from-brand/10 to-transparent p-6 text-center shadow-glow">
        <div className="text-xs uppercase tracking-wide text-white/40">Total boosteado</div>
        <div className="mt-1 text-4xl font-black text-brand-glow sm:text-5xl">{money(s.raised)}</div>
        <div className="mt-1 text-sm text-white/50">en {nf(s.boosts)} boost{s.boosts === 1 ? "" : "s"}</div>
      </div>

      {/* Grilla de métricas */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Stat label="En línea" value={nf(s.online)} accent />
        <Stat label="Última hora" value={nf(s.lastHour)} />
        <Stat label="Últimas 24 h" value={nf(s.last24h)} />
        <Stat label="Perfiles" value={nf(s.profiles)} />
        <Stat label="Boosts" value={nf(s.boosts)} />
        <Stat label="Clics a perfiles" value={nf(s.clicks)} />
      </div>

      {/* Actividad reciente */}
      <h2 className="mb-3 mt-10 text-sm font-semibold uppercase tracking-wide text-white/40">Actividad reciente</h2>
      {s.recent.length === 0 ? (
        <div className="card rounded-2xl p-6 text-center text-white/50">Todavía no hubo boosts. ¡Sé el primero!</div>
      ) : (
        <ul className="space-y-2">
          {s.recent.map((r, i) => (
            <li key={i} className="card flex items-center gap-3 rounded-2xl p-3">
              <Avatar
                platform={r.platform as Platform}
                handle={r.handle}
                className="h-9 w-9 bg-white/5"
                iconClassName="h-4 w-4"
              />
              <span className="min-w-0 flex-1 truncate">
                <span className="font-semibold">{r.handle}</span>
                <span className="text-white/50"> recibió un boost</span>
              </span>
              <span className="shrink-0 font-bold text-brand-glow">{money(r.amount)}</span>
              <span className="shrink-0 text-[11px] text-white/35">{timeAgo(r.created_at)}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-10 text-center">
        <Link href="/#ranking" className="btn-brand inline-block rounded-full px-6 py-3 font-semibold text-white">
          Sumar mi perfil
        </Link>
      </div>
    </main>
  );
}
