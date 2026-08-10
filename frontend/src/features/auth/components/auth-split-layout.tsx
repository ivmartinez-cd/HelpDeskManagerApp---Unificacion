import type { ReactNode } from "react";

interface AuthSplitLayoutProps {
  children: ReactNode;
}

/** Layout compartido por login, forgot-password y reset-password: panel de
 * marca Canal Directo a la izquierda (oculto <lg) + panel de formulario a la
 * derecha. Fidelidad pixel a pixel con el design handoff "Portal mesa de
 * ayuda corporativo_1 / Login Mesa de Ayuda.dc.html" (Etapa UI refactor). */
export function AuthSplitLayout({ children }: AuthSplitLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {/* Panel izquierdo: identidad de marca — oculto en pantallas chicas */}
      <div className="hidden lg:flex lg:w-[42%] lg:flex-none flex-col items-center justify-center bg-brand-charcoal px-12 relative overflow-hidden">
        <div
          aria-hidden="true"
          className="absolute rounded-full pointer-events-none"
          style={{
            width: 520,
            height: 520,
            top: -120,
            right: -140,
            background: "radial-gradient(circle, rgba(247,148,29,.18), transparent 70%)",
          }}
        />
        <div
          aria-hidden="true"
          className="absolute rounded-full pointer-events-none"
          style={{
            width: 420,
            height: 420,
            bottom: -100,
            left: -120,
            background: "radial-gradient(circle, rgba(88,89,91,.25), transparent 70%)",
          }}
        />
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG, next/image no aporta acá */}
        <img
          src="/isotipo-white.svg"
          alt=""
          aria-hidden="true"
          className="absolute pointer-events-none select-none opacity-[.08]"
          style={{ width: 340, height: "auto", bottom: -60, right: -60 }}
        />
        <div className="relative z-10 flex flex-col items-center gap-[22px] text-center max-w-[420px]">
          {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
          <img src="/logo-white.svg" alt="Canal Directo" className="h-9 w-auto object-contain" />
          <div className="h-0.5 w-12 bg-brand-orange" />
          <h1 className="font-heading text-[25px] font-extrabold leading-[1.3] text-white">
            Plataforma Unificada
            <br />
            de Operaciones
          </h1>
          <p className="font-body text-[14.5px] leading-relaxed text-white/65">
            Insumos, liquidaciones, vacaciones, análisis de logs de impresoras y monitoreo, todo
            en un solo lugar.
          </p>
        </div>
      </div>

      {/* Panel derecho: formulario */}
      <div className="flex flex-1 items-center justify-center bg-brand-surface px-6 py-12">
        <div className="w-full max-w-[360px]">
          <div className="mb-8 flex flex-col items-center lg:hidden">
            {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
            <img src="/logo.svg" alt="Canal Directo" className="h-9 w-auto object-contain" />
          </div>
          {children}
          <p className="mt-8 text-center font-body text-xs text-brand-muted">
            Portal interno · Canal Directo
          </p>
        </div>
      </div>
    </div>
  );
}
