import type { RequestRow as RequestRowType } from "../../types";

/** Badges chicos de `request-row.tsx`, separados porque ese archivo ya está
 * en el tamaño máximo (§4): color del canal, pedido activo sin confirmar
 * entrega, y cartucho/drum reinstalado (consumable_serial repetido). */

const COLOUR_LABELS: Record<string, string> = {
  CYAN: "C",
  MAGENTA: "M",
  YELLOW: "Y",
  BLACK: "K",
  QUADCOLOUR: "CMYK",
};

const COLOUR_CLASSES: Record<string, string> = {
  CYAN: "bg-[rgba(34,211,238,.15)] text-[#0891b2] dark:text-[#67e8f9]",
  MAGENTA: "bg-[rgba(236,72,153,.15)] text-[#db2777] dark:text-[#f9a8d4]",
  YELLOW: "bg-[rgba(234,179,8,.15)] text-[#a16207] dark:text-[#facc15]",
  BLACK: "bg-[rgba(88,89,91,.15)] text-[#3a3a3c] dark:text-[#b5b5b5]",
};

export function ColourBadge({ colour }: { colour: string }) {
  const label = COLOUR_LABELS[colour] ?? colour;
  const className =
    COLOUR_CLASSES[colour] ?? "bg-[rgba(88,89,91,.15)] text-[#58595B] dark:text-[#b5b5b5]";
  return (
    <span
      title={`Color del canal: ${colour}`}
      className={`ml-1 inline-flex items-center rounded-[4px] px-1 py-0.5 text-[9px] font-bold ${className}`}
    >
      {label}
    </span>
  );
}

/** Aviso de "pedido activo sin confirmar entrega" — badge en la columna de
 * acción cuando `hasActiveSupply(row)`, en las dos ramas (normal y
 * validationPending). No implica que la solicitud esté "cargada": ver
 * request-status.ts::isLoaded. */
export function UnconfirmedSupplyBadge({
  row,
  validating,
}: {
  row: RequestRowType;
  validating: boolean;
}) {
  const fecha = row.supplyFecha ? `, creado ${row.supplyFecha}` : "";
  const title = validating
    ? `Pedido ${row.supplyId} (${row.supplyStatus}${fecha}) sin confirmar entrega en Canal Directo — probablemente esta oscilación sea el mismo glitch de sensor, no un consumo real.`
    : `Pedido ${row.supplyId} (${row.supplyStatus}${fecha}) sin confirmar entrega en Canal Directo — revisá si hace falta reclamar la entrega antes de cargar uno nuevo.`;
  return (
    <span
      title={title}
      className="inline-flex items-center gap-1 self-start rounded-full bg-[rgba(234,179,8,.15)] px-1.5 py-0.5 text-[10px] font-semibold text-[#a16207] dark:text-[#facc15]"
    >
      ⚠ {row.supplyId} · {row.supplyStatus}
    </span>
  );
}

export function ReusedConsumableBadge({ note }: { note: string }) {
  return (
    <span
      title={note}
      className="ml-1 inline-flex items-center rounded-[6px] bg-[rgba(234,179,8,.15)] px-1.5 py-0.5 text-[10px] font-semibold text-[#a16207] dark:text-[#facc15]"
    >
      ⚠ cartucho repetido
    </span>
  );
}
