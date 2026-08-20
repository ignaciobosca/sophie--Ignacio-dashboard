export type Platform =
  | "instagram"
  | "tiktok"
  | "x"
  | "youtube"
  | "twitch"
  | "kick"
  | "spotify"
  | "otro";

export const PLATFORMS: { id: Platform; label: string; emoji: string }[] = [
  { id: "instagram", label: "Instagram", emoji: "📸" },
  { id: "tiktok", label: "TikTok", emoji: "🎵" },
  { id: "x", label: "X / Twitter", emoji: "𝕏" },
  { id: "youtube", label: "YouTube", emoji: "▶️" },
  { id: "twitch", label: "Twitch", emoji: "🎮" },
  { id: "kick", label: "Kick", emoji: "🟢" },
  { id: "spotify", label: "Spotify", emoji: "🎧" },
  { id: "otro", label: "Otro", emoji: "🔗" },
];

export interface Entry {
  id: string;
  handle: string;
  platform: Platform;
  url: string;
  message: string;
  avatar_url: string | null;
  total_amount: number;
  boosts: number;
  created_at: string;
}

export interface Payment {
  id: string;
  entry_id: string;
  amount: number;
  currency: string;
  status: "pending" | "approved" | "rejected";
  provider_ref: string | null;
  created_at: string;
}

export interface CheckoutResult {
  checkoutUrl: string;
  paymentId: string;
  entryId: string;
  demo: boolean;
}
