import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { ThemeProvider, ThemeScript } from "@/shared/components/theme-provider";
import { Toaster } from "sonner";

// Fuentes servidas desde el repo (subset latin, versión variable, licencia OFL)
// en vez de next/font/google: Google a veces devuelve URLs `/l/font?kit=...&...`
// que Turbopack no sabe resolver y rompe el arranque del frontend.
const outfit = localFont({
  src: "./fonts/outfit-latin-variable.woff2",
  variable: "--font-outfit",
  weight: "100 900",
});

// Tipografía de marca Canal Directo (manual de marca), usada hoy en las
// pantallas de auth — ver globals.css `--font-heading` / `--font-body`.
const montserrat = localFont({
  src: "./fonts/montserrat-latin-variable.woff2",
  variable: "--font-montserrat",
  weight: "600 800",
});

const sourceSans = localFont({
  src: "./fonts/source-sans-3-latin-variable.woff2",
  variable: "--font-source-sans",
  weight: "400 700",
});

export const metadata: Metadata = {
  title: {
    default: "HelpDesk Manager",
    template: "%s | HelpDesk Manager",
  },
  description: "Plataforma interna de gestión de operaciones y helpdesk",
  icons: {
    icon: "/favicon.svg",
  },
};

export const viewport = {
  themeColor: "#F97316",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${outfit.variable} ${montserrat.variable} ${sourceSans.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <ThemeScript />
      </head>
      <body
        className="min-h-full bg-background text-foreground transition-colors duration-300"
        suppressHydrationWarning
      >
        <ThemeProvider>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-6 focus:py-3 focus:bg-accent focus:text-accent-foreground focus:rounded-xl focus:font-bold focus:shadow-2xl focus:outline-none transition-all"
          >
            Saltar al contenido principal
          </a>
          <main id="main-content">{children}</main>
          <Toaster richColors position="top-right" closeButton />
        </ThemeProvider>
      </body>
    </html>
  );
}
