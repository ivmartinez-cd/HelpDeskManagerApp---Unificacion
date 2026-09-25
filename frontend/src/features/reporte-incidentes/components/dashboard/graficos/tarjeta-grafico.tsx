import type { ReactNode } from "react";
import { cn } from "@/shared/utils/cn";

interface Props {
  titulo: string;
  subtitulo?: string;
  /** Dato a la derecha del título (total, "Top 10", etc.). */
  derecha?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Card con encabezado de los gráficos y paneles del reporte. */
export function TarjetaGrafico({ titulo, subtitulo, derecha, children, className }: Props) {
  return (
    <section data-print-card className={cn("flex flex-col rounded-[12px] border border-border bg-card", className)}>
      <header className="flex flex-wrap items-start justify-between gap-3 px-6 pt-5">
        <div>
          <h3 className="font-heading text-base font-bold text-foreground">{titulo}</h3>
          {subtitulo && <p className="font-body text-[13px] text-muted-foreground">{subtitulo}</p>}
        </div>
        {derecha && <div className="font-body text-[13px] text-muted-foreground">{derecha}</div>}
      </header>
      {children}
    </section>
  );
}

export function SinDatos() {
  return (
    <div className="flex h-40 items-center justify-center font-body text-sm text-muted-foreground">
      Sin datos para el período
    </div>
  );
}
