# 🚀 Boost tus Redes

Un ranking público donde la gente **paga para posicionar sus redes sociales**
(Instagram, TikTok, YouTube, Twitch, etc.). Cuanto más boosteás, más arriba
aparecés — inspirado en [topapp.lol](https://topapp.lol/).

- **Frontend + backend:** Next.js 14 (App Router) + TypeScript + Tailwind
- **Base de datos:** Supabase (Postgres)
- **Pagos:** MercadoPago (Checkout Pro)
- **Modo demo:** corre sin ninguna credencial (datos en memoria + pago simulado)

---

## 🏁 Arranque rápido (modo demo)

```bash
cd boost-redes
npm install
npm run dev
```

Abrí http://localhost:3000. Ya viene con perfiles de ejemplo. Podés sumar tu
perfil y "pagar" (el pago se simula y el perfil sube al instante). **No hace
falta configurar nada** para probarlo.

> En modo demo los datos viven en memoria y se reinician al reiniciar el server.

---

## ⚙️ Pasar a producción

Copiá `.env.example` a `.env.local` y completá las credenciales.

### 1) Base de datos (Supabase)

1. Creá un proyecto en https://supabase.com
2. **SQL Editor → New query** → pegá y corré `supabase/schema.sql`
3. **Project Settings → API** → copiá:
   - `Project URL` → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` → `SUPABASE_SERVICE_ROLE_KEY` *(secreto, solo server)*

### 2) Pagos (MercadoPago)

1. Entrá a https://www.mercadopago.com.ar/developers → **Tus integraciones**
2. Creá una aplicación → **Credenciales de prueba** (empezá con `TEST-...`)
3. Copiá el **Access Token** → `MERCADOPAGO_ACCESS_TOKEN`
4. Configurá el **Webhook** apuntando a `https://TU-DOMINIO/api/webhook`
   (evento *Pagos*). En local podés usar [ngrok](https://ngrok.com).

### 3) Variables

```env
NEXT_PUBLIC_SITE_URL=https://tu-dominio.com
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxx
NEXT_PUBLIC_MIN_BOOST_ARS=500
```

Con estas variables la app deja de usar el modo demo automáticamente.

---

## 🧱 Cómo funciona

1. El usuario suma su perfil o elige uno existente y define un **monto**.
2. `POST /api/checkout` crea el perfil (si es nuevo) + un `payment` pendiente
   y genera la preferencia de MercadoPago → redirige al checkout.
3. MercadoPago cobra y notifica a `POST /api/webhook`.
4. El webhook marca el pago como aprobado y **suma el monto** al total del
   perfil (`increment_boost`), que reordena el ranking.

El ranking se ordena por `total_amount` desc. Los pagos son **acumulativos**:
podés seguir boosteando para escalar posiciones.

### 📈 Contador de clics (tráfico real)

Cada link del ranking pasa por un redirect propio `GET /api/go/:id` que **suma
un clic** al perfil y redirige a su URL destino. Así cada perfil ve cuánto
tráfico real le trajo su boost — el gran diferencial de estilo outbid.lol. Los
clics se muestran en cada fila (`👆 N clics`).

**Anti-inflado de clics:**

1. **Filtro de bots** (`src/lib/bot.ts`): no cuenta si el User-Agent parece
   crawler, preview de link (WhatsApp/Discord/Slack/Twitter), headless o cliente
   HTTP (curl/wget/requests/axios…), ni cuando falta el User-Agent.
2. **Dedup por visitante**: un mismo visitante (IP + cookie de sesión) suma como
   máximo **1 clic por perfil por ventana** (`CLICK_DEDUP_WINDOW_SECONDS`,
   default 1h). La IP se guarda **hasheada** (SHA-256) por privacidad.
3. En Supabase la lógica es atómica vía la RPC `register_click` + la tabla
   `click_log`; en modo demo se hace en memoria. El redirect **siempre**
   funciona aunque el clic no se cuente.

---

## 🚀 Deploy

La forma más simple es [Vercel](https://vercel.com):

1. Importá el repo (carpeta `boost-redes`).
2. Cargá las variables de entorno.
3. Deploy. Actualizá `NEXT_PUBLIC_SITE_URL` y el webhook de MercadoPago con la
   URL final.

---

## 📁 Estructura

```
src/
  app/
    page.tsx              # landing + ranking
    api/checkout/route.ts # inicia el pago
    api/webhook/route.ts  # confirma el pago (MercadoPago)
    api/entries/route.ts  # lista el ranking
    api/go/[id]/route.ts  # redirect con conteo de clics
    api/demo-pay/route.ts # simulación de pago (solo demo)
    success | pending | failure
  components/Ranking.tsx   # UI del ranking + modal de boost
  lib/
    store.ts               # Supabase o memoria
    payments.ts            # MercadoPago o demo
    validate.ts            # validación de inputs
    types.ts
supabase/schema.sql        # tablas + RPC + RLS
```
