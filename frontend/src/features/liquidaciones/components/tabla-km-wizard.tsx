"use client";

import { useMemo, useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Tooltip } from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/utils/cn";
import { useAsistenteKm, type DatosAsistente } from "../hooks/use-asistente-km";
import { componerBandeja, consecuenciaPendientes, resumirBandeja, type ResumenBandeja } from "../lib/asistente-km-bandeja";
import type { AplicarDistanciasResult, CalculoKmPreview, PrestadorLiquidacion } from "../types/liquidaciones";
import { MomentoRevisar } from "./tabla-km-wizard-bandeja";
import { MomentoCalcular } from "./tabla-km-wizard-calcular";
import { PantallaCierre } from "./tabla-km-wizard-cierre";
import { PantallaChequeos, PantallaIntro } from "./tabla-km-wizard-intro";
import { LABEL_MOMENTO, MOMENTOS, type FaseWizard, type Momento } from "./tabla-km-wizard-tipos";
import { MomentoTraer } from "./tabla-km-wizard-traer";

type EstadoPaso = "actual" | "bloqueado" | "pendiente" | "ok";

function estadoDeMomento(
  momento: Momento, fase: FaseWizard, datos: DatosAsistente | null, resumen: ResumenBandeja | null,
): { estado: EstadoPaso; motivo?: string } {
  if (momento === fase) return { estado: "actual" };
  if (fase === "cierre") return { estado: "ok" };
  if (!datos || !resumen) return { estado: "bloqueado" };
  const e = datos.estado;
  if (!e.vinculadoSiges && momento !== "traer") {
    return { estado: "bloqueado", motivo: "Primero vinculá el prestador a Gestión (ver Traer de Gestión)." };
  }
  switch (momento) {
    case "traer":
      return { estado: e.sucursalesNuevasPorImportar > 0 ? "pendiente" : "ok" };
    case "revisar":
      return { estado: resumen.pinesRotos + resumen.nombres + resumen.ubicaciones + resumen.sinUbicacion > 0 ? "pendiente" : "ok" };
    case "calcular":
      if (!e.baseConfigurada || !e.baseConCoordenadas) {
        return {
          estado: "bloqueado",
          motivo: !e.baseConfigurada
            ? "Falta la sucursal base de despacho (ver Traer de Gestión)."
            : "La sucursal base no tiene ubicación en Gestión (ver Traer de Gestión).",
        };
      }
      return { estado: e.filasSinKm > 0 ? "pendiente" : "ok" };
  }
}

/** Consecuencia concreta de avanzar dejando pendientes. `null` = se puede avanzar sin preguntar. */
function consecuenciaDeAvanzar(fase: FaseWizard, datos: DatosAsistente | null, resumen: ResumenBandeja | null): string | null {
  if (!datos || !resumen) return null;
  if (fase === "traer" && datos.estado.sucursalesNuevasPorImportar > 0) {
    return `Quedan ${datos.estado.sucursalesNuevasPorImportar} sucursales sin importar: no van a tener fila en tu Tabla KM ni km calculado hasta que las traigas de Gestión.`;
  }
  if (fase === "revisar") return consecuenciaPendientes(resumen);
  return null;
}

function Indicador({ fase, datos, resumen, irA }: {
  fase: FaseWizard; datos: DatosAsistente | null; resumen: ResumenBandeja | null; irA: (m: Momento) => void;
}) {
  return (
    <ol className="mb-6 flex items-center justify-center" aria-label="Momentos del asistente">
      {MOMENTOS.map((momento, i) => {
        const info = estadoDeMomento(momento, fase, datos, resumen);
        const boton = (
          <button
            type="button"
            disabled={info.estado === "bloqueado"}
            aria-current={info.estado === "actual" ? "step" : undefined}
            onClick={() => irA(momento)}
            className="flex flex-col items-center gap-1 disabled:cursor-not-allowed"
          >
            <span className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full font-heading text-sm font-bold transition-colors",
              info.estado === "actual" && "bg-brand-orange text-white",
              info.estado === "ok" && "bg-success/15 text-success",
              info.estado === "pendiente" && "bg-brand-orange/15 text-brand-orange border-2 border-brand-orange/50",
              info.estado === "bloqueado" && "border-2 border-border text-muted-foreground opacity-50",
            )}>
              {info.estado === "ok" ? "✓" : info.estado === "bloqueado" && info.motivo ? "🔒" : i + 1}
            </span>
            <span className={cn(
              "font-body text-[10px] font-bold uppercase tracking-[.06em]",
              info.estado === "actual" ? "text-brand-orange" : "text-muted-foreground",
            )}>
              {LABEL_MOMENTO[momento]}
            </span>
          </button>
        );
        return (
          <li key={momento} className="flex items-center">
            {info.motivo ? <Tooltip content={<span className="font-body text-xs">{info.motivo}</span>}>{boton}</Tooltip> : boton}
            {i < MOMENTOS.length - 1 && <div className="mb-5 mx-3 h-[2px] w-14 flex-shrink-0 rounded-full bg-border" />}
          </li>
        );
      })}
    </ol>
  );
}

/** Asistente de KM — rediseño 2026-08-20 (docs/liquidaciones/REDISENO_UX_ASISTENTE_KM.md):
 * intro → chequeos gratis → Traer de Gestión → Revisar pendientes → Calcular km → cierre. */
export function TablaKmWizard({ prestador, onClose, onAplicado }: {
  prestador: PrestadorLiquidacion; onClose: () => void; onAplicado: () => void;
}) {
  const [fase, setFase] = useState<FaseWizard>("intro");
  const [preview, setPreview] = useState<CalculoKmPreview | null>(null);
  const [aplicado, setAplicado] = useState<AplicarDistanciasResult | null>(null);
  const [salidaPendiente, setSalidaPendiente] = useState<Momento | null>(null);
  const { datos, error, progreso, recargar, correrChequeosGratis, registrarNoEncontradas } = useAsistenteKm(prestador.id);

  const resumen = useMemo(() => (datos ? resumirBandeja(componerBandeja(datos.bandeja)) : null), [datos]);

  const empezar = async () => {
    setFase("chequeos");
    await correrChequeosGratis();
    setFase("traer");
  };
  const cambio = async () => { onAplicado(); await recargar(); };
  const irA = (destino: Momento) => {
    if (estadoDeMomento(destino, fase, datos, resumen).estado === "bloqueado") return;
    setFase(destino);
  };
  const idx = MOMENTOS.indexOf(fase as Momento);
  const siguiente = idx >= 0 ? MOMENTOS[idx + 1] : undefined;
  const avanzar = () => {
    if (!siguiente) return;
    if (consecuenciaDeAvanzar(fase, datos, resumen)) setSalidaPendiente(siguiente);
    else irA(siguiente);
  };
  const alAplicar = async (res: AplicarDistanciasResult) => { setAplicado(res); await cambio(); setFase("cierre"); };

  return (
    <BrandModal isOpen onClose={onClose} title={`Asistente de KM — ${prestador.nombreCorto}`} widthPx={900}>
      <Indicador fase={fase} datos={datos} resumen={resumen} irA={irA} />
      <div className="min-h-[300px]">
        {error && <p className="mb-3 font-body text-sm text-destructive">{error}</p>}
        {fase === "intro" && <PantallaIntro onEmpezar={empezar} />}
        {fase === "chequeos" && <PantallaChequeos progreso={progreso} />}
        {fase === "traer" && datos && (
          <MomentoTraer
            prestadorId={prestador.id} nombrePrestador={prestador.nombre} datos={datos}
            onCambio={cambio} registrarNoEncontradas={registrarNoEncontradas} irARevisar={() => irA("revisar")}
          />
        )}
        {fase === "revisar" && datos && (
          <MomentoRevisar
            prestadorId={prestador.id} datos={datos} pendientesPorTope={progreso.pendientesPorTope}
            onCambio={cambio} onSeguirChequeando={correrChequeosGratis}
          />
        )}
        {fase === "calcular" && datos && (
          <MomentoCalcular
            prestador={prestador} estado={datos.estado} preview={preview} setPreview={setPreview}
            onAplicado={alAplicar} irARevisar={() => irA("revisar")}
          />
        )}
        {fase === "cierre" && aplicado && resumen && (
          <PantallaCierre prestadorId={prestador.id} aplicado={aplicado} resumen={resumen} irARevisar={() => setFase("revisar")} onClose={onClose} />
        )}
      </div>
      {idx >= 0 && (
        <div className="mt-4 flex items-center justify-end gap-2 border-t border-border pt-4">
          {idx > 0 && <BrandButton variant="outline" onClick={() => setFase(MOMENTOS[idx - 1])}>← Anterior</BrandButton>}
          {siguiente
            ? <BrandButton onClick={avanzar} disabled={!datos || estadoDeMomento(siguiente, fase, datos, resumen).estado === "bloqueado"}>Siguiente →</BrandButton>
            : <BrandButton variant="outline" onClick={onClose}>Cerrar</BrandButton>}
        </div>
      )}
      <BrandModal isOpen={salidaPendiente !== null} onClose={() => setSalidaPendiente(null)} title="Este momento quedó incompleto" widthPx={460}>
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">{consecuenciaDeAvanzar(fase, datos, resumen)}</p>
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setSalidaPendiente(null)}>Quedarme y terminarlo</BrandButton>
            <BrandButton onClick={() => { const destino = salidaPendiente; setSalidaPendiente(null); if (destino) irA(destino); }}>Continuar igual</BrandButton>
          </div>
        </div>
      </BrandModal>
    </BrandModal>
  );
}
