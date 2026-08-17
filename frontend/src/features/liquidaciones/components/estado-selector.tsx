"use client";

import { useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import type { EstadoLiquidacion } from "../types/liquidaciones";

export const ESTADOS: EstadoLiquidacion[] = [
  "abierta",
  "preliquidada",
  "recibida",
  "observada",
  "aprobada",
  "cerrada",
];

export const ESTADO_LABELS: Record<EstadoLiquidacion, string> = {
  abierta: "Abierta",
  preliquidada: "Preliquidada",
  recibida: "Recibida",
  observada: "Observada",
  aprobada: "Aprobada",
  cerrada: "Cerrada",
};

/** Retroceder en el ciclo (o salir de aprobada/cerrada) es una corrección
 * excepcional, no el flujo normal — se confirma antes de aplicar. */
function esSaltoRiesgoso(actual: EstadoLiquidacion, nuevo: EstadoLiquidacion): boolean {
  if (actual === "cerrada" || actual === "aprobada") return true;
  return ESTADOS.indexOf(nuevo) < ESTADOS.indexOf(actual);
}

export function EstadoSelector({ estado, disabled, onCambiar }: {
  estado: EstadoLiquidacion;
  disabled: boolean;
  onCambiar: (nuevo: EstadoLiquidacion) => void;
}) {
  const [confirmar, setConfirmar] = useState<EstadoLiquidacion | null>(null);

  const elegir = (nuevo: EstadoLiquidacion) => {
    if (nuevo === estado) return;
    if (esSaltoRiesgoso(estado, nuevo)) setConfirmar(nuevo);
    else onCambiar(nuevo);
  };

  return (
    <>
      <select
        value={estado}
        disabled={disabled}
        onChange={(e) => elegir(e.target.value as EstadoLiquidacion)}
        className="rounded-[8px] border border-border bg-card px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50 disabled:opacity-50"
      >
        {ESTADOS.map((e) => (
          <option key={e} value={e}>{ESTADO_LABELS[e]}</option>
        ))}
      </select>
      <BrandModal
        isOpen={confirmar !== null}
        onClose={() => setConfirmar(null)}
        title="¿Retroceder el estado de la liquidación?"
        widthPx={460}
      >
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">
            Vas a pasar la liquidación de{" "}
            <span className="font-bold">{ESTADO_LABELS[estado]}</span> a{" "}
            <span className="font-bold">{confirmar ? ESTADO_LABELS[confirmar] : ""}</span>.
          </p>
          <p className="font-body text-sm text-muted-foreground">
            Esto solo cambia el estado en esta app — no toca web agentes. Si además hay
            que corregirlo en AyC, usá los botones de la barra AyC.
          </p>
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setConfirmar(null)}>
              Cancelar
            </BrandButton>
            <BrandButton
              onClick={() => {
                if (confirmar) onCambiar(confirmar);
                setConfirmar(null);
              }}
            >
              Sí, cambiar estado
            </BrandButton>
          </div>
        </div>
      </BrandModal>
    </>
  );
}
