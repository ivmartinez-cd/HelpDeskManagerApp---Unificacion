import { ESTADO_COLOR } from "./preventivos-mapa-colores";
import { ESTADO_META } from "./preventivos-tabla";

export function PreventivosMapaLeyenda() {
  return (
    <div className="flex flex-wrap items-center gap-4 font-body text-xs text-muted-foreground">
      {(Object.keys(ESTADO_META) as (keyof typeof ESTADO_META)[]).map((clave) => (
        <span key={clave} className="flex items-center gap-1.5">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ background: ESTADO_COLOR[clave] }}
            aria-hidden
          />
          {ESTADO_META[clave].label}
        </span>
      ))}
    </div>
  );
}
