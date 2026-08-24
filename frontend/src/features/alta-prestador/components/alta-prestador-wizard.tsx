"use client";

import { useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import type { PrestadorLiquidacion, SigesEmpresa } from "@/features/liquidaciones/types/liquidaciones";
import { PasoDatos } from "./alta-prestador-wizard-datos";
import { PasoBase, PasoSiges } from "./alta-prestador-wizard-siges";
import { PasoCanalDirecto, PasoSla } from "./alta-prestador-wizard-cd-sla";
import { LABEL_PASO, PASOS, type PasoAlta } from "./alta-prestador-wizard-tipos";

function Indicador({ paso, resueltos }: { paso: PasoAlta; resueltos: Set<PasoAlta> }) {
  return (
    <ol className="mb-6 flex items-center justify-center" aria-label="Pasos del asistente">
      {PASOS.map((p, i) => {
        const activo = p === paso;
        const resuelto = resueltos.has(p);
        return (
          <li key={p} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full font-heading text-sm font-bold transition-colors",
                  activo && "bg-brand-orange text-white",
                  !activo && resuelto && "bg-success/15 text-success",
                  !activo && !resuelto && "border-2 border-border text-muted-foreground",
                )}
              >
                {!activo && resuelto ? "✓" : i + 1}
              </span>
              <span
                className={cn(
                  "font-body text-[10px] font-bold uppercase tracking-[.06em]",
                  activo ? "text-brand-orange" : "text-muted-foreground",
                )}
              >
                {LABEL_PASO[p]}
              </span>
            </div>
            {i < PASOS.length - 1 && <div className="mb-5 mx-3 h-[2px] w-10 flex-shrink-0 rounded-full bg-border" />}
          </li>
        );
      })}
    </ol>
  );
}

function Cierre({
  prestador,
  sigesElegida,
  resueltos,
  slaCreado,
  onClose,
}: {
  prestador: PrestadorLiquidacion;
  sigesElegida: SigesEmpresa | null;
  resueltos: Set<PasoAlta>;
  slaCreado: boolean;
  onClose: () => void;
}) {
  const filas: { label: string; ok: boolean }[] = [
    { label: "Datos básicos", ok: true },
    { label: "Vínculo Siges", ok: resueltos.has("siges") },
    { label: "Base / distancias", ok: resueltos.has("base") },
    { label: "Canal Directo", ok: resueltos.has("cd") },
    { label: "Alta en módulo SLA", ok: slaCreado },
  ];
  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm font-semibold text-foreground">
        {prestador.nombreCorto} está creado
        {sigesElegida ? ` y vinculado a Siges (#${sigesElegida.sigesEmpresaId})` : ""}.
      </p>
      <ul className="flex flex-col gap-1.5">
        {filas.map((f) => (
          <li key={f.label} className="flex items-center gap-2 font-body text-sm text-foreground">
            {f.ok ? <Badge variant="success">✓</Badge> : <Badge variant="neutral">Pendiente</Badge>}
            {f.label}
          </li>
        ))}
      </ul>
      <p className="font-body text-xs text-muted-foreground">
        Lo que quedó pendiente se completa después desde la fila del prestador en
        la tabla de Configuración.
      </p>
      <div className="flex justify-end pt-1">
        <BrandButton type="button" onClick={onClose}>Cerrar</BrandButton>
      </div>
    </div>
  );
}

/** Asistente de alta de prestador — ver `alta-prestador-wizard-tipos.ts` para
 * el porqué de la feature separada. Datos básicos es el único paso obligatorio
 * (crea la fila en liquidaciones.prestadores); los demás son saltables y
 * quedan disponibles después desde la fila del prestador en Configuración. */
export function AltaPrestadorWizard({ onClose, onCreado }: { onClose: () => void; onCreado: () => void }) {
  const [paso, setPaso] = useState<PasoAlta | "cierre">("datos");
  const [prestador, setPrestador] = useState<PrestadorLiquidacion | null>(null);
  const [sigesElegida, setSigesElegida] = useState<SigesEmpresa | null>(null);
  const [resueltos, setResueltos] = useState<Set<PasoAlta>>(new Set());
  const [slaCreado, setSlaCreado] = useState(false);

  const marcarResuelto = (p: PasoAlta) => setResueltos((prev) => new Set(prev).add(p));
  const siguienteDe = (p: PasoAlta): PasoAlta | "cierre" => PASOS[PASOS.indexOf(p) + 1] ?? "cierre";

  const handleClose = () => {
    if (prestador) onCreado();
    onClose();
  };

  return (
    <BrandModal isOpen onClose={handleClose} title="Asistente: nuevo prestador" widthPx={640}>
      {paso !== "cierre" && <Indicador paso={paso} resueltos={resueltos} />}
      <div className="min-h-[280px]">
        {paso === "datos" && (
          <PasoDatos
            onCreado={(p) => {
              setPrestador(p);
              marcarResuelto("datos");
              setPaso("siges");
            }}
          />
        )}
        {paso === "siges" && prestador && (
          <PasoSiges
            prestador={prestador}
            onVinculado={(emp) => {
              setSigesElegida(emp);
              marcarResuelto("siges");
              setPaso(siguienteDe("siges"));
            }}
            onSaltear={() => setPaso(siguienteDe("siges"))}
          />
        )}
        {paso === "base" && prestador && (
          <PasoBase
            prestador={prestador}
            sigesVinculado={sigesElegida !== null}
            onVinculado={() => {
              marcarResuelto("base");
              setPaso(siguienteDe("base"));
            }}
            onSaltear={() => setPaso(siguienteDe("base"))}
          />
        )}
        {paso === "cd" && prestador && (
          <PasoCanalDirecto
            prestador={prestador}
            onVinculado={() => {
              marcarResuelto("cd");
              setPaso(siguienteDe("cd"));
            }}
            onSaltear={() => setPaso(siguienteDe("cd"))}
          />
        )}
        {paso === "sla" && prestador && (
          <PasoSla
            prestador={prestador}
            sigesElegida={sigesElegida}
            onCreado={() => {
              setSlaCreado(true);
              marcarResuelto("sla");
              setPaso("cierre");
            }}
            onSaltear={() => setPaso("cierre")}
          />
        )}
        {paso === "cierre" && prestador && (
          <Cierre
            prestador={prestador}
            sigesElegida={sigesElegida}
            resueltos={resueltos}
            slaCreado={slaCreado}
            onClose={handleClose}
          />
        )}
      </div>
    </BrandModal>
  );
}
