import { httpClient } from "@/services/http-client";
import type {
  CalendarEvent,
  CalendarFilterParams,
  EmpresaSiges,
  MiOperador,
  Operador,
  ResumenClientesOperador,
  SyncCalendarioResult,
  SyncStatus,
} from "../types/calendario";
import type {
  AnexoPendiente,
  AnexosPendientesListParams,
  AnexosPendientesResumen,
} from "../types/anexos-pendientes";
import type {
  EquipoSinReal,
  EquiposSinRealListParams,
  EquiposSinRealResumen,
} from "../types/equipos-sin-real";

/** Nombres tal como los serializa el backend real (`RunDb3ExportResponse` en
 * `db3_schemas.py`, camelCase vía `serialization_alias`) — este tipo tenía
 * campos que ese backend nunca devolvió (`csv_filename`, `total_rows`,
 * conteos por clase), rompía "Procesar DB3" pidiendo
 * `/outputs/undefined`. */
export interface Db3ExportResponse {
  csvFile: string;
  rowCount: number;
  warnings: string[];
}

/** Ídem `RunEstimationZeroResponse` en `tools_schemas.py`: el backend (y la
 * app vieja) nunca calculan un total de filas para esta herramienta. */
export interface EstimationZeroResponse {
  file: string;
}

/** Ídem `RunFixedSumResponse` en `tools_schemas.py`: un CSV por archivo de
 * entrada, sin conteo de filas (tampoco lo tenía la app vieja). */
export interface FixedSumResponse {
  files: string[];
}

/** Nombres tal como los serializa el backend real (`FtpClientOut` en
 * `ftp_client_schemas.py`) — este tipo tenía campos inventados
 * (`port`, `username`, `remote_dir`, `created_at`, `updated_at`) que ese
 * backend nunca devolvió, rompía el CRUD completo de clientes FTP: el
 * usuario y la ruta remota quedaban vacíos al editar, y el host se mostraba
 * como "host:undefined" en el listado. */
export interface FtpClient {
  id: string;
  name: string;
  host: string;
  user: string;
  path: string;
  pattern: string;
}

/** `FtpClientIn` en `ftp_client_schemas.py` exige `user`/`password` (ambos
 * requeridos) y usa `path`/`pattern` con default en el backend, no en el
 * cliente — se mandan siempre explícitos acá para no depender del default. */
export interface CreateFtpClientPayload {
  name: string;
  host: string;
  user: string;
  password: string;
  path: string;
  pattern: string;
}

/** A diferencia de crear, acá `password` es opcional: como `FtpClientOut`
 * (GET) nunca devuelve la contraseña guardada (por seguridad), no hay forma
 * de precargarla y reenviarla tal cual al editar. Omitir el campo le dice
 * al backend "conservá la actual". */
export interface UpdateFtpClientPayload {
  name: string;
  host: string;
  user: string;
  password?: string;
  path: string;
  pattern: string;
}

export interface ProcessFtpClientResponse {
  client_name: string;
  remote_filename: string;
  csv_filename: string;
  db3_filename: string;
  row_count: number;
  warnings: string[];
}

export interface SdsClient {
  id: string;
  name: string;
  suma_color: boolean;
}

export interface UpdateSdsConfigPayload {
  customer_name: string;
  suma_color: boolean;
}

export interface ProcessSdsResponse {
  csv_filename: string;
  customer_name: string;
}

export interface ErsClient {
  id: string;
  name: string;
  suma_color: boolean;
}

export interface UpdateErsConfigPayload {
  customer_name: string;
  suma_color: boolean;
}

export interface ProcessErsResponse {
  csv_filename: string;
  customer_name: string;
}

/** Envelope de paginación del backend (`Page[T]`, ver
 * shared/presentation/schemas/pagination.py) — estos catálogos se piden
 * completos en una sola página grande para alimentar un combobox con
 * búsqueda en vivo, así que acá se desenvuelve `.items` para que el resto
 * del frontend siga viendo un array plano como antes. */
interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const contadoresApi = {
  // DB3 a CSV
  runDb3Export: (formData: FormData) =>
    httpClient.postForm<Db3ExportResponse>("/api/contadores/db3", formData),

  // Estimación en 0
  runEstimationZero: (formData: FormData) =>
    httpClient.postForm<EstimationZeroResponse>("/api/contadores/en0", formData),

  // Suma Fija
  runFixedSum: (formData: FormData) =>
    httpClient.postForm<FixedSumResponse>("/api/contadores/suma-fija", formData),

  // Clientes FTP
  listFtpClients: () =>
    httpClient
      .get<Page<FtpClient>>("/api/contadores/ftp/clients")
      .then((page) => page.items),
  getFtpClient: (id: string) => httpClient.get<FtpClient>(`/api/contadores/ftp/clients/${id}`),
  createFtpClient: (payload: CreateFtpClientPayload) =>
    httpClient.post<FtpClient>("/api/contadores/ftp/clients", payload),
  updateFtpClient: (id: string, payload: UpdateFtpClientPayload) =>
    httpClient.put<FtpClient>(`/api/contadores/ftp/clients/${id}`, payload),
  deleteFtpClient: (id: string) =>
    httpClient.delete<{ message: string }>(`/api/contadores/ftp/clients/${id}`),
  processFtpClient: (id: string, fechaMaxima?: string) =>
    httpClient.post<ProcessFtpClientResponse>(
      `/api/contadores/ftp/clients/${id}/process`,
      fechaMaxima ? { fecha_maxima: fechaMaxima } : {},
    ),

  // HP SDS
  listSdsClients: () =>
    httpClient
      .get<Page<SdsClient>>("/api/contadores/sds/clients")
      .then((page) => page.items),
  updateSdsConfig: (id: string, payload: UpdateSdsConfigPayload) =>
    httpClient.put<SdsClient>(`/api/contadores/sds/clients/${id}/config`, payload),
  processSds: (payload: { customer_id: string; customer_name: string; fecha_maxima: string }) =>
    httpClient.post<ProcessSdsResponse>("/api/contadores/sds/process", payload),

  // Epson ERS
  listErsClients: () =>
    httpClient
      .get<Page<ErsClient>>("/api/contadores/ers/clients")
      .then((page) => page.items),
  updateErsConfig: (id: string, payload: UpdateErsConfigPayload) =>
    httpClient.put<ErsClient>(`/api/contadores/ers/clients/${id}/config`, payload),
  processErs: (payload: { customer_id: string; customer_name: string; fecha_maxima: string }) =>
    httpClient.post<ProcessErsResponse>("/api/contadores/ers/process", payload),

  // Download Output File
  getOutputUrl: (filename: string) => `/api/contadores/outputs/${encodeURIComponent(filename)}`,

  // Calendario de Planificación — siempre lee de la copia local (ver
  // /calendario/sync); el operador se resuelve solo del lado del backend
  // según quién inició sesión.
  getCalendarioEvents: (params: CalendarFilterParams) => {
    const searchParams = new URLSearchParams({
      start: params.start,
      end: params.end,
      size: "500",
    });
    if (params.operador_id) {
      searchParams.set("operador_id", params.operador_id);
    }
    return httpClient.get<Page<CalendarEvent>>(
      `/api/contadores/calendario?${searchParams.toString()}`,
    );
  },
  // Backlog de pendientes de días anteriores para la card de Inicio — misma
  // visibilidad que /calendario; el corte (30 días) lo decide el backend.
  getCalendarioPendientes: (today: string) => {
    const searchParams = new URLSearchParams({ today, size: "500" });
    return httpClient.get<Page<CalendarEvent>>(
      `/api/contadores/calendario/pendientes?${searchParams.toString()}`,
    );
  },
  getMiOperador: () => httpClient.get<MiOperador>("/api/contadores/calendario/mi-operador"),
  // Catálogo de operadores para el filtro de superadmin (ver
  // GetCalendarEventsUseCase — un usuario regular no puede elegir operador).
  listCalendarioOperadores: () =>
    httpClient
      .get<Page<Operador>>("/api/contadores/calendario/operadores")
      .then((page) => page.items),
  getSyncStatus: () => httpClient.get<SyncStatus>("/api/contadores/calendario/sync/status"),
  // Card de Inicio: clientes del mes e impresoras (cruce contra Siges) por
  // operador. El backend excluye los operadores pool.
  getResumenClientesOperador: () =>
    httpClient.get<ResumenClientesOperador>("/api/contadores/calendario/resumen-clientes"),
  // Resolución de clientes sin cruce: búsqueda en vivo de empresas en Siges
  // y guardado del mapeo manual (requiere contadores:manage).
  searchEmpresasSiges: (q: string) =>
    httpClient
      .get<Page<EmpresaSiges>>(
        `/api/contadores/calendario/empresas-siges?q=${encodeURIComponent(q)}`,
      )
      .then((page) => page.items),
  setClienteSigesMap: (clienteGestion: string, sigesEmpresaIds: number[]) =>
    httpClient.put<void>("/api/contadores/calendario/cliente-siges-map", {
      cliente_gestion: clienteGestion,
      siges_empresa_ids: sigesEmpresaIds,
    }),
  syncCalendario: () => httpClient.post<SyncCalendarioResult>("/api/contadores/calendario/sync"),

  // Equipos sin contador real — consulta en vivo a Siges cacheada en el
  // backend (TTL 10 min); filtro/orden/paginación son server-side sobre ese
  // snapshot, así que acá se devuelve el envelope completo (hace falta
  // `total` para paginar).
  listEquiposSinReal: (params: EquiposSinRealListParams) => {
    const searchParams = new URLSearchParams({
      page: String(params.page),
      size: String(params.size),
      sort_by: params.sortBy,
      sort_dir: params.sortDir,
      min_meses: String(params.minMeses),
    });
    if (params.search) searchParams.set("search", params.search);
    if (params.refresh) searchParams.set("refresh", "true");
    return httpClient.get<Page<EquipoSinReal>>(
      `/api/contadores/equipos-sin-real?${searchParams.toString()}`,
    );
  },
  getEquiposSinRealResumen: () =>
    httpClient.get<EquiposSinRealResumen>("/api/contadores/equipos-sin-real/resumen"),

  // Anexos sin facturar (reporte de cierre de contadores) — consulta en vivo
  // a Siges cacheada en el backend (TTL 5 min). El universo real es chico
  // (~50 filas) y el reporte se imprime entero: se pide en una sola página
  // grande y se desenvuelve `.items`.
  listAnexosPendientes: (params: AnexosPendientesListParams = {}) => {
    const searchParams = new URLSearchParams({ size: "500" });
    if (params.estado) searchParams.set("estado", params.estado);
    if (params.search) searchParams.set("search", params.search);
    if (params.refresh) searchParams.set("refresh", "true");
    return httpClient
      .get<Page<AnexoPendiente>>(
        `/api/contadores/anexos-pendientes?${searchParams.toString()}`,
      )
      .then((page) => page.items);
  },
  getAnexosPendientesResumen: () =>
    httpClient.get<AnexosPendientesResumen>("/api/contadores/anexos-pendientes/resumen"),
};


