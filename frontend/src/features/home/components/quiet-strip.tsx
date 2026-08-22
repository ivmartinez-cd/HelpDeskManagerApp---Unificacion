import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import type { QuietInfo } from "../config/card-quiet";

/** Tira "sin novedades" al pie de la vista: una línea por panel que no
 * tiene nada que hacer hoy (ver card-quiet.ts). Cada chip lleva a su
 * pantalla por si igual se quiere mirar. */
export function QuietStrip({ items }: { items: QuietInfo[] }) {
  if (items.length === 0) return null;
  return (
    <div
      data-testid="quiet-strip"
      className="flex flex-none flex-wrap items-center gap-x-2 gap-y-1.5 rounded-[12px] border border-border bg-card px-3.5 py-2 short:py-1.5"
    >
      <span className="font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        Sin novedades
      </span>
      {items.map((q) => (
        <Link
          key={q.id}
          href={q.href}
          className="inline-flex items-center gap-1.5 rounded-full bg-success/10 px-2.5 py-1 font-body text-[12px] no-underline transition-colors hover:bg-success/20"
        >
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" aria-hidden="true" />
          <span className="font-semibold text-foreground">{q.label}</span>
          <span className="text-muted-foreground">· {q.texto}</span>
        </Link>
      ))}
    </div>
  );
}
