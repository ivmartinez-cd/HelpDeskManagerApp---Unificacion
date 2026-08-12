"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandInput } from "@/shared/components/ui/brand-form";
import { insumosApi } from "../../api/insumos-api";
import type { ZoneContactRow } from "../../types";
import { ConfirmationModal } from "../shared";

function errorMsg(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

interface ImportFromSupplyModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId: number | null;
  onImported: (row: ZoneContactRow) => void;
}

/** Modal para resolver el contacto de una zona a partir de un N° de pedido
 * de supply (SOAP HP SDS). A diferencia de la importación masiva de SDS, acá
 * NO hay preview: el endpoint hace upsert directo sobre la zona resuelta, por
 * eso el copy es explícito sobre lo que se pierde. */
export function ImportFromSupplyModal({
  isOpen,
  onClose,
  customerId,
  onImported,
}: ImportFromSupplyModalProps) {
  const [supplyId, setSupplyId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleClose() {
    setSupplyId("");
    setError(null);
    onClose();
  }

  async function handleConfirm() {
    if (!customerId) return;
    if (supplyId.trim() === "") {
      setError("Ingresá el N° de pedido de supply.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await insumosApi.importContactsFromSupply(customerId, supplyId.trim());
      if (!res.ok || !res.row) {
        setError(res.error ?? "No se pudo importar el contacto.");
        return;
      }
      toast.success(`Zona "${res.zone}" importada.`);
      onImported(res.row);
      setSupplyId("");
      onClose();
    } catch (err: unknown) {
      setError(errorMsg(err, "No se pudo importar el contacto."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={handleClose}
      onConfirm={() => void handleConfirm()}
      title="Importar contacto desde pedido"
      variant="warning"
      confirmLabel="Importar y pisar zona"
      loading={busy}
      error={error}
      extra={
        <BrandInput
          label="N° de pedido de supply"
          value={supplyId}
          onChange={(e) => setSupplyId(e.target.value)}
          placeholder="Ej: 12345 o 12345-A"
          disabled={busy}
        />
      }
    >
      Esta acción sobrescribe directamente la zona que corresponda a la sucursal del pedido, sin
      vista previa. El nombre completo del contacto queda todo en el campo <strong>Apellido</strong>
      {" "}— el campo Nombre queda vacío. Además, se pierden las observaciones que hubiera
      cargadas en esa zona.
    </ConfirmationModal>
  );
}
