"use client";

import type { EntradaBitacora } from "../types/bitacora";

function formatFecha(valor: string): string {
  return new Date(valor).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" });
}

/** Hilo de comentarios de Web Agentes (prestador y Canal Directo), solo
 * lectura: se sigue respondiendo desde Web Agentes. */
export function BitacoraSeccion({
  items,
  error,
}: {
  items: EntradaBitacora[] | null;
  error: boolean;
}) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <p className="font-body text-sm font-semibold text-foreground">
          Bitácora de Web Agentes
          {items && items.length > 0 && (
            <span className="ml-2 font-normal text-muted-foreground">({items.length})</span>
          )}
        </p>
      </div>
      <div className="flex flex-col gap-3 px-4 py-3">
        {error && (
          <p className="font-body text-sm text-muted-foreground">No se pudo cargar la bitácora.</p>
        )}
        {!error && items === null && (
          <p className="font-body text-sm text-muted-foreground">Cargando bitácora…</p>
        )}
        {items?.length === 0 && (
          <p className="font-body text-sm text-muted-foreground">Sin comentarios.</p>
        )}
        {items?.map((e) => (
          <div
            key={e.id}
            className={`max-w-[85%] rounded-[10px] border px-3 py-2 ${
              e.esCanal
                ? "self-end border-brand-orange/30 bg-brand-orange/[0.06]"
                : "self-start border-border bg-muted/40"
            }`}
          >
            <p className="font-body text-xs text-muted-foreground">
              <span className="font-semibold text-foreground">{e.autor ?? e.usuario}</span>
              {e.autor && <span> · {e.usuario}</span>}
              <span> · {e.esCanal ? "Canal Directo" : "Prestador"}</span>
              <span> · {formatFecha(e.fecha)}</span>
            </p>
            <p className="mt-1 whitespace-pre-wrap font-body text-sm text-foreground">{e.texto}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
