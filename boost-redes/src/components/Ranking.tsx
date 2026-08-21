"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Entry, Platform } from "@/lib/types";
import { PLATFORMS } from "@/lib/types";
import { PlatformIcon } from "./icons";
import PlatformSelect from "./PlatformSelect";
import Avatar from "./Avatar";

const MIN = Number(process.env.NEXT_PUBLIC_MIN_BOOST_ARS || 500);

function fmt(n: number) {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);
}

function nf(n: number) {
  return new Intl.NumberFormat("es-AR").format(n);
}

function platformMeta(id: Platform) {
  return PLATFORMS.find((p) => p.id === id) ?? PLATFORMS[PLATFORMS.length - 1];
}

function medal(rank: number) {
  if (rank === 1) return { ring: "ring-gold", badge: "bg-gold text-black", label: "🥇" };
  if (rank === 2) return { ring: "ring-silver", badge: "bg-silver text-black", label: "🥈" };
  if (rank === 3) return { ring: "ring-bronze", badge: "bg-bronze text-black", label: "🥉" };
  return { ring: "ring-white/10", badge: "bg-white/10 text-white", label: String(rank) };
}

const QUICK = [500, 1000, 2500, 5000];

const STEPS = [
  { n: "1", t: "Sumá tu perfil", d: "Elegí tu red y pegá el link." },
  { n: "2", t: "Pagá tu boost", d: "El monto define tu posición." },
  { n: "3", t: "Escalá el ranking", d: "Sumá más para pasar a los de arriba." },
];

// Achica y comprime la imagen en el navegador antes de subirla (avatar liviano).
async function compressImage(file: File, max = 400, quality = 0.82): Promise<string> {
  const dataUrl: string = await new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result as string);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
  const img: HTMLImageElement = await new Promise((res, rej) => {
    const i = new Image();
    i.onload = () => res(i);
    i.onerror = rej;
    i.src = dataUrl;
  });
  const scale = Math.min(1, max / Math.max(img.width, img.height));
  const w = Math.round(img.width * scale);
  const h = Math.round(img.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return dataUrl;
  ctx.drawImage(img, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", quality);
}

export default function Ranking({ initialEntries }: { initialEntries: Entry[] }) {
  const [entries, setEntries] = useState<Entry[]>(initialEntries);
  const [open, setOpen] = useState(false);
  const [target, setTarget] = useState<Entry | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/entries", { cache: "no-store" });
      const data = await res.json();
      if (Array.isArray(data.entries)) setEntries(data.entries);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    const t = setInterval(refresh, 8000);
    return () => clearInterval(t);
  }, [refresh]);

  const openNew = () => {
    setTarget(null);
    setOpen(true);
  };
  const openBoost = (e: Entry) => {
    setTarget(e);
    setOpen(true);
  };

  const [reported, setReported] = useState<Set<string>>(new Set());
  const report = async (e: Entry) => {
    if (reported.has(e.id)) return;
    if (!confirm(`¿Reportar ${e.handle} por contenido inapropiado?`)) return;
    setReported((s) => new Set(s).add(e.id));
    try {
      await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entryId: e.id }),
      });
    } catch {
      /* ignore */
    }
  };

  const leader = entries[0];
  const top3 = entries.slice(0, 3);
  const rest = entries.slice(3);

  const renderRow = (e: Entry, rank: number) => {
    const m = medal(rank);
    const meta = platformMeta(e.platform);
    return (
      <li key={e.id} className={`card animate-rise rounded-2xl p-3 ring-1 ${m.ring} sm:p-4`}>
        <div className="flex items-center gap-3 sm:gap-4">
          <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold ${m.badge}`}>
            {m.label}
          </div>

          <Avatar platform={e.platform} handle={e.handle} src={e.avatar_url} className="h-12 w-12 bg-white/5" iconClassName="h-6 w-6" />

          {/* Identidad: el @usuario es el protagonista */}
          <div className="min-w-0 flex-1">
            <a
              href={`/api/go/${e.id}`}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="block truncate text-lg font-extrabold leading-tight tracking-tight hover:text-brand-glow sm:text-xl"
            >
              {e.handle}
            </a>
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-white/45">
              <span className="inline-flex items-center gap-1 rounded-full bg-brand/20 px-2 py-0.5 font-semibold text-brand-glow">
                <PlatformIcon platform={e.platform} className="h-3 w-3" /> {meta.label}
              </span>
              <span>👆 {nf(e.clicks)} clic{e.clicks === 1 ? "" : "s"}</span>
              <span className="text-white/25">·</span>
              <span>⚡ {e.boosts} boost{e.boosts === 1 ? "" : "s"}</span>
              <button
                onClick={() => report(e)}
                className="text-white/25 hover:text-white/70"
                title="Reportar contenido inapropiado"
              >
                · {reported.has(e.id) ? "reportado ✓" : "reportar"}
              </button>
            </div>
          </div>

          <div className="shrink-0 text-right">
            <div className="text-base font-bold text-brand-glow sm:text-lg">{fmt(e.total_amount)}</div>
            <div className="text-[10px] uppercase tracking-wide text-white/35">boosteado</div>
          </div>
        </div>

        {/* Segunda línea: frase + botón Boost */}
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="min-w-0 flex-1 truncate text-sm text-white/50">{e.message || " "}</p>
          <button
            onClick={() => openBoost(e)}
            className="btn-brand shrink-0 rounded-full px-5 py-2 text-sm font-semibold text-white"
          >
            ⚡ Boost
          </button>
        </div>
      </li>
    );
  };

  const renderChampion = (e: Entry) => {
    const meta = platformMeta(e.platform);
    return (
      <div className="animate-rise relative mb-3 overflow-hidden rounded-3xl border border-gold/40 bg-gradient-to-b from-gold/10 to-transparent p-4 shadow-[0_0_55px_-12px_rgba(245,197,66,0.55)] sm:p-5">
        <div className="mb-3">
          <span className="rounded-full bg-gold px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide text-black">
            👑 #1 · Campeón
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <Avatar
            platform={e.platform}
            handle={e.handle}
            src={e.avatar_url}
            className="h-16 w-16 bg-gold/15 ring-2 ring-gold/60"
            iconClassName="h-8 w-8"
          />

          <div className="min-w-0 flex-1">
            <a
              href={`/api/go/${e.id}`}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="block truncate text-2xl font-black leading-tight tracking-tight hover:text-gold sm:text-3xl"
            >
              {e.handle}
            </a>
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-white/55">
              <span className="inline-flex items-center gap-1 rounded-full bg-gold/20 px-2 py-0.5 font-semibold text-gold">
                <PlatformIcon platform={e.platform} className="h-3 w-3" /> {meta.label}
              </span>
              <span>👆 {nf(e.clicks)} clic{e.clicks === 1 ? "" : "s"}</span>
              <span className="text-white/25">·</span>
              <span>⚡ {e.boosts} boost{e.boosts === 1 ? "" : "s"}</span>
              <button
                onClick={() => report(e)}
                className="text-white/30 hover:text-white/80"
                title="Reportar contenido inapropiado"
              >
                · {reported.has(e.id) ? "reportado ✓" : "reportar"}
              </button>
            </div>
          </div>

          <div className="shrink-0 text-right">
            <div className="text-xl font-black text-gold sm:text-2xl">{fmt(e.total_amount)}</div>
            <div className="text-[10px] uppercase tracking-wide text-white/40">boosteado</div>
          </div>
        </div>

        {e.message && <p className="mt-3 truncate text-sm text-white/60">{e.message}</p>}

        <button
          onClick={() => openBoost(e)}
          className="mt-4 w-full rounded-xl bg-gold py-3 text-sm font-extrabold text-black transition hover:brightness-105 active:translate-y-px"
        >
          ⚡ Boostear al #1
        </button>
      </div>
    );
  };

  return (
    <section id="ranking" className="mx-auto w-full max-w-3xl px-4 pb-28">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-xl font-semibold tracking-tight">🏆 Top boosteados</h2>
        <button
          onClick={openNew}
          className="btn-brand rounded-full px-4 py-2 text-sm font-semibold text-white"
        >
          + Sumar mi perfil
        </button>
      </div>

      {entries.length === 0 && (
        <div className="card rounded-2xl p-8 text-center text-white/60">
          Todavía no hay nadie.{" "}
          <button onClick={openNew} className="text-brand-glow underline">
            Sé el primero
          </button>
          .
        </div>
      )}

      {/* TOP 3 — arriba de todo: el #1 destacado como campeón */}
      {top3.length > 0 && (
        <div>
          {renderChampion(top3[0])}
          {top3.length > 1 && (
            <ul className="space-y-3">{top3.slice(1).map((e, i) => renderRow(e, i + 2))}</ul>
          )}
        </div>
      )}

      {/* Cómo funciona — en el medio */}
      <div className="my-10">
        <h3 className="mb-3 text-center text-xs font-semibold uppercase tracking-wide text-white/40">
          Cómo funciona
        </h3>
        <div className="grid gap-3 sm:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="card rounded-2xl p-4">
              <div className="mb-2 grid h-8 w-8 place-items-center rounded-full bg-brand/20 text-sm font-bold text-brand-glow">
                {s.n}
              </div>
              <div className="font-semibold">{s.t}</div>
              <div className="text-sm text-white/50">{s.d}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Del 4° en adelante — abajo */}
      {rest.length > 0 && (
        <>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-white/40">
            Del 4° en adelante
          </h3>
          <ul className="space-y-3">{rest.map((e, i) => renderRow(e, i + 4))}</ul>
        </>
      )}

      <p className="mt-8 text-center text-xs text-white/30">
        El ranking se ordena por el total boosteado. Podés seguir sumando para escalar posiciones.
      </p>

      {open && (
        <BoostModal
          target={target}
          leaderAmount={leader?.total_amount ?? 0}
          onClose={() => setOpen(false)}
        />
      )}
    </section>
  );
}

function BoostModal({
  target,
  leaderAmount,
  onClose,
}: {
  target: Entry | null;
  leaderAmount: number;
  onClose: () => void;
}) {
  const [amount, setAmount] = useState<number>(QUICK[1]);
  const [handle, setHandle] = useState("");
  const [platform, setPlatform] = useState<Platform>("instagram");
  const [url, setUrl] = useState("");
  const [message, setMessage] = useState("");
  const [photo, setPhoto] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onPickPhoto(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    try {
      setPhoto(await compressImage(file));
    } catch {
      setError("No se pudo procesar la imagen");
    }
  }

  const toBeatLeader = useMemo(() => Math.max(MIN, leaderAmount + 100 - (target?.total_amount ?? 0)), [leaderAmount, target]);

  async function submit() {
    setError(null);
    if (amount < MIN) {
      setError(`El monto mínimo es ${fmt(MIN)}`);
      return;
    }
    setLoading(true);
    try {
      const payload = target
        ? { entryId: target.id, amount }
        : { handle, platform, url, message, amount, photo };
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Algo salió mal");
        setLoading(false);
        return;
      }
      window.location.href = data.checkoutUrl;
    } catch {
      setError("No se pudo conectar. Probá de nuevo.");
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-md rounded-3xl p-6"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h3 className="text-lg font-semibold">
            {target ? `⚡ Boostear ${target.handle}` : "🚀 Sumá tu perfil"}
          </h3>
          <button onClick={onClose} className="text-white/40 hover:text-white">✕</button>
        </div>

        {!target && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs text-white/50">Usuario</label>
                <input
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  placeholder="@tuusuario"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-white/50">Plataforma</label>
                <PlatformSelect value={platform} onChange={setPlatform} />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-white/50">Link a tu perfil</label>
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://instagram.com/tuusuario"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-white/50">
                Frase corta <span className="text-white/30">(opcional, 140)</span>
              </label>
              <input
                value={message}
                maxLength={140}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Contá en una línea por qué te sigan"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-white/50">
                Foto de perfil <span className="text-white/30">(opcional)</span>
              </label>
              <div className="flex items-center gap-3">
                <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-full border border-white/10 bg-white/5">
                  {photo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={photo} alt="preview" className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-lg text-white/40">📷</span>
                  )}
                </div>
                <label className="cursor-pointer rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70 hover:border-white/25">
                  {photo ? "Cambiar" : "Subir foto"}
                  <input type="file" accept="image/*" className="hidden" onChange={onPickPhoto} />
                </label>
                {photo && (
                  <button
                    type="button"
                    onClick={() => setPhoto(null)}
                    className="text-xs text-white/40 hover:text-white"
                  >
                    Quitar
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="mt-4">
          <label className="mb-1 block text-xs text-white/50">Monto del boost (ARS)</label>
          <div className="mb-2 grid grid-cols-4 gap-2">
            {QUICK.map((q) => (
              <button
                key={q}
                onClick={() => setAmount(q)}
                className={`rounded-xl border px-2 py-2 text-sm font-semibold transition ${
                  amount === q
                    ? "border-brand bg-brand/20 text-white"
                    : "border-white/10 bg-white/5 text-white/70 hover:border-white/25"
                }`}
              >
                ${q.toLocaleString("es-AR")}
              </button>
            ))}
          </div>
          <input
            type="number"
            min={MIN}
            value={amount}
            onChange={(e) => setAmount(Math.floor(Number(e.target.value)))}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          {target && leaderAmount > 0 && (
            <button
              onClick={() => setAmount(toBeatLeader)}
              className="mt-2 text-xs text-brand-glow underline"
            >
              Pagar {fmt(toBeatLeader)} para pasar al #1
            </button>
          )}
        </div>

        {error && <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</p>}

        <button
          onClick={submit}
          disabled={loading}
          className="btn-brand mt-5 w-full rounded-xl py-3 font-semibold text-white disabled:opacity-60"
        >
          {loading ? "Redirigiendo…" : `Pagar ${fmt(amount)} y boostear`}
        </button>
        <p className="mt-3 text-center text-[11px] text-white/30">
          Pago seguro con MercadoPago. Tu perfil sube apenas se acredita.
        </p>
      </div>
    </div>
  );
}
