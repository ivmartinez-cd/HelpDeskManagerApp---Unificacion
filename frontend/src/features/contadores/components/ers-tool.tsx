"use client";

import { Radio } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import { MeterClientsTool } from "./meter-clients-tool";

export function ErsTool() {
  return (
    <MeterClientsTool
      processType="ers"
      listClients={contadoresApi.listErsClients}
      updateConfig={contadoresApi.updateErsConfig}
      loadErrorMessage="Error al cargar grupos Epson ERS"
      searchAriaLabel="Buscar grupos Epson ERS"
      searchPlaceholder="Buscar por grupo Epson ERS..."
      emptyIcon={Radio}
      emptyTitle="No se encontraron grupos Epson ERS"
      clientColumnLabel="Grupo de Equipos Epson ERS"
      idColumnLabel="ID de Grupo"
      downloadButtonLabel="Descargar Telemetría"
    />
  );
}
