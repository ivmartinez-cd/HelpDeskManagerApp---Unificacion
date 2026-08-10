"use client";

import { Printer } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import { MeterClientsTool } from "./meter-clients-tool";

export function SdsTool() {
  return (
    <MeterClientsTool
      processType="sds"
      listClients={contadoresApi.listSdsClients}
      updateConfig={contadoresApi.updateSdsConfig}
      loadErrorMessage="Error al cargar clientes HP SDS"
      searchAriaLabel="Buscar clientes HP SDS"
      searchPlaceholder="Buscar por cliente SDS..."
      emptyIcon={Printer}
      emptyTitle="No se encontraron clientes HP SDS"
      clientColumnLabel="Cliente HP SDS"
      idColumnLabel="ID Remoto"
      downloadButtonLabel="Descargar Contadores"
    />
  );
}
