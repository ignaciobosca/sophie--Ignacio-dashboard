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
 * Foto de perfil de la red del usuario (vía unavatar), con fallback al logo
 * de la plataforma si no se encuentra o falla la carga.
 */
export default function Avatar({
  platform,
  handle,
  className = "h-12 w-12 bg-white/5",
  iconClassName = "h-6 w-6",
}: {
  platform: Platform;
  handle: string;
  className?: string;
  iconClassName?: string;
}) {
  const provider = UNAVATAR[platform];
  const user = handle.replace(/^@+/, "").trim();
  const [failed, setFailed] = useState(false);
  const showImg = Boolean(provider && user) && !failed;

  return (
    <div className={`grid shrink-0 place-items-center overflow-hidden rounded-full ${className}`}>
      {showImg ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`https://unavatar.io/${provider}/${encodeURIComponent(user)}?fallback=false`}
          alt={handle}
          referrerPolicy="no-referrer"
          loading="lazy"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
        />
      ) : (
        <PlatformIcon platform={platform} brand className={iconClassName} />
      )}
    </div>
  );
}
