"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import type { EstadoChequeo, ProgresoChequeos } from "../hooks/use-asistente-km";

const MOMENTOS_INTRO = [
  {
    numero: "①",
    titulo: "Traer de Gestión",
    texto: "Actualiza domicilios y vínculos, importa las sucursales nuevas con actividad y vincula sola las que solo difieren en un símbolo o una abreviatura. No consulta Google.",
  },
  {
    numero: "②",
    titulo: "Revisar pendientes",
    texto: "Una sola lista con lo que necesita tu decisión: nombres por confirmar, ubicaciones por elegir y pines que los chequeos automáticos marcaron como rotos. Lo que haya que corregir en Gestión se exporta en un CSV.",
  },
  {
    numero: "③",
    titulo: "Calcular km",
    texto: "Calcula ida y vuelta con Google Maps, te muestra el resultado y recién cuando aplicás se guarda. El umbral de viático y las observaciones no se tocan.",
  },
];

/** Pantalla de entrada (decisión 0.4.a): siempre se muestra; un solo botón. */
export function PantallaIntro({ onEmpezar }: { onEmpezar: () => void }) {
  return (
    <div className="flex flex-col gap-5">
      <p className="font-body text-sm text-foreground">
        Este asistente deja tu Tabla KM al día en tres momentos:
      </p>
      <ol className="flex flex-col gap-4">
        {MOMENTOS_INTRO.map((m) => (
          <li key={m.titulo} className="flex gap-3">
            <span className="font-heading text-lg font-extrabold text-brand-orange" aria-hidden>{m.numero}</span>
            <div>
              <p className="font-body text-sm font-semibold text-foreground">{m.titulo}</p>
              <p className="font-body text-sm text-muted-foreground">{m.texto}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="font-body text-sm text-muted-foreground">
        Nada consulta Google sin mostrarte antes cuántas consultas cuesta.
      </p>
      <BrandButton onClick={onEmpezar} className="self-start">Empezar</BrandButton>
    </div>
  );
}

const ICONO: Record<EstadoChequeo, string> = { pendiente: "○", corriendo: "●", ok: "✓", error: "!" };

function Chequeo({ estado, texto, textoError }: { estado: EstadoChequeo; texto: string; textoError: string }) {
  return (
    <li className="flex items-center gap-3 font-body text-sm">
      <span
        aria-hidden
        className={cn(
          "w-4 text-center font-bold",
          estado === "ok" && "text-success",
          estado === "corriendo" && "text-brand-orange animate-pulse",
          estado === "error" && "text-warning",
          estado === "pendiente" && "text-muted-foreground",
        )}
      >
        {ICONO[estado]}
      </span>
      <span className={estado === "pendiente" ? "text-muted-foreground" : "text-foreground"}>
        {estado === "error" ? textoError : texto}
      </span>
    </li>
  );
}

/** Chequeos que corren tras "Empezar": solo lectura + chequeos gratis de pines.
 * Nada escribe en la Tabla KM. */
export function PantallaChequeos({ progreso }: { progreso: ProgresoChequeos }) {
  return (
    <div className="flex flex-col gap-4" aria-live="polite">
      <div className="flex items-center gap-3">
        <Spinner />
        <p className="font-body text-sm font-semibold text-foreground">Analizando tu Tabla KM…</p>
      </div>
      <ul className="flex flex-col gap-2">
        <Chequeo estado={progreso.lectura} texto="Leímos tu Tabla KM y las sucursales de Gestión" textoError="No pudimos leer el estado — se reintenta al recargar" />
        <Chequeo estado={progreso.georef} texto="Comparamos la provincia de cada pin con datos oficiales (sin costo)" textoError="El chequeo de provincia no pudo completarse — se reintenta la próxima vez" />
        <Chequeo estado={progreso.nominatim} texto="Pedimos una segunda opinión sobre los pines dudosos (sin costo)" textoError="La segunda opinión no pudo completarse — se reintenta la próxima vez" />
      </ul>
      <p className="font-body text-xs text-muted-foreground">
        Nada de esto consulta Google; el costo de cada acción se muestra antes.
      </p>
    </div>
  );
}
