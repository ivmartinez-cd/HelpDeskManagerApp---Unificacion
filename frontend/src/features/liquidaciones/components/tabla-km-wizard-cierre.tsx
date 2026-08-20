"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";
import type { ResumenBandeja } from "../lib/asistente-km-bandeja";
import { plural } from "../lib/asistente-km-textos";
import type { AplicarDistanciasResult } from "../types/liquidaciones";
import { BotonExportarCsv } from "./tabla-km-wizard-bandeja";
import { Resultado } from "./tabla-km-wizard-ui";

/** Estado de cierre explícito: qué quedó al día y qué sigue pendiente. */
export function PantallaCierre({ prestadorId, aplicado, resumen, irARevisar, onClose }: {
  prestadorId: string;
  aplicado: AplicarDistanciasResult;
  resumen: ResumenBandeja;
  irARevisar: () => void;
  onClose: () => void;
}) {
  const pendientes: string[] = [];
  if (resumen.nombres > 0) pendientes.push(plural(resumen.nombres, "nombre", "nombres"));
  if (resumen.ubicaciones + resumen.sinUbicacion > 0) pendientes.push(plural(resumen.ubicaciones + resumen.sinUbicacion, "ubicación", "ubicaciones"));
  if (resumen.pinesPorVerificar > 0) pendientes.push(`${resumen.pinesPorVerificar} pines a verificar`);

  return (
    <div className="flex flex-col gap-4">
      <Resultado>Listo: tu Tabla KM quedó al día.</Resultado>
      <p className="font-body text-sm text-foreground">
        {plural(aplicado.creadas, "fila nueva", "filas nuevas")} y {plural(aplicado.actualizadas, "actualizada", "actualizadas")}.
        El umbral de viático y las observaciones no se tocaron.
      </p>
      <div className="flex flex-wrap items-center gap-3 rounded-[8px] border border-border p-3">
        <p className="font-body text-sm text-foreground">
          Quedan para corregir en Gestión: <strong>{plural(resumen.paraGestion, "sucursal", "sucursales")}</strong>
        </p>
        <BotonExportarCsv prestadorId={prestadorId} />
      </div>
      {pendientes.length > 0 && (
        <p className="font-body text-sm text-muted-foreground">
          Pendientes que dejaste sin resolver: {pendientes.join(", ")}.{" "}
          <button type="button" onClick={irARevisar} className="text-brand-orange underline-offset-2 hover:underline">
            Volver a Revisar pendientes
          </button>{" "}
          cuando quieras — el asistente recuerda todo.
        </p>
      )}
      <BrandButton onClick={onClose} className="self-end">Cerrar</BrandButton>
    </div>
  );
}
