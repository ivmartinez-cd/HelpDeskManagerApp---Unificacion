import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type { EntradaBitacora } from "../types/bitacora";

export const bitacoraApi = {
  listByLiquidacion: (liquidacionId: string, page = 1, size = 500) =>
    httpClient.get<Page<EntradaBitacora>>(
      `/api/liquidaciones/${liquidacionId}/bitacora?page=${page}&size=${size}`,
    ),
};
