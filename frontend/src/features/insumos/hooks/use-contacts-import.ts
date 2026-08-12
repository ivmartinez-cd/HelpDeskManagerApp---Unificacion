"use client";

import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { ZoneContactApplyRow, ZoneContactPreviewRow } from "../types";

function errorMsg(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

/** Una fila es seleccionable si el backend pudo resolver un contacto real
 * para ella. El apply del servidor saltea en silencio (sin marcarla como
 * error) las filas con `error`, sin `apellido`, o `already_configured &&
 * !overwrite` — la UI no debe ofrecer seleccionar lo que el apply va a
 * ignorar, o el contador `applied` que devuelve confunde al operador. */
export function selectableImportRow(row: ZoneContactPreviewRow): boolean {
  return !row.error && row.apellido.trim() !== "";
}

interface ContactsImportResult {
  applied: number;
  requested: number;
}

/** Estado de la importación masiva de contactos desde el PortalWeb de SDS:
 * preview explícito (nunca automático — ver `contacts-import-modal.tsx`),
 * selección múltiple por `zone` y apply con SIEMPRE refetch vía `onApplied`
 * — el apply re-resuelve del lado del servidor y puede aplicar datos
 * distintos a los que la UI mostró en el preview, así que acá nunca hay
 * update optimista. */
export function useContactsImport(customerId: number | null, onApplied: () => void) {
  const [rows, setRows] = useState<ZoneContactPreviewRow[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContactsImportResult | null>(null);

  // Cliente nuevo (o el padre manda `null` al cerrar el modal) arranca en
  // estado limpio: no tiene sentido arrastrar el preview o la selección de
  // otro cliente. Ajuste de estado durante el render (mismo patrón que
  // `confirmation-modal.tsx`) en vez de un efecto, para no disparar un
  // render en cascada por un `setState` síncrono dentro de un `useEffect`.
  const [prevCustomerId, setPrevCustomerId] = useState(customerId);
  if (customerId !== prevCustomerId) {
    setPrevCustomerId(customerId);
    setRows([]);
    setSelected(new Set());
    setError(null);
    setResult(null);
  }

  const selectableRows = useMemo(() => rows.filter(selectableImportRow), [rows]);

  const preview = useCallback(async () => {
    if (!customerId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSelected(new Set());
    try {
      const res = await insumosApi.previewZoneContactsImport(customerId);
      if (!res.ok) {
        setError(res.error ?? "No se pudo obtener la vista previa.");
        setRows([]);
        return;
      }
      setRows(res.rows);
    } catch (err: unknown) {
      setError(errorMsg(err, "No se pudo obtener la vista previa."));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  function toggle(zone: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(zone)) next.delete(zone);
      else next.add(zone);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => {
      const allSelected =
        selectableRows.length > 0 && selectableRows.every((r) => prev.has(r.zone));
      return allSelected ? new Set() : new Set(selectableRows.map((r) => r.zone));
    });
  }

  const apply = useCallback(async () => {
    if (!customerId || selected.size === 0) return;
    const requested = selected.size;
    // Seleccionar una fila ya configurada implica pisarla — no hay checkbox
    // de "sobreescribir" separado (permitiría armar una selección que no
    // hace nada, la peor UX posible acá).
    const body: ZoneContactApplyRow[] = rows
      .filter((r) => selected.has(r.zone))
      .map((r) => ({ zone: r.zone, overwrite: r.already_configured }));
    setApplying(true);
    setError(null);
    try {
      const res = await insumosApi.applyZoneContactsImport(customerId, body);
      if (!res.ok) {
        setError(res.error ?? "No se pudo aplicar la importación.");
        return;
      }
      setResult({ applied: res.applied, requested });
      if (res.applied < requested) {
        toast.warning(
          `Se aplicaron ${res.applied} de ${requested} zonas. Los datos cambiaron desde la ` +
            "vista previa — volvé a previsualizar.",
        );
      } else {
        toast.success(`Se importaron ${res.applied} zona(s).`);
      }
      setSelected(new Set());
      onApplied();
    } catch (err: unknown) {
      setError(errorMsg(err, "No se pudo aplicar la importación."));
    } finally {
      setApplying(false);
    }
  }, [customerId, selected, rows, onApplied]);

  return { rows, selected, loading, applying, error, result, preview, toggle, toggleAll, apply };
}
