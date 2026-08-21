import { siInstagram, siTiktok, siX, siYoutube, siTwitch, siKick, siSpotify } from "simple-icons";
import type { Platform } from "@/lib/types";

type Glyph = { title: string; hex: string; path: string };

const MAP: Record<Exclude<Platform, "otro">, Glyph> = {
  instagram: siInstagram,
  tiktok: siTiktok,
  x: siX,
  youtube: siYoutube,
  twitch: siTwitch,
  kick: siKick,
  spotify: siSpotify,
};

// Marcas cuyo color oficial es (casi) negro → se ven mejor en blanco sobre fondo oscuro.
const DARK = new Set<Platform>(["tiktok", "x"]);

export function PlatformIcon({
  platform,
  className = "h-5 w-5",
  brand = false,
}: {
  platform: Platform;
  className?: string;
  brand?: boolean;
}) {
  if (platform === "otro") {
    return (
      <svg
        viewBox="0 0 24 24"
        className={className}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-label="Otro"
      >
        <path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
        <path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
      </svg>
    );
  }
  const icon = MAP[platform];
  const fill = brand ? (DARK.has(platform) ? "#ffffff" : `#${icon.hex}`) : "currentColor";
  return (
    <svg role="img" viewBox="0 0 24 24" className={className} fill={fill} aria-label={icon.title}>
      <path d={icon.path} />
    </svg>
  );
}
