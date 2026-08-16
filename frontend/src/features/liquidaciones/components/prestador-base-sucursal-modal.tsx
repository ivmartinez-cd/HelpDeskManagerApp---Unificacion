"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, SucursalPropia } from "../types/liquidaciones";

export function PrestadorBaseSucursalModal({
  prestador,
  onClose,
  onChanged,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [sucursales, setSucursales] = useState<SucursalPropia[] | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(prestador.sigesBaseSucursalId);
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
      await liquidacionesApi.vincularBaseSucursal(prestador.id, selectedId);
      toast.success(selectedId ? "Sucursal base guardada" : "Base desvinculada");
      onChanged();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const baseCambiada = selectedId !== prestador.sigesBaseSucursalId;
  const baseTieneCoords = sucursales?.find((s) => s.sigesSucursalId === selectedId)?.tieneCoords ?? false;

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Sucursal base — ${prestador.nombreCorto}`}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          Seleccioná la sede del PST desde donde se calculan las distancias a los clientes.
          La sucursal debe tener coordenadas cargadas en Gestión.
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
                  name="base-sucursal"
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
            Verificá que el vínculo Siges del prestador esté configurado.
          </p>
        )}

        {prestador.sigesBaseSucursalId !== null && !baseCambiada && (
          <p className="font-body text-xs text-muted-foreground">
            El cálculo de distancias (con preview de km ida y vuelta) se hace desde la
            pantalla Tabla KM con este prestador seleccionado.
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
