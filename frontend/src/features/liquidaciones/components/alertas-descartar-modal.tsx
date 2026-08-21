"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Alerta } from "../types/liquidaciones";

export function DescartarModal({ liquidacionId, alertas, onClose, onChanged }: {
  liquidacionId: string;
  alertas: Alerta[];
  onClose: () => void;
  onChanged: () => void;
}) {
  const [justificacion, setJustificacion] = useState("");
  const [enviando, setEnviando] = useState(false);
  const esMasivo = alertas.length > 1;

  const descartar = async () => {
    setEnviando(true);
    try {
      const justificacionTrim = justificacion.trim();
      const resultados = await Promise.allSettled(
        alertas.map((a) =>
          liquidacionesApi.updateEstadoAlerta(liquidacionId, a.id, {
            estado: "descartada",
            justificacion: justificacionTrim,
          }),
        ),
      );
      const fallidas = resultados.filter((r) => r.status === "rejected").length;
      if (fallidas > 0) {
        toast.error(
          `No se pudieron descartar ${fallidas} de ${alertas.length} alerta${alertas.length === 1 ? "" : "s"}`,
        );
      }
      onChanged();
      onClose();
    } finally {
      setEnviando(false);
    }
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={esMasivo ? `Descartar ${alertas.length} alertas` : `Descartar ${alertas[0].tipoAlerta}`}
      widthPx={460}
    >
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          {esMasivo
            ? "Las alertas seleccionadas quedan descartadas y NO van a volver a aparecer aunque se re-analice la liquidación."
            : "La alerta queda descartada y NO va a volver a aparecer aunque se re-analice la liquidación."}{" "}
          Dejá escrito el motivo — queda guardado con la{esMasivo ? "s" : ""} alerta{esMasivo ? "s" : ""}.
        </p>
        <textarea
          value={justificacion}
          onChange={(e) => setJustificacion(e.target.value)}
          rows={3}
          placeholder="Ej.: diferencia acordada con el prestador"
          className="w-full rounded-[8px] border border-border bg-background p-3 font-body text-sm text-foreground outline-none focus:border-brand-orange"
        />
        <div className="flex justify-end gap-2">
          <BrandButton variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton
            loading={enviando}
            disabled={!justificacion.trim()}
            onClick={() => void descartar()}
          >
            {esMasivo ? `Descartar ${alertas.length} alertas` : "Descartar alerta"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
