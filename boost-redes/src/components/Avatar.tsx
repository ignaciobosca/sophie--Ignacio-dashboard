"use client";

import { useState } from "react";
import type { Platform } from "@/lib/types";
import { PlatformIcon } from "./icons";

// Redes que unavatar sabe resolver por usuario.
const UNAVATAR: Partial<Record<Platform, string>> = {
  instagram: "instagram",
  x: "x",
  youtube: "youtube",
  tiktok: "tiktok",
  twitch: "twitch",
};

/**
 * Foto de perfil, con cascada de fuentes:
 *   1) foto subida por el usuario (src)
 *   2) foto pública de la red vía unavatar
 *   3) logo de la plataforma (siempre funciona)
 */
export default function Avatar({
  platform,
  handle,
  src,
  className = "h-12 w-12 bg-white/5",
  iconClassName = "h-6 w-6",
}: {
  platform: Platform;
  handle: string;
  src?: string | null;
  className?: string;
  iconClassName?: string;
}) {
  const user = handle.replace(/^@+/, "").trim();
  const provider = UNAVATAR[platform];

  const sources: string[] = [];
  if (src) sources.push(src);
  if (provider && user) sources.push(`https://unavatar.io/${provider}/${encodeURIComponent(user)}?fallback=false`);

  const [idx, setIdx] = useState(0);
  const current = sources[idx];

  return (
    <div className={`grid shrink-0 place-items-center overflow-hidden rounded-full ${className}`}>
      {current ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={current}
          alt={handle}
          referrerPolicy="no-referrer"
          loading="lazy"
          onError={() => setIdx((i) => i + 1)}
          className="h-full w-full object-cover"
        />
      ) : (
        <PlatformIcon platform={platform} brand className={iconClassName} />
      )}
    </div>
  );
}
