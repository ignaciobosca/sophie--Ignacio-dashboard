import { createHash, randomUUID } from "crypto";

/**
 * Detección de tráfico no-humano para no inflar el contador de clics.
 * Cubre crawlers, previews de links (WhatsApp/Discord/Slack/Twitter),
 * herramientas headless y clientes HTTP (curl/wget/requests/axios...).
 */
const BOT_RE =
  /(bot|crawl|spider|slurp|mediapartners|facebookexternalhit|whatsapp|telegram|discord|slackbot|twitterbot|linkedinbot|pinterest|embedly|quora link preview|preview|headless|phantomjs|puppeteer|playwright|selenium|curl|wget|python-requests|python-urllib|aiohttp|httpclient|okhttp|axios|node-fetch|got |go-http-client|libwww|java\/|apache-httpclient|scrapy|semrush|ahrefs|mj12bot|dotbot|petalbot|bytespider|screaming frog|lighthouse|gtmetrix|pingdom|uptimerobot|monitis|statuscake|newrelic|datadog)/i;

export function isBot(ua: string | null): boolean {
  // Sin User-Agent (o demasiado corto) = sospechoso → no contamos.
  if (!ua || ua.trim().length < 5) return true;
  return BOT_RE.test(ua);
}

/**
 * IP del visitante a partir de los headers del proxy (Vercel/Cloudflare/etc.).
 */
export function clientIp(headers: Headers): string {
  const xff = headers.get("x-forwarded-for");
  if (xff) return xff.split(",")[0].trim();
  return (
    headers.get("x-real-ip") ||
    headers.get("cf-connecting-ip") ||
    headers.get("x-vercel-forwarded-for") ||
    "unknown"
  );
}

/**
 * Clave de dedup: hash de IP + sesión. Guardamos el hash (no la IP en claro)
 * por privacidad. Un mismo visitante = misma clave dentro de la ventana.
 */
export function dedupKey(ip: string, sid: string): string {
  return createHash("sha256").update(`${ip}|${sid}`).digest("hex").slice(0, 32);
}

export function newSessionId(): string {
  return randomUUID();
}
