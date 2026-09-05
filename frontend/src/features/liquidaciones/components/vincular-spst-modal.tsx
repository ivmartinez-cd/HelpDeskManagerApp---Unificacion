"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { ResultadoVinculoTablaKmSpst } from "../types/liquidaciones";

const seccionCls = "font-heading text-xs font-bold uppercase tracking-[.06em] text-muted-foreground";

// Dry-run al abrir (promise-chain: ver nota en siges-tarifarios-modal.tsx sobre
// set-state-in-effect); "Vincular" repite la llamada con dryRun=false.
export function VincularSpstModal({
  prestadorId, onClose, onVinculado,
}: {
  prestadorId: string; onClose: () => void; onVinculado: () => void;
}) {
  const [resultado, setResultado] = useState<ResultadoVinculoTablaKmSpst | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aplicando, setAplicando] = useState(false);
  // Las propuestas por provincia son un proxy más débil que la localidad (la
  // provincia no siempre coincide con la zona tarifaria): se aplican solo si
  // la TL lo tilda para este prestador.
  const [incluirProvincia, setIncluirProvincia] = useState(false);

  const load = useCallback(
    () =>
      liquidacionesApi
        .vincularSpstTablaKm(prestadorId, true, incluirProvincia)
        .then((r) => { setResultado(r); setError(null); })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al calcular vínculos");
        }),
    [prestadorId, incluirProvincia],
  );

  useEffect(() => { void load(); }, [load]);

  const handleAplicar = async () => {
    setAplicando(true);
    try {
      const res = await liquidacionesApi.vincularSpstTablaKm(prestadorId, false, incluirProvincia);
      setResultado(res);
      toast.success(`${res.vinculadas} fila(s) vinculada(s)`);
      onVinculado();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al vincular");
    } finally {
      setAplicando(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Vincular SPST por localidad o provincia" error={error}>
      {resultado === null ? (
        <div className="flex h-32 items-center justify-center">{!error && <Spinner />}</div>
      ) : (
        <div className="flex max-h-[65vh] flex-col gap-4 overflow-y-auto pr-1">
          <p className="font-body text-sm text-muted-foreground">
            Cruza la localidad de cada fila sin SPST contra la zona/localidad de los SPST de
            este prestador. Solo propone cuando hay un único candidato — el resto queda para
            vínculo manual.
          </p>
          {resultado.porProvincia > 0 && (
            <label className="flex items-start gap-2 font-body text-sm text-foreground">
              <input
                type="checkbox"
                className="mt-1"
                checked={incluirProvincia}
                onChange={(e) => setIncluirProvincia(e.target.checked)}
                disabled={aplicando || !resultado.dryRun}
              />
              <span>
                Incluir también las {resultado.porProvincia} propuesta(s) por provincia
                (único SPST de esa provincia). Es un proxy más débil: la provincia no siempre
                coincide con la zona tarifaria — revisá los ejemplos antes de aplicar.
              </span>
            </label>
          )}
          <div className="flex gap-3">
            <div className="flex-1 rounded-[10px] border border-border bg-muted/30 p-3 text-center">
              <p className="font-body text-lg font-bold text-foreground">{resultado.totalSinVincular}</p>
              <p className="font-body text-[11px] text-muted-foreground">Sin SPST</p>
            </div>
            <div className="flex-1 rounded-[10px] border border-success/20 bg-success/10 p-3 text-center">
              <p className="font-body text-lg font-bold text-success">{resultado.conPropuesta}</p>
              <p className="font-body text-[11px] text-muted-foreground">Con propuesta</p>
            </div>
            <div className="flex-1 rounded-[10px] border border-border bg-muted/30 p-3 text-center">
              <p className="font-body text-lg font-bold text-foreground">{resultado.sinPropuesta}</p>
              <p className="font-body text-[11px] text-muted-foreground">Sin match</p>
            </div>
          </div>

          {resultado.ejemplos.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Ejemplos {resultado.ejemplos.length < resultado.totalSinVincular ? `(primeros ${resultado.ejemplos.length} de ${resultado.totalSinVincular})` : ""}
              </p>
              {resultado.ejemplos.map((e) => (
                <p key={e.tablaKmId} className="border-t border-border py-1.5 font-body text-xs text-muted-foreground first:border-t-0">
                  <span className="text-foreground">{e.sucursalNombre}</span> · {e.localidadCliente ?? "sin localidad"} →{" "}
                  {e.spstNombre ? <span className="font-semibold text-success">{e.spstNombre}</span> : <span className="text-muted-foreground">sin match</span>}
                  {e.criterio === "provincia" && <span className="ml-1 text-muted-foreground">(por provincia)</span>}
                </p>
              ))}
            </div>
          )}

          {!resultado.dryRun && (
            <p className="font-body text-sm font-semibold text-success">
              {resultado.vinculadas} fila(s) vinculada(s). Las liquidaciones abiertas de este
              prestador se reanalizaron solas con los precios de zona nuevos.
            </p>
          )}

          <div className="flex justify-end gap-3 pt-1">
            <BrandButton variant="outline" onClick={onClose}>Cerrar</BrandButton>
            <BrandButton
              loading={aplicando}
              disabled={resultado.conPropuesta === 0 || !resultado.dryRun}
              onClick={handleAplicar}
            >
              Vincular {resultado.conPropuesta > 0 ? `(${resultado.conPropuesta})` : ""}
            </BrandButton>
          </div>
        </div>
      )}
    </BrandModal>
  );
}
