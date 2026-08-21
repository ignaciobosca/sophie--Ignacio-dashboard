import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Boost tus Redes — el ranking donde subís pagando";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0a0a0f",
          backgroundImage:
            "radial-gradient(1200px 600px at 50% -10%, #1b1440 0%, #0a0a0f 60%)",
          color: "white",
          fontFamily: "sans-serif",
          padding: "60px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: "999px",
            padding: "12px 26px",
            fontSize: "30px",
            color: "rgba(255,255,255,0.75)",
          }}
        >
          🔥 El ranking donde subís pagando
        </div>

        <div style={{ display: "flex", fontSize: "128px", fontWeight: 800, marginTop: "28px", letterSpacing: "-4px" }}>
          <span style={{ marginRight: "28px" }}>Boost tus</span>
          <span style={{ color: "#a78bfa" }}>Redes</span>
        </div>

        <div
          style={{
            display: "flex",
            fontSize: "38px",
            color: "rgba(255,255,255,0.6)",
            marginTop: "26px",
            textAlign: "center",
            maxWidth: "920px",
          }}
        >
          Pagá para posicionar tu Instagram, TikTok, YouTube o Twitch. El que más paga queda #1 👑
        </div>

        <div style={{ display: "flex", fontSize: "36px", fontWeight: 700, color: "#a78bfa", marginTop: "54px" }}>
          boost-tus-redes.com
        </div>
      </div>
    ),
    { ...size, emoji: "twemoji" }
  );
}
