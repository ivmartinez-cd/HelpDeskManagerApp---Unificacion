import Link from "next/link";
import { TOOLS, type ToolKey } from "@/features/contadores/tool-catalog";

const CARD_COLOR: Record<ToolKey, { badge: string; fg: string }> = {
  calendario: { badge: "bg-brand-orange/[0.12]", fg: "text-brand-orange" },
  sds: { badge: "bg-brand-orange/[0.12]", fg: "text-brand-orange" },
  ers: { badge: "bg-brand-orange/[0.12]", fg: "text-brand-orange" },
  ftp: { badge: "bg-brand-charcoal/[0.1]", fg: "text-foreground" },
  db3: { badge: "bg-brand-gray/[0.12]", fg: "text-brand-gray" },
  en0: { badge: "bg-brand-orange/[0.12]", fg: "text-brand-orange" },
  "suma-fija": { badge: "bg-brand-orange/[0.12]", fg: "text-brand-orange" },
  proyeccion: { badge: "bg-brand-charcoal/[0.1]", fg: "text-foreground" },
};


/** Hub "Centro de Contadores" — landing del módulo cuando se entra por el
 * nav de arriba, sin `?tool=`. Cada card navega a la herramienta real: el
 * modal genérico (`/contadores?tool=<key>`, ver contadores/page.tsx) salvo
 * que declare `route` propia (Proyección: tablero completo, no entra en un
 * modal). Todas las herramientas del catálogo son funcionales. */
export function ContadoresHub() {
  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">
          Centro de Contadores
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Automatización de reportes y gestión de bases de datos de contadores de impresión
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {TOOLS.map((tool) => {
          const Icon = tool.icon;
          const color = CARD_COLOR[tool.key];

          if (tool.disabled) {
            return (
              <div
                key={tool.key}
                title="No disponible"
                className="flex cursor-not-allowed flex-col gap-2.5 rounded-[12px] border border-border bg-card p-5 opacity-50"
              >
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-[9px] ${color.badge} ${color.fg}`}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <h2 className="font-heading text-[14.5px] font-bold text-foreground">
                  {tool.navLabel ?? tool.label}
                </h2>
                <span className="font-body text-[13px] text-muted-foreground">{tool.description}</span>
                <span className="mt-0.5 font-body text-[12.5px] font-bold text-muted-foreground">
                  No disponible
                </span>
              </div>
            );
          }

          return (
            <Link
              key={tool.key}
              href={tool.route ?? `/contadores?tool=${tool.key}`}
              className="flex flex-col gap-2.5 rounded-[12px] border border-border bg-card p-5 no-underline transition-colors hover:border-muted-foreground/30"
            >
              <span
                className={`flex h-9 w-9 items-center justify-center rounded-[9px] ${color.badge} ${color.fg}`}
              >
                <Icon className="h-4 w-4" />
              </span>
              <h2 className="font-heading text-[14.5px] font-bold text-foreground">
                {tool.navLabel ?? tool.label}
              </h2>
              <span className="font-body text-[13px] text-muted-foreground">{tool.description}</span>
              <span className={`mt-0.5 font-body text-[12.5px] font-bold ${color.fg}`}>
                INICIAR PROCESO →
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
