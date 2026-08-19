"use client";

import { useCallback, useEffect, useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { Tooltip } from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  CalculoKmPreview, EstadoAsistenteKm, PrestadorLiquidacion,
} from "../types/liquidaciones";
import { PasoCalcular } from "./tabla-km-wizard-calcular";
import { PasoDiagnostico } from "./tabla-km-wizard-diagnostico";
import { PasoGeocodificar } from "./tabla-km-wizard-geocodificar";
import { PasoImportar } from "./tabla-km-wizard-importar";
import { PasoMatching } from "./tabla-km-wizard-matching";
import { PasoPines } from "./tabla-km-wizard-pines";
import { LABEL_PASO, PASOS_WIZARD, type PasoWizard } from "./tabla-km-wizard-tipos";

type EstadoPaso = "actual" | "bloqueado" | "pendiente" | "ok";

function estadoDePaso(
  paso: PasoWizard, actual: PasoWizard, e: EstadoAsistenteKm | null,
): { estado: EstadoPaso; motivo?: string } {
  if (paso === actual) return { estado: "actual" };
  if (!e || paso === "diagnostico") return { estado: "ok" };
  if (!e.vinculadoSiges) {
    return { estado: "bloqueado", motivo: "Primero vinculá el prestador a Gestión (ver Diagnóstico)." };
  }
  switch (paso) {
    case "importar":
      return { estado: e.sucursalesNuevasPorImportar > 0 ? "pendiente" : "ok" };
    case "matching":
      return { estado: e.noEncontradasEnSiges > 0 ? "pendiente" : "ok" };
    case "ubicar":
      return {
        estado: e.sinCoordenadas + e.ambiguasPendientes > 0 ? "pendiente" : "ok",
      };
    case "distancias":
      if (!e.baseConfigurada || !e.baseConCoordenadas) {
        return {
          estado: "bloqueado",
          motivo: !e.baseConfigurada
            ? "Falta la sucursal base de despacho (ver Diagnóstico)."
            : "La sucursal base no tiene ubicación en Gestión (ver Diagnóstico).",
        };
      }
      return { estado: e.filasSinKm > 0 ? "pendiente" : "ok" };
    case "pines":
      return { estado: e.pinesSospechososCacheados > 0 ? "pendiente" : "ok" };
    default:
      return { estado: "ok" };
  }
}

/** Consecuencia concreta de avanzar dejando pendientes — reemplaza al viejo
 * "Omitir este paso" ciego. `null` = se puede avanzar sin preguntar. */
function consecuenciaDeAvanzar(paso: PasoWizard, e: EstadoAsistenteKm | null): string | null {
  if (!e) return null;
  if (paso === "importar" && e.sucursalesNuevasPorImportar > 0) {
    return `Quedan ${e.sucursalesNuevasPorImportar} sucursales sin importar: no van a tener fila en tu Tabla KM ni km calculado hasta que las importes.`;
  }
  if (paso === "matching" && e.noEncontradasEnSiges > 0) {
    return `Quedan ${e.noEncontradasEnSiges} filas sin vincular a una sucursal de Gestión: no van a poder ubicarse ni calcular km hasta que las resuelvas.`;
  }
  if (paso === "ubicar" && e.sinCoordenadas + e.ambiguasPendientes > 0) {
    const partes = [];
    if (e.sinCoordenadas > 0) partes.push(`${e.sinCoordenadas} sucursales sin ubicación`);
    if (e.ambiguasPendientes > 0) partes.push(`${e.ambiguasPendientes} direcciones sin resolver`);
    return `Quedan ${partes.join(" y ")}: esas sucursales van a quedar SIN km cuando calcules distancias.`;
  }
  return null;
}

function Indicador({ actual, estado, irA }: {
  actual: PasoWizard;
  estado: EstadoAsistenteKm | null;
  irA: (p: PasoWizard) => void;
}) {
  return (
    <div className="mb-6 flex items-center justify-center">
      {PASOS_WIZARD.map((paso, i) => {
        const info = estadoDePaso(paso, actual, estado);
        const boton = (
          <button
            type="button"
            disabled={info.estado === "bloqueado"}
            onClick={() => irA(paso)}
            className="flex flex-col items-center gap-1 disabled:cursor-not-allowed"
          >
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full font-heading text-sm font-bold transition-colors",
              info.estado === "actual" && "bg-brand-orange text-white",
              info.estado === "ok" && "bg-emerald-500/15 text-emerald-500",
              info.estado === "pendiente" && "bg-brand-orange/15 text-brand-orange border-2 border-brand-orange/50",
              info.estado === "bloqueado" && "border-2 border-border text-muted-foreground opacity-50",
            )}>
              {info.estado === "ok" ? "✓" : info.estado === "bloqueado" ? "🔒" : i + 1}
            </div>
            <span className={cn(
              "font-body text-[10px] font-bold uppercase tracking-[.06em]",
              info.estado === "actual" ? "text-brand-orange" : "text-muted-foreground",
            )}>
              {LABEL_PASO[paso]}
            </span>
          </button>
        );
        return (
          <div key={paso} className="flex items-center">
            {info.motivo
              ? <Tooltip content={<span className="font-body text-xs">{info.motivo}</span>}>{boton}</Tooltip>
              : boton}
            {i < PASOS_WIZARD.length - 1 && (
              <div className="mb-5 mx-3 h-[2px] w-10 flex-shrink-0 rounded-full bg-border" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function TablaKmWizard({ prestador, onClose, onAplicado }: {
  prestador: PrestadorLiquidacion; onClose: () => void; onAplicado: () => void;
}) {
  const [paso, setPaso] = useState<PasoWizard>("diagnostico");
  const [estado, setEstado] = useState<EstadoAsistenteKm | null>(null);
  const [errorEstado, setErrorEstado] = useState<string | null>(null);
  const [preview, setPreview] = useState<CalculoKmPreview | null>(null);
  const [salidaPendiente, setSalidaPendiente] = useState<PasoWizard | null>(null);

  const refrescarEstado = useCallback(() => {
    liquidacionesApi.estadoAsistenteKm(prestador.id)
      .then((e) => { setEstado(e); setErrorEstado(null); })
      .catch(() => setErrorEstado("No se pudo leer el estado del asistente. Cerrá y volvé a abrir."));
  }, [prestador.id]);
  useEffect(() => { refrescarEstado(); }, [refrescarEstado]);

  const cambio = () => { onAplicado(); refrescarEstado(); };

  const irA = (destino: PasoWizard) => {
    if (estadoDePaso(destino, paso, estado).estado === "bloqueado") return;
    setPaso(destino);
  };
  const idx = PASOS_WIZARD.indexOf(paso);
  const siguiente = PASOS_WIZARD[idx + 1] as PasoWizard | undefined;
  const avanzar = () => {
    if (!siguiente) return;
    const consecuencia = consecuenciaDeAvanzar(paso, estado);
    if (consecuencia) setSalidaPendiente(siguiente);
    else irA(siguiente);
  };

  return (
    <BrandModal isOpen onClose={onClose} title={`Asistente de KM — ${prestador.nombreCorto}`} widthPx={900}>
      <Indicador actual={paso} estado={estado} irA={irA} />
      <div className="min-h-[300px]">
        {errorEstado && <p className="font-body text-sm text-destructive">{errorEstado}</p>}
        {!estado && !errorEstado && (
          <div className="flex h-40 flex-col items-center justify-center gap-3">
            <Spinner />
            <p className="font-body text-sm text-muted-foreground">Revisando el estado de tu Tabla KM… (no consulta Google)</p>
          </div>
        )}
        {estado && paso === "diagnostico" && (
          <PasoDiagnostico estado={estado} nombrePrestador={prestador.nombre} irA={irA} />
        )}
        {estado && paso === "importar" && (
          <PasoImportar prestadorId={prestador.id} onCambio={cambio} />
        )}
        {estado && paso === "matching" && (
          <PasoMatching prestadorId={prestador.id} onCambio={cambio} />
        )}
        {estado && paso === "ubicar" && (
          <PasoGeocodificar prestadorId={prestador.id} estado={estado} onCambio={cambio} />
        )}
        {estado && paso === "distancias" && (
          <PasoCalcular
            prestador={prestador} estado={estado} preview={preview}
            setPreview={setPreview} onCambio={cambio} irAUbicar={() => irA("ubicar")}
          />
        )}
        {estado && paso === "pines" && (
          <PasoPines prestadorId={prestador.id} estado={estado} onCambio={cambio} />
        )}
      </div>
      <div className="mt-4 flex items-center justify-end gap-2 border-t border-border pt-4">
        {idx > 0 && <BrandButton variant="outline" onClick={() => setPaso(PASOS_WIZARD[idx - 1])}>← Anterior</BrandButton>}
        {siguiente
          ? (
            <BrandButton
              onClick={avanzar}
              disabled={!estado || estadoDePaso(siguiente, paso, estado).estado === "bloqueado"}
            >
              Siguiente →
            </BrandButton>
          )
          : <BrandButton onClick={onClose}>Finalizar</BrandButton>}
      </div>
      <BrandModal
        isOpen={salidaPendiente !== null}
        onClose={() => setSalidaPendiente(null)}
        title="Este paso quedó incompleto"
        widthPx={460}
      >
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">{consecuenciaDeAvanzar(paso, estado)}</p>
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setSalidaPendiente(null)}>
              Quedarme y terminarlo
            </BrandButton>
            <BrandButton onClick={() => { const destino = salidaPendiente; setSalidaPendiente(null); if (destino) irA(destino); }}>
              Continuar igual
            </BrandButton>
          </div>
        </div>
      </BrandModal>
    </BrandModal>
  );
}
