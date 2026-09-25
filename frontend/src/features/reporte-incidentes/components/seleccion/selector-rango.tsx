"use client";

import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { etiquetaPeriodo } from "../../lib/periodos";
import { OPCIONES_RANGO, PERSONALIZADO } from "./rango";
import { CONTROL } from "./estilos";

interface Props {
  meses: number;
  /** Período "Desde" del modo Personalizado; `null` = preset. */
  desde: string | null;
  /** Períodos elegibles como "Desde" (solo los <= mes final). */
  opcionesDesde: string[];
  onPreset: (meses: number) => void;
  onPersonalizado: () => void;
  onDesde: (desde: string) => void;
  size?: "sm" | "md";
}

/** Presets de rango + "Personalizado" con su select "Desde". Controlado: la
 * selección lo maneja con estado local, la barra con la URL. */
export function SelectorRango({
  meses,
  desde,
  opcionesDesde,
  onPreset,
  onPersonalizado,
  onDesde,
  size = "md",
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <SegmentedControl
        label="Rango hacia atrás desde el mes final"
        size={size}
        options={OPCIONES_RANGO}
        value={desde ? PERSONALIZADO : String(meses)}
        onChange={(v) => (v === PERSONALIZADO ? onPersonalizado() : onPreset(Number(v)))}
      />
      {desde && (
        <select
          aria-label="Desde"
          className={CONTROL}
          value={desde}
          onChange={(e) => onDesde(e.target.value)}
        >
          {opcionesDesde.map((p) => (
            <option key={p} value={p}>
              Desde {etiquetaPeriodo(p)}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
