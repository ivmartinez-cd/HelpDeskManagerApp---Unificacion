"use client";

import { useEffect, useState } from "react";
import { gestionApi } from "../api/gestion-api";
import type { PropuestaVinculoSiges, PropuestasVinculoSigesResult } from "../types/vacaciones";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";

/** Vínculo Empleado↔técnico de Siges (ADR-014, adaptado a Gestión de
 * Personal): propuesta de matching por nombre, confirmación siempre manual
 * por fila. Sin sync posterior — el único dato que interesa acá es el id de
 * Siges, no hay campos espejo que mantener actualizados. */
export function SigesVinculoModal({ onClose, onChanged }: { onClose: () => void; onChanged: () => void }) {
  const [resultado, setResultado] = useState<PropuestasVinculoSigesResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [vinculando, setVinculando] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // `loading` solo cubre la carga inicial (arranca en `true`); un refetch
  // posterior (post-vínculo) actualiza la lista sin tapar el modal con un
  // spinner de panel entero — el spinner por fila (`vinculando`) ya cubre eso.
  const cargar = () => {
    return gestionApi
      .listSigesPropuestas()
      .then(setResultado)
      .catch((err: unknown) => {
        console.error("Error al cargar propuestas de vínculo Siges:", err);
        setError(err instanceof Error ? err.message : "No se pudieron cargar las propuestas.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    void cargar();
  }, []);

  const vincular = (propuesta: PropuestaVinculoSiges) => {
    setVinculando(propuesta.empleadoId);
    setError(null);
    gestionApi
      .vincularEmpleadoSiges(propuesta.empleadoId, propuesta.sigesEmpresaId)
      .then(() => {
        onChanged();
        return cargar();
      })
      .catch((err: unknown) => {
        console.error("Error al vincular con Siges:", err);
        setError(err instanceof Error ? err.message : "No se pudo confirmar el vínculo.");
      })
      .finally(() => setVinculando(null));
  };

  return (
    <BrandModal isOpen title="Vincular con Siges" onClose={onClose} widthPx={640} error={error ?? undefined}>
      <p className="mb-4 font-body text-sm text-muted-foreground">
        Cruce por nombre entre los empleados de Personal y los técnicos de planta de Siges.
        Solo se proponen coincidencias sin ambigüedad — confirmá cada una a mano.
      </p>

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Spinner />
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          <section className="flex flex-col gap-2">
            <h3 className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              Propuestas ({resultado?.propuestas.length ?? 0})
            </h3>
            {!resultado || resultado.propuestas.length === 0 ? (
              <p className="font-body text-xs text-muted-foreground">
                No hay propuestas nuevas para confirmar.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {resultado.propuestas.map((p) => (
                  <div
                    key={p.empleadoId}
                    className="flex items-center justify-between gap-3 rounded-[8px] border border-border px-4 py-2.5"
                  >
                    <span className="font-body text-sm text-foreground">
                      {p.empleadoNombre}
                      <span className="mx-1.5 text-muted-foreground">↔</span>
                      {p.sigesDenComercial}
                      <span className="ml-1 text-xs text-muted-foreground">
                        (#{p.sigesEmpresaId})
                      </span>
                    </span>
                    <BrandButton
                      size="sm"
                      onClick={() => vincular(p)}
                      loading={vinculando === p.empleadoId}
                      disabled={vinculando !== null}
                    >
                      Vincular
                    </BrandButton>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              Técnicos sin par local ({resultado?.disponibles.length ?? 0})
            </h3>
            {!resultado || resultado.disponibles.length === 0 ? (
              <p className="font-body text-xs text-muted-foreground">—</p>
            ) : (
              <p className="font-body text-xs text-muted-foreground">
                {resultado.disponibles.map((d) => d.denComercial).join(" · ")}
              </p>
            )}
          </section>
        </div>
      )}
    </BrandModal>
  );
}
