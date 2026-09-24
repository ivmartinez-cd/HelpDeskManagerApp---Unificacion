"use client";

import Link from "next/link";
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

function Encabezado() {
  return (
    <>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">Centro de Contadores</Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Proyección</span>
        <Link href="/contadores/proyeccion/recesos" className="ml-auto hover:text-foreground">Recesos →</Link>
      </div>
      <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
        Proyección de contadores
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
