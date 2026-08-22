import { contadoresApi } from "../api/contadores-api";

/** Configuración por tipo de cliente del modal "elegir cliente + fecha +
 * procesar" (`client-picker-process-modal.tsx`). */

export type PickerClientType = "sds" | "ers" | "ftp";

export interface ClientOption {
  id: string;
  name: string;
}

interface TypeConfig {
  title: string;
  clientLabel: string;
  processLabel: string;
  loadErrorMessage: string;
  listClients: () => Promise<ClientOption[]>;
  process: (
    clientId: string,
    clientName: string,
    fechaMaxima: string,
  ) => Promise<{ csv_filename: string; db3_filename?: string }>;
}

export const CONFIG: Record<PickerClientType, TypeConfig> = {
  sds: {
    title: "Descargar SDS",
    clientLabel: "Seleccionar cliente SDS",
    processLabel: "Descargar Contadores",
    loadErrorMessage: "Error al cargar clientes HP SDS",
    listClients: contadoresApi.listSdsClients,
    process: (id, name, fecha) =>
      contadoresApi.processSds({ customer_id: id, customer_name: name, fecha_maxima: fecha }),
  },
  ers: {
    title: "Descargar ERS",
    clientLabel: "Seleccionar grupo Epson ERS",
    processLabel: "Descargar Telemetría",
    loadErrorMessage: "Error al cargar grupos Epson ERS",
    listClients: contadoresApi.listErsClients,
    process: (id, name, fecha) =>
      contadoresApi.processErs({ customer_id: id, customer_name: name, fecha_maxima: fecha }),
  },
  ftp: {
    title: "Descarga FTP",
    clientLabel: "Seleccionar cliente FTP",
    processLabel: "Procesar DB3",
    loadErrorMessage: "Error al cargar clientes FTP",
    listClients: contadoresApi.listFtpClients,
    process: (id, _name, fecha) => contadoresApi.processFtpClient(id, fecha),
  },
};
