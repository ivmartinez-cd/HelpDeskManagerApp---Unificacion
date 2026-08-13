import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Acceso desde otras máquinas de la LAN (ej. para que un compañero pruebe
  // la app): Next.js bloquea por default los chunks JS/HMR si el browser no
  // pide el host desde localhost, y falla en silencio (la página carga pero
  // React nunca hidrata, así que el login no responde y no hay error en la UI).
  allowedDevOrigins: ["192.168.178.2"],
  experimental: {
    // El default de Next (proxy interno httpxy) corta cualquier rewrite a
    // los 30s. El login de Epson ERS vía Playwright (ver
    // playwright_ers_token_refresher.py) puede superar eso: solo el desafío
    // anti-bot de Incapsula demora ~45s desde un datacenter, y el token
    // puede tardar hasta 90s en aparecer — sin este override, Next mata la
    // conexión antes de que el backend responda y el usuario ve "Error de
    // Red" aunque el backend nunca haya fallado.
    proxyTimeout: 180_000,
  },
  async rewrites() {
    let backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8012";
    backendUrl = backendUrl
      .replace(/^http:\/([^/])/, "http://$1")
      .replace(/^https:\/([^/])/, "https://$1");
    if (backendUrl.endsWith("/")) {
      backendUrl = backendUrl.slice(0, -1);
    }
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
