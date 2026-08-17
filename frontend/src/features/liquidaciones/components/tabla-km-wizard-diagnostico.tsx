"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { EstadoAsistenteKm } from "../types/liquidaciones";
import type { PasoWizard } from "./tabla-km-wizard-tipos";

type Nivel = "bloqueante" | "pendiente" | "ok";

interface Renglon {
  nivel: Nivel;
  texto: string;
  detalle?: string;
  /** Paso al que lleva la acción; sin paso = solo instrucción. */
  irA?: PasoWizard;
  accionLabel?: string;
}

/** Deriva el checklist en el orden en que conviene resolverlo. El primer
 * renglón no-verde es la "siguiente acción recomendada". */
export function derivarRenglones(e: EstadoAsistenteKm, nombrePrestador: string): Renglon[] {
  if (!e.vinculadoSiges) {
    return [{
      nivel: "bloqueante",
      texto: "Este prestador no está vinculado a Gestión",
      detalle: `Sin ese vínculo el asistente no puede leer sus sucursales. Se configura en Configuración → Prestadores → ${nombrePrestador} → Vincular con Siges.`,
    }];
  }
  const renglones: Renglon[] = [];
  if (!e.baseConfigurada) {
    renglones.push({
      nivel: "bloqueante",
      texto: "Falta la sucursal base de despacho",
      detalle: `Es el punto desde donde sale el técnico — sin ella no se pueden calcular km. Se configura en Configuración → Prestadores → ${nombrePrestador}, campo Sucursal base.`,
    });
  } else if (!e.baseConCoordenadas) {
    renglones.push({
      nivel: "bloqueante",
      texto: "La sucursal base no tiene ubicación en Gestión",
      detalle: "Su latitud y longitud están vacías o en cero. Hay que cargar las coordenadas reales en Gestión, en la sucursal del prestador.",
    });
  }
  if (e.sucursalesNuevasPorImportar > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.sucursalesNuevasPorImportar} sucursal${e.sucursalesNuevasPorImportar !== 1 ? "es" : ""} nueva${e.sucursalesNuevasPorImportar !== 1 ? "s" : ""} para importar desde Gestión`,
      irA: "importar",
      accionLabel: "Ir a Importar",
    });
  }
  if (e.sinCoordenadas > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.sinCoordenadas} sucursal${e.sinCoordenadas !== 1 ? "es" : ""} sin ubicación en el mapa`,
      detalle: `Sin ubicación no se les puede calcular km. Buscarlas cuesta ~${e.estimacionGeocodificar} consultas a Google.`,
      irA: "ubicar",
      accionLabel: "Ir a Ubicar",
    });
  }
  if (e.ambiguasPendientes > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.ambiguasPendientes} dirección${e.ambiguasPendientes !== 1 ? "es" : ""} con más de un resultado posible`,
      detalle: "Google devolvió varias opciones — elegí vos la correcta (no cuesta consultas).",
      irA: "ubicar",
      accionLabel: "Resolver",
    });
  }
  if (e.noEncontradasEnSiges > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.noEncontradasEnSiges} fila${e.noEncontradasEnSiges !== 1 ? "s" : ""} de tu tabla no aparece${e.noEncontradasEnSiges !== 1 ? "n" : ""} en Gestión`,
      detalle: "Puede que hayan cambiado de nombre o ya no estén asignadas al prestador. En el paso Ubicar, \"Actualizar desde Gestión\" te muestra cuáles.",
      irA: "ubicar",
      accionLabel: "Ver cuáles",
    });
  }
  if (e.filasSinKm > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.filasSinKm} fila${e.filasSinKm !== 1 ? "s" : ""} sin km calculado`,
      detalle: `Calcular distancias cuesta ~${e.estimacionDistancias} consultas a Google (ida y vuelta por sucursal).`,
      irA: "distancias",
      accionLabel: "Ir a Distancias",
    });
  }
  if (e.pinesSospechososCacheados > 0) {
    renglones.push({
      nivel: "pendiente",
      texto: `${e.pinesSospechososCacheados} pin${e.pinesSospechososCacheados !== 1 ? "es" : ""} del mapa que no coincide${e.pinesSospechososCacheados !== 1 ? "n" : ""} con la dirección`,
      detalle: "El pin de Gestión está a más de 5 km de la dirección escrita — conviene revisarlos.",
      irA: "pines",
      accionLabel: "Revisar pines",
    });
  }
  if (renglones.length === 0) {
    renglones.push({
      nivel: "ok",
      texto: "Tu Tabla KM está completa",
      detalle: `${e.filasTablaKm} filas, todas con km y ubicación al día. No hay nada pendiente.`,
    });
  }
  return renglones;
}

const PUNTO: Record<Nivel, string> = {
  bloqueante: "bg-destructive",
  pendiente: "bg-brand-orange",
  ok: "bg-emerald-500",
};

export function PasoDiagnostico({ estado, nombrePrestador, irA }: {
  estado: EstadoAsistenteKm;
  nombrePrestador: string;
  irA: (paso: PasoWizard) => void;
}) {
  const renglones = derivarRenglones(estado, nombrePrestador);
  const recomendado = renglones.find((r) => r.nivel !== "ok");

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Esto es lo que el asistente encontró revisando tu Tabla KM contra Gestión.
        Nada de lo que ves acá gastó consultas de Google — el costo de cada acción se
        muestra antes de ejecutarla.
      </p>
      <div className="rounded-[8px] border border-border divide-y divide-border">
        {renglones.map((r) => (
          <div key={r.texto} className="flex items-start justify-between gap-3 px-4 py-3">
            <div className="flex items-start gap-3">
              <span className={cn("mt-1.5 h-[9px] w-[9px] flex-shrink-0 rounded-full", PUNTO[r.nivel])} />
              <div>
                <p className="font-body text-sm font-semibold text-foreground">{r.texto}</p>
                {r.detalle && (
                  <p className="mt-0.5 font-body text-xs text-muted-foreground">{r.detalle}</p>
                )}
              </div>
            </div>
            {r.irA && (
              <BrandButton size="sm" variant="outline" onClick={() => irA(r.irA as PasoWizard)}>
                {r.accionLabel}
              </BrandButton>
            )}
          </div>
        ))}
      </div>
      {recomendado?.irA && (
        <BrandButton className="self-start" onClick={() => irA(recomendado.irA as PasoWizard)}>
          Siguiente paso recomendado: {recomendado.accionLabel} →
        </BrandButton>
      )}
    </div>
  );
}
