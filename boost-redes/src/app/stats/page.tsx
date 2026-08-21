import type { Metadata } from "next";
import StatsView from "@/components/StatsView";
import { getPublicStats } from "@/lib/store";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Estadísticas en vivo · Boost tus Redes",
  description: "Cuánto se movió, cuántos están online y la actividad reciente del ranking.",
};

export default async function StatsPage() {
  const stats = await getPublicStats();
  return <StatsView initial={stats} />;
}
