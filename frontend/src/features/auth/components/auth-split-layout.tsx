import type { ReactNode } from "react";
import { HelpDeskLogo } from "@/shared/components/helpdesk-logo";

interface AuthSplitLayoutProps {
  children: ReactNode;
}

/** Layout compartido por login, forgot-password y reset-password: panel de
 * marca a la izquierda (oculto <lg) + panel de formulario a la derecha.
 * Extraído de login-form.tsx para no repetir este JSX en cada pantalla de
 * auth (Etapa 13.5). */
export function AuthSplitLayout({ children }: AuthSplitLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {/* Panel izquierdo: identidad de marca — oculto en pantallas chicas */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center bg-[#1a1a1a] px-12 relative overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG, next/image no aporta acá */}
        <img
          src="/isotipo.svg"
          alt=""
          aria-hidden="true"
          className="absolute -bottom-16 -right-16 h-80 w-80 opacity-5 select-none pointer-events-none"
        />
        <div className="relative z-10 flex flex-col items-center text-center max-w-sm">
          <HelpDeskLogo size="lg" className="mb-8" />
          <div className="w-12 h-0.5 bg-accent mb-8 rounded-full" />
          {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
          <img src="/logo-white.svg" alt="Canal Directo" className="h-8 w-auto mb-8 opacity-70" />
          <h1 className="text-2xl font-bold text-white leading-snug">
            Plataforma Unificada
            <br />
            de Operaciones
          </h1>
          <p className="mt-4 text-sm text-white/50 leading-relaxed">
            Insumos, liquidaciones, vacaciones, parque de impresoras y monitoreo, todo en un
            solo lugar.
          </p>
        </div>
      </div>

      {/* Panel derecho: formulario */}
      <div className="flex flex-1 items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center lg:hidden">
            {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
            <img src="/logo.svg" alt="HelpDesk Manager" className="h-10 w-auto" />
          </div>
          {children}
          <p className="mt-8 text-center text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} HelpDesk Manager. Uso interno.
          </p>
        </div>
      </div>
    </div>
  );
}
