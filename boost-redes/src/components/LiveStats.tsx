"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

function nf(n: number) {
  return new Intl.NumberFormat("es-AR").format(n);
}

/**
 * Contador de prueba social: "N en línea · M en la última hora".
 * Hace ping a /api/hit al entrar y cada 20s (mantiene al visitante "en línea").
 */
export default function LiveStats() {
  const [stats, setStats] = useState<{ online: number; lastHour: number } | null>(null);

  useEffect(() => {
    let alive = true;
    const ping = async () => {
      try {
        const res = await fetch("/api/hit", { method: "POST" });
        const data = await res.json();
        if (alive && typeof data.online === "number") setStats(data);
      } catch {
        /* ignore */
      }
    };
    ping();
    const t = setInterval(ping, 20000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (!stats) return null;

  return (
    <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-green-400" />
      </span>
      <span className="font-semibold text-green-400">{nf(stats.online)} en línea</span>
      <span className="text-white/30">·</span>
      <span>{nf(stats.lastHour)} en la última hora</span>
      <span className="text-white/30">·</span>
      <Link href="/stats" className="font-semibold text-brand-glow hover:underline">
        ver stats →
      </Link>
    </div>
  );
}
