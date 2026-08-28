import { BarRow } from "@/features/home/components/dashboard-card-bits";
import { FALLBACK_COLOR, fmtInt, fmtPct } from "@/features/home/utils/inicio-format";
import type { OperadorSinReal } from "../types/equipos-sin-real";

/** Nombre literal del bucket armado en el backend
 * (`_SIN_OPERADOR` en `get_equipos_sin_real_resumen.py`) para los equipos
 * cuyo cliente no cruza con ningún operador. Va en gris neutro, no en el
 * naranja de marca reservado a operadores reales. */
const SIN_OPERADOR = "Sin operador asignado";
const SIN_OPERADOR_COLOR = "var(--muted-foreground)";

/** Desglose por operador ("laburo mes a mes de recuperación de reales"):
 * cuánto del parque sin real le corresponde a cada uno. Reusa `BarRow`
 * (barras ordenadas, no dona — decisión del handoff de Inicio) en vez de
 * inventar un patrón visual nuevo; no hay handoff propio de `contadores`.
 *
 * `BarRow` reserva 44% del ancho de fila para el label — pensado para las
 * cards angostas de Inicio (~340-420px). Esta pantalla no vive en una
 * grilla de cards, así que el bloque se envuelve en la misma card
 * (`rounded-[12px] border border-border bg-card`, header con `border-b`)
 * que usa `StatsTable` para Estadísticas, con un ancho máximo — si no, en
 * una página ancha el label queda pegado a la izquierda y la barra
 * arranca lejísimos, con un hueco vacío enorme en el medio.
 *
 * El backend ya filtra `operadores` con los mismos min_meses/solo_activos
 * que la tabla de abajo (decisión 2026-08-28: antes era fijo sobre el
 * universo completo y confundía — el número no se movía al cambiar filtros).
 * Por eso el % de cada barra se calcula sobre la suma de `operadores`, no
 * sobre el total sin filtrar de las tarjetas de arriba. */
export function EquiposSinRealResumenOperador({
  operadores,
}: {
  operadores: OperadorSinReal[];
}) {
  const total = operadores.reduce((suma, o) => suma + o.equipos, 0);
  const max = Math.max(1, ...operadores.map((o) => o.equipos));
  return (
    <section className="flex max-w-xl flex-col rounded-[12px] border border-border bg-card">
      <header className="border-b border-border px-6 py-4">
        <h2 className="font-heading text-base font-bold text-foreground">
          Detalle por operador
        </h2>
        <p className="mt-0.5 font-body text-[13px] text-muted-foreground">
          Con los mismos filtros de meses y estado que la tabla de abajo.
        </p>
      </header>
      <div className="flex flex-col gap-3 px-6 py-4">
        {operadores.map((op) => (
          <BarRow
            key={op.nombre}
            color={op.nombre === SIN_OPERADOR ? SIN_OPERADOR_COLOR : (op.color ?? FALLBACK_COLOR)}
            label={op.nombre}
            detail={
              op.parque_total
                ? `${fmtPct(Math.round((op.equipos / op.parque_total) * 1000) / 10)}% de su parque`
                : undefined
            }
            value={fmtInt(op.equipos)}
            pct={total > 0 ? `${fmtPct(Math.round((op.equipos / total) * 1000) / 10)}%` : undefined}
            widthPct={(op.equipos / max) * 100}
          />
        ))}
      </div>
    </section>
  );
}
