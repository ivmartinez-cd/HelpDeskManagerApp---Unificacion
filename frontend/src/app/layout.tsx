import type { Metadata } from "next";
import { Outfit, Montserrat, Source_Sans_3 } from "next/font/google";
import "./globals.css";

import { ThemeProvider } from "@/shared/components/theme-provider";
import { Toaster } from "sonner";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

// Tipografía de marca Canal Directo (manual de marca), usada hoy en las
// pantallas de auth — ver globals.css `--font-heading` / `--font-body`.
const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

const sourceSans = Source_Sans_3({
  variable: "--font-source-sans",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
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
      <body
        className="min-h-full bg-background text-foreground transition-colors duration-300"
        suppressHydrationWarning
      >
        <ThemeProvider attribute="class" defaultTheme="dark" disableTransitionOnChange>
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
