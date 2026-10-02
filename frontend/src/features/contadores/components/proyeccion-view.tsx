"use client";

import Link from "next/link";
import { Loader2 } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { useTableroProyeccion } from "../hooks/use-tablero-proyeccion";
import { ProyeccionGrilla } from "./proyeccion-grilla";
import { ProyeccionBannerRestauracion } from "./proyeccion-resumen";
import { ProyeccionSelectores } from "./proyeccion-selectores";

/** Pantalla de Proyección — `Index.razor` del Estimador v1.7: combos,
 * "Cargar", errores de conexión/carga, banner de restauración y la grilla
 * del tablero cargado. */

function Alerta({ titulo, detalle, children }: { titulo: string; detalle: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
      <strong>{titulo}</strong>
      <p className="text-muted-foreground">{detalle}</p>
      {children}
    </div>
  );
}

// Relectura tras una acción del operador: en procesos grandes (San Juan,
// ~800 filas) Siges tarda ~10 s y sin aviso la grilla parecía no actualizarse.
function AvisoActualizando() {
  return (
    <div role="status" className="fixed bottom-6 right-6 z-[110] flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 font-body text-xs font-semibold text-foreground shadow-lg">
      <Loader2 className="h-4 w-4 animate-spin text-brand-orange" />
      Actualizando grilla…
    </div>
  );
}

function Encabezado() {
  return (
    <>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">Centro de Contadores</Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Estimador de contadores</span>
        <Link href="/contadores/proyeccion/recesos" className="ml-auto hover:text-foreground">Recesos →</Link>
      </div>
      <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
        Estimador de contadores
      </h1>
    </>
  );
}

export function ProyeccionView() {
  const { can, hasFeature } = useSession();
  const puedeOperar = can("contadores", "manage") || hasFeature("contadores-proyeccion-operar");
  const t = useTableroProyeccion();
  const { tablero } = t;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <Encabezado />
      {t.errorConexion && <Alerta titulo="Error conectando a SiGes." detalle={t.errorConexion} />}

      <ProyeccionSelectores
        grupos={t.grupos}
        procesosVisibles={t.procesosVisibles}
        idGrupo={t.idGrupo}
        idProcesoValido={t.idProcesoValido}
        procesoElegido={t.procesoElegido}
        fechaObjetivo={t.fechaObjetivo}
        cargando={t.cargando}
        onChangeGrupo={t.elegirGrupo}
        onChangeProceso={t.elegirProceso}
        onChangeFecha={t.setFechaObjetivo}
        onCargar={t.cargar}
      />

      {t.error && (
        <Alerta titulo="Error al cargar la grilla." detalle={t.error}>
          <BrandButton variant="outline" size="sm" className="mt-2" onClick={tablero ? t.recargar : t.cargar}>
            Reintentar
          </BrandButton>
        </Alerta>
      )}

      {t.banner && (
        <ProyeccionBannerRestauracion restauracion={t.banner} onDescartar={t.descartarRestauracion} onCerrar={t.ocultarBanner} />
      )}

      {tablero && t.cargando && <AvisoActualizando />}

      {tablero ? (
        <ProyeccionGrilla
          tablero={tablero}
          contexto={t.contexto}
          descartes={t.descartes}
          puedeOperar={puedeOperar}
          recargar={t.recargar}
        />
      ) : (
        <p className="text-sm text-muted-foreground">
          {t.cargando
            ? "Cargando grilla de estimación…"
            : "Elegí un grupo económico y un proceso (o dejalo en blanco para ver datos de ejemplo) y apretá Cargar."}
        </p>
      )}
    </div>
  );
}
