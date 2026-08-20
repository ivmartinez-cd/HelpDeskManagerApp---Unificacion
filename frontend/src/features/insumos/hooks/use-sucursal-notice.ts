"use client";

import { useCallback, useState } from "react";
import type {
  BulkSucursalState,
  SucursalNoticeState,
} from "../components/dashboard/dashboard-sucursal-modals";
import type { RequestRow } from "../types";

/** Estado de los dos modales del aviso de cambio de sucursal — separado de
 * use-order-actions.ts (ya señalado como deuda de tamaño en ADR-020) porque es un
 * contenedor de estado puro, sin lógica de carga: ese hook lo consume para disparar
 * el aviso post-carga y la exclusión previa a "Cargar seleccionados". */

const EMPTY_NOTICE: SucursalNoticeState = {
  visible: false,
  orderId: null,
  supplyUrl: null,
  sucursal: null,
  observacion: "",
};

interface BulkSucursalInternalState extends BulkSucursalState {
  includedRows: RequestRow[];
  customerId: number | null;
  customerName: string | null;
}

const EMPTY_BULK: BulkSucursalInternalState = {
  visible: false,
  excluded: [],
  includedCount: 0,
  includedRows: [],
  customerId: null,
  customerName: null,
};

export function useSucursalNotice() {
  const [notice, setNotice] = useState<SucursalNoticeState>(EMPTY_NOTICE);
  const [bulk, setBulk] = useState<BulkSucursalInternalState>(EMPTY_BULK);

  const closeNotice = useCallback(() => setNotice(EMPTY_NOTICE), []);
  const clearBulk = useCallback(() => setBulk(EMPTY_BULK), []);

  return { notice, setNotice, closeNotice, bulk, setBulk, clearBulk };
}
