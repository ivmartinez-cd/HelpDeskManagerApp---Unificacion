"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, SucursalPropia } from "../types/liquidaciones";

export function SpstBaseSucursalModal({
  spst,
  prestador,
  onClose,
  onChanged,
}: {
  spst: Spst;
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [sucursales, setSucursales] = useState<SucursalPropia[] | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(spst.sigesBaseSucursalId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .listSucursalesPropiasPrestatdor(prestador.id)
      .then(setSucursales)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar sucursales"))
      .finally(() => setLoadingList(false));
  }, [prestador.id]);

  const handleGuardar = async () => {
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.vincularBaseSucursalSpst(spst.id, selectedId);
      toast.success(selectedId ? "Base guardada" : "Base desvinculada");
      onChanged();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const baseCambiada = selectedId !== spst.sigesBaseSucursalId;
  const baseTieneCoords = sucursales?.find((s) => s.sigesSucursalId === selectedId)?.tieneCoords ?? false;

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Base despacho — ${spst.nombre}`}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          Seleccioná la sucursal de Siges desde donde este SPST despacha.
          Se usa como punto de origen para el cálculo de distancias de las filas asignadas a este SPST.
        </p>

        {loadingList ? (
          <div className="flex h-24 items-center justify-center"><Spinner /></div>
        ) : sucursales && sucursales.length > 0 ? (
          <div className="max-h-64 overflow-y-auto rounded-[8px] border border-border">
            {sucursales.map((s) => (
              <label
                key={s.sigesSucursalId}
                className={`flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30 ${
                  selectedId === s.sigesSucursalId ? "bg-brand-orange/5" : ""
                }`}
              >
                <input
                  type="radio"
                  name="base-sucursal-spst"
                  value={s.sigesSucursalId}
                  checked={selectedId === s.sigesSucursalId}
                  onChange={() => setSelectedId(s.sigesSucursalId)}
                  className="accent-brand-orange"
                />
                <span className="flex-1 font-body text-sm">{s.descripcion}</span>
                {s.tieneCoords ? (
                  <Badge variant="success">Con coords</Badge>
                ) : (
                  <Badge variant="neutral">Sin coords</Badge>
                )}
              </label>
            ))}
          </div>
        ) : (
          <p className="font-body text-sm text-muted-foreground italic">
            No se encontraron sucursales propias del PST en Siges.
          </p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <div className="flex gap-2">
            {selectedId !== null && (
              <BrandButton
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSelectedId(null)}
              >
                Quitar base
              </BrandButton>
            )}
          </div>
          <div className="flex gap-2">
            <BrandButton type="button" variant="outline" onClick={onClose}>Cerrar</BrandButton>
            {baseCambiada && (
              <BrandButton
                type="button"
                loading={saving}
                disabled={selectedId !== null && !baseTieneCoords}
                onClick={handleGuardar}
              >
                Guardar base
              </BrandButton>
            )}
          </div>
        </div>
      </div>
    </BrandModal>
  );
}
