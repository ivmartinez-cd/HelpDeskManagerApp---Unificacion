"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { clientesNuevosApi } from "../api/clientes-nuevos-api";
import type { CandidatoClienteNuevo } from "../types/clientes-nuevos";
import { RUBRO_LABEL, formatFecha } from "../lib/clientes-nuevos";
import {
  BrandBadge,
  BrandButton,
  BrandEmptyState,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";

interface Props {
  onClose: () => void;
  onElegir: (candidato: CandidatoClienteNuevo) => void;
}

const DIAS = 120;

/** Empresas de Siges con su primer contrato firmado en los últimos 120 días
 * y sin ficha todavía: la TL crea la ficha desde acá con cliente, contrato,
 * firma y vendedor ya cargados (es lo mismo que trae el mail de Comercial). */
export function ClientesNuevosCandidatosModal({ onClose, onElegir }: Props) {
  const [candidatos, setCandidatos] = useState<CandidatoClienteNuevo[] | null>(null);
  const [desde, setDesde] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    clientesNuevosApi
      .candidatos(DIAS)
      .then((r) => {
        setCandidatos(r.candidatos);
        setDesde(r.firmado_desde);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar candidatos de Siges:", err);
        setError("No se pudo consultar Siges. Reintentá en un momento.");
      });
  }, []);

  return (
    <BrandModal isOpen onClose={onClose} title="Sugerencias de Siges" widthPx={720} error={error}>
      <p className="-mt-2 mb-4 font-body text-xs text-muted-foreground">
        Empresas cliente con su <strong>primer contrato</strong> firmado
        {desde ? ` desde el ${formatFecha(desde)}` : ` en los últimos ${DIAS} días`} y sin ficha.
        El rubro sale de quién administra el contrato (CD3 = impresión, CD4 = cartelería).
      </p>
      {candidatos === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}
      {candidatos !== null && candidatos.length === 0 && (
        <BrandEmptyState
          icon={Sparkles}
          title="Nada pendiente"
          description="Todas las empresas con primer contrato reciente ya tienen ficha."
        />
      )}
      {candidatos !== null && candidatos.length > 0 && (
        <ul className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto pr-1">
          {candidatos.map((c) => (
            <li
              key={c.empresa_id}
              className="flex items-center justify-between gap-3 rounded-[10px] border border-border bg-card px-4 py-3"
            >
              <div className="min-w-0 leading-tight">
                <div className="flex items-center gap-2">
                  <p className="truncate font-body text-sm font-semibold text-foreground">
                    {c.cliente}
                  </p>
                  <BrandBadge variant={c.rubro === "IMPRESION" ? "accent" : "neutral"}>
                    {RUBRO_LABEL[c.rubro] ?? c.rubro}
                  </BrandBadge>
                </div>
                <p className="truncate font-body text-xs text-muted-foreground">
                  {c.contrato_nro ?? "Sin N° de contrato"} · firma {formatFecha(c.fecha_firma)}
                  {c.vendedor ? ` · ${c.vendedor}` : ""} · {c.equipos_instalados} equipo
                  {c.equipos_instalados === 1 ? "" : "s"} instalado
                  {c.equipos_instalados === 1 ? "" : "s"}
                </p>
              </div>
              <BrandButton size="sm" variant="outline" onClick={() => onElegir(c)}>
                Crear ficha
              </BrandButton>
            </li>
          ))}
        </ul>
      )}
    </BrandModal>
  );
}
