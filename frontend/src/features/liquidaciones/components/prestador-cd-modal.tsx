"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

/** Vínculo a Canal Directo/AyC (`cd_prestador_id`) — sin esto `SincronizarLiquidaciones`
 * clasifica al prestador como "sin vínculo" y nunca lo consulta contra wsAyC, aunque
 * ya tenga vínculo Siges. No hay catálogo de AyC para elegir de una lista: el id se
 * carga a mano (viene de Canal Directo). */
export function PrestadorCdModal({
  prestador,
  onClose,
  onSuccess,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [valor, setValor] = useState(prestador.cdPrestadorId?.toString() ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cdPrestadorId = valor.trim() === "" ? null : Number(valor);
    if (cdPrestadorId !== null && (!Number.isInteger(cdPrestadorId) || cdPrestadorId <= 0)) {
      setError("El id de Canal Directo tiene que ser un número entero positivo");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.vincularCdPrestador(prestador.id, cdPrestadorId);
      toast.success(cdPrestadorId ? "Vínculo a Canal Directo guardado" : "Vínculo a Canal Directo quitado");
      onClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title={`Vínculo a Canal Directo — ${prestador.nombreCorto}`} error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <p className="font-body text-sm text-muted-foreground">
          Id numérico del prestador en Canal Directo/AyC. Sin este vínculo, el sync
          de liquidaciones nunca consulta a wsAyC por este prestador — sus
          liquidaciones no van a entrar a la app aunque ya esté vinculado a Siges.
        </p>
        <BrandInput
          label="Id en Canal Directo"
          type="number"
          min={1}
          step={1}
          placeholder="Ej: 123"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
        />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={saving}>Guardar</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
