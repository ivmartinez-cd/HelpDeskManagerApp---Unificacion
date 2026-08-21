"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PropuestasVinculo, SyncSigesResult } from "../types/liquidaciones";

const seccionCls = "font-heading text-xs font-bold uppercase tracking-[.06em] text-muted-foreground";
const filaCls = "flex items-center justify-between gap-3 border-t border-border py-2 first:border-t-0";

function ResultadoSync({ resultado }: { resultado: SyncSigesResult }) {
  return (
    <div className="flex flex-col gap-2">
      <p className={seccionCls}>
        {resultado.dryRun ? "Cambios a aplicar (simulación)" : "Cambios aplicados"}
      </p>
      {resultado.cambios.length === 0 && (
        <p className="font-body text-sm text-muted-foreground">Sin cambios de campos espejo.</p>
      )}
      {resultado.cambios.map((c) => (
        <p key={`${c.localId}-${c.campo}`} className="font-body text-sm text-foreground">
          <span className="font-bold">{c.localNombre}</span>: {c.campo}{" "}
          <span className="text-muted-foreground line-through">{c.valorAnterior ?? "—"}</span>{" "}
          → {c.valorNuevo ?? "—"}
        </p>
      ))}
      {resultado.nombresDistintos.length > 0 && (
        <>
          <p className={`${seccionCls} mt-2`}>Nombres distintos (no se pisan)</p>
          {resultado.nombresDistintos.map((d) => (
            <p key={d.localId} className="font-body text-xs text-muted-foreground">
              {d.localNombre} · remoto: {d.sigesDenComercial}
            </p>
          ))}
        </>
      )}
      <p className="font-body text-xs text-muted-foreground mt-2">
        Sin cambios: {resultado.sinCambios}
        {resultado.sinVinculo.length > 0 && ` · Sin vínculo: ${resultado.sinVinculo.join(", ")}`}
        {resultado.vinculoRoto.length > 0 &&
          ` · Vínculo roto (ya no está activa): ${resultado.vinculoRoto.join(", ")}`}
      </p>
    </div>
  );
}

export function SigesSyncModal({
  isOpen,
  onClose,
  onChanged,
}: {
  isOpen: boolean;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [propuestas, setPropuestas] = useState<PropuestasVinculo | null>(null);
  const [resultado, setResultado] = useState<SyncSigesResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Al abrir: propuestas de vínculo + dry-run en paralelo. El componente se
  // monta solo con el modal abierto (ver prestadores-config), así que el load
  // corre una vez por apertura; estado de carga derivado (propuestas === null).
  // Promise-chain en vez de async/await: react-hooks/set-state-in-effect solo
  // acepta setState en callbacks .then/.catch (mismo patrón que el load de
  // prestadores en tarifarios-config).
  const load = useCallback(
    () =>
      Promise.all([liquidacionesApi.getSigesPropuestas(), liquidacionesApi.syncSiges(true)])
        .then(([props, dry]) => {
          setPropuestas(props);
          setResultado(dry);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al consultar");
        }),
    [],
  );

  useEffect(() => { void load(); }, [load]);

  const handleClose = () => {
    setPropuestas(null);
    setResultado(null);
    setError(null);
    onClose();
  };

  const handleVincular = async (
    entidad: "prestador" | "spst",
    localId: string,
    sigesEmpresaId: number,
  ) => {
    try {
      if (entidad === "prestador") {
        await liquidacionesApi.vincularPrestadorSiges(localId, sigesEmpresaId);
      } else {
        await liquidacionesApi.vincularSpstSiges(localId, sigesEmpresaId);
      }
      toast.success("Vínculo establecido");
      onChanged();
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al vincular");
    }
  };

  const handleAplicar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.syncSiges(false);
      setResultado(res);
      toast.success(`Sync aplicado: ${res.cambios.length} cambio(s)`);
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al sincronizar");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Sincronizar" error={error}>
      {propuestas === null || resultado === null ? (
        <div className="flex h-32 items-center justify-center">
          {!error && <Spinner />}
        </div>
      ) : (
        <div className="flex max-h-[65vh] flex-col gap-5 overflow-y-auto pr-1">
          {propuestas.propuestas.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>Propuestas de vínculo</p>
              {propuestas.propuestas.map((p) => (
                <div key={p.localId} className={filaCls}>
                  <div className="min-w-0">
                    <p className="truncate font-body text-sm text-foreground">
                      <Badge variant="neutral">{p.entidad}</Badge>{" "}
                      <span className="font-bold">{p.localNombre}</span>
                    </p>
                    <p className="truncate font-body text-xs text-muted-foreground">
                      ↔ {p.sigesDenComercial} (#{p.sigesEmpresaId})
                    </p>
                  </div>
                  <BrandButton
                    size="sm"
                    variant="outline"
                    onClick={() => handleVincular(p.entidad, p.localId, p.sigesEmpresaId)}
                  >
                    Vincular
                  </BrandButton>
                </div>
              ))}
            </div>
          )}

          <ResultadoSync resultado={resultado} />

          {propuestas.disponibles.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Sin vínculo local ({propuestas.disponibles.length}) — el alta sigue
                siendo manual
              </p>
              <div className="max-h-36 overflow-y-auto">
                {propuestas.disponibles.map((d) => (
                  <p key={d.sigesEmpresaId} className="font-body text-xs text-muted-foreground">
                    #{d.sigesEmpresaId} · {d.denComercial}
                  </p>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-1">
            <BrandButton variant="outline" onClick={handleClose}>Cerrar</BrandButton>
            <BrandButton
              loading={syncing}
              disabled={resultado.cambios.length === 0 || !resultado.dryRun}
              onClick={handleAplicar}
            >
              Aplicar sync
            </BrandButton>
          </div>
        </div>
      )}
    </BrandModal>
  );
}
