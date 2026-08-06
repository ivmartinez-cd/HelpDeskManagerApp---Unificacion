import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

import { ThemeProvider } from "@/shared/components/theme-provider";
import { Toaster } from "sonner";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
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
    <html lang="es" className={`${outfit.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full bg-background text-foreground transition-colors duration-300">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-6 focus:py-3 focus:bg-accent focus:text-accent-foreground focus:rounded-xl focus:font-bold focus:shadow-2xl focus:outline-none transition-all"
          >
            Saltar al contenido principal
          </a>
          <main id="main-content">{children}</main>
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
