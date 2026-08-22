"use client";

import { AlertTriangle } from "lucide-react";

export function LiquidacionAlertasBanner({
  incConAlertas,
  soloConAlertas,
  onSoloConAlertas,
}: {
  incConAlertas: number;
  soloConAlertas: boolean;
  onSoloConAlertas: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-[12px] border border-brand-orange/30 bg-brand-orange/10 px-5 py-4">
      <div className="flex items-start gap-3">
        <AlertTriangle size={16} className="mt-0.5 flex-shrink-0 text-brand-orange" />
        <p className="font-body text-sm text-foreground">
          <span className="font-semibold">
            Los {incConAlertas} incidentes tienen alertas de validación.
          </span>{" "}
          Revisá los importes cobrados contra los esperados antes de aprobar.
        </p>
      </div>
      {soloConAlertas ? (
        <button
          onClick={() => onSoloConAlertas(false)}
          className="flex-shrink-0 font-body text-sm text-brand-orange hover:underline"
        >
          Mostrar todos
        </button>
      ) : (
        <button
          onClick={() => onSoloConAlertas(true)}
          className="flex-shrink-0 font-body text-sm text-brand-orange hover:underline"
        >
          Ver sólo con alertas →
        </button>
      )}
    </div>
  );
}
