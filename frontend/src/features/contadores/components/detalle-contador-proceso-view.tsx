"use client";

import Link from "next/link";
import { Copy, Download, Mail } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { BrandButton, brandButtonClasses } from "@/shared/components/ui/brand-form";
import { compareSortValues, useTableSort, type SortValue } from "@/shared/hooks/use-table-sort";
import { cn } from "@/shared/utils/cn";
import { proyeccionApi } from "../api/proyeccion-api";
import { detalleContadorProcesoApi, type AlcanceReporte } from "../api/detalle-contador-proceso-api";
import { formatearTablaWhatsapp } from "../lib/formato-whatsapp";
import { formatearTablaMailHtml, formatearTablaMailTexto } from "../lib/formato-mail";
import { copiarHtmlYTexto, copiarTexto } from "@/shared/utils/clipboard";
import type { GrupoEconomicoOption, ProcesoOption } from "../types/proyeccion";
import type { DetalleContadorProceso, DetalleContadorRow } from "../types/detalle-contador-proceso";
import { DetalleContadorTabla, SORT_KEYS, type SortKey } from "./detalle-contador-tabla";

const ALCANCES: { value: AlcanceReporte; label: string }[] = [
  { value: "todos", label: "Todo el proceso" },
  { value: "falta_contador", label: "Solo Falta Contador" },
];

function valorOrdenable(fila: DetalleContadorRow, key: SortKey): SortValue {
  return fila[key];
}

/** Reporte "Detalle de contadores por nro de proceso" — reconstrucción del
 * reporte legacy SSRS (`reportes.cdsa.com.ar:8090`), con el mismo circuito
 * de selección Grupo económico → Proceso que ya usa Proyección/Estimador
 * (misma noción de "cliente" del resto del módulo). Toda columna es
 * ordenable (pedido del usuario: "toda tabla se tiene que poder filtrar
 * por la columna" — acá se resolvió como orden ascendente/descendente al
 * click del título, mismo patrón que `proyeccion-tabla.tsx`).
 *
 * Elegir un cliente ya trae TODOS sus anexos/procesos recientes en una sola
 * consulta (pedido del usuario, 2026-09-17: antes había que elegir también
 * un proceso puntual para poder cargar). El selector de Proceso queda como
 * filtro opcional sobre lo ya cargado — click de nuevo sobre la opción
 * elegida la deselecciona (comportamiento propio de `SearchableSelect`). */
export function DetalleContadorProcesoView() {
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [procesos, setProcesos] = useState<ProcesoOption[]>([]);
  const [idGrupo, setIdGrupo] = useState<string | null>(null);
  const [idProceso, setIdProceso] = useState<string | null>(null);
  const [alcance, setAlcance] = useState<AlcanceReporte>("falta_contador");

  const [detalle, setDetalle] = useState<DetalleContadorProceso | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { sort, toggleSort } = useTableSort<SortKey>({
    initial: { key: "empresa", direction: "asc" },
    keys: SORT_KEYS,
  });

  useEffect(() => {
    void proyeccionApi.listGruposEconomicos().then(setGrupos);
  }, []);

  useEffect(() => {
    if (idGrupo == null) return;
    void proyeccionApi.listProcesos(Number(idGrupo)).then(setProcesos);
  }, [idGrupo]);

  // Disparado desde el onChange del selector de cliente (evento de usuario,
  // no un efecto) para no resetear cargando/error/detalle sincrónicamente
  // dentro de un useEffect (react-hooks/set-state-in-effect) — mismo
  // criterio que ya usa `proyeccion-view.tsx` para el resto del combo.
  const cargarDetallePorGrupo = (idGrupoElegido: string) => {
    setCargando(true);
    setError(null);
    setDetalle(null);
    detalleContadorProcesoApi
      .getDetallePorGrupo(Number(idGrupoElegido))
      .then(setDetalle)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "No se pudo cargar el cliente."),
      )
      .finally(() => setCargando(false));
  };

  const procesosVisibles = idGrupo == null ? [] : procesos;
  const idProcesoValido = procesosVisibles.some((p) => String(p.nro_proceso) === idProceso)
    ? idProceso
    : null;

  const clienteLabel = grupos.find((g) => String(g.id) === idGrupo)?.descripcion ?? detalle?.cliente ?? "";

  const filasDelCliente = useMemo(() => {
    if (!detalle) return [];
    if (!idProcesoValido) return detalle.filas;
    return detalle.filas.filter((f) => String(f.nro_proceso) === idProcesoValido);
  }, [detalle, idProcesoValido]);

  const filasVisibles = useMemo(() => {
    const filtradas =
      alcance === "todos" ? filasDelCliente : filasDelCliente.filter((f) => f.falta_contador);
    return [...filtradas].sort((a, b) =>
      compareSortValues(valorOrdenable(a, sort.key), valorOrdenable(b, sort.key), sort.direction),
    );
  }, [filasDelCliente, alcance, sort]);

  const faltantes = filasDelCliente.filter((f) => f.falta_contador).length;

  const handleCopiarWhatsapp = async () => {
    if (!detalle) return;
    const alcanceLabel = ALCANCES.find((a) => a.value === alcance)?.label ?? "";
    const texto = formatearTablaWhatsapp(filasVisibles, clienteLabel, alcanceLabel);
    try {
      await copiarTexto(texto);
      toast.success("Tabla copiada, lista para pegar en WhatsApp.");
    } catch {
      toast.error("No se pudo copiar. Probá de nuevo o copiá manualmente.");
    }
  };

  const handleCopiarMail = async () => {
    if (!detalle) return;
    const html = formatearTablaMailHtml(filasVisibles, clienteLabel);
    const texto = formatearTablaMailTexto(filasVisibles, clienteLabel);
    try {
      await copiarHtmlYTexto(html, texto);
      toast.success("Tabla copiada con formato, lista para pegar en un mail.");
    } catch {
      toast.error("No se pudo copiar. Probá de nuevo o copiá manualmente.");
    }
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">
          Centro de Contadores
        </Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Detalle por Proceso</span>
      </div>

      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Detalle de contadores por proceso
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Reconstrucción del reporte &ldquo;Detalle de contadores por nro de proceso&rdquo; — elegí
          un cliente para traer todo su parque, y si querés acotalo a un anexo puntual con el
          selector de Proceso.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-[260px]">
          <SearchableSelect
            label="Cliente (grupo económico)"
            placeholder="Buscar cliente…"
            options={grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
            value={idGrupo}
            onChange={(id) => {
              setIdGrupo(id);
              setIdProceso(null);
              if (id == null) {
                setDetalle(null);
              } else {
                cargarDetallePorGrupo(id);
              }
            }}
          />
        </div>
        <div className="w-[280px]">
          <SearchableSelect
            label="Proceso (opcional, filtra un anexo)"
            placeholder={idGrupo ? "Todos los anexos" : "Elegí primero un cliente"}
            disabled={!idGrupo}
            options={procesosVisibles.map((p) => ({
              id: String(p.nro_proceso),
              label: `${p.periodo_facturacion} · ${p.nombre_anexo}`,
              sublabel: `Proc. ${p.nro_proceso} · cierre ${p.periodo_hasta}`,
            }))}
            value={idProcesoValido}
            onChange={setIdProceso}
          />
        </div>
      </div>

      {error && (
        <p className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
          {error}
        </p>
      )}

      {detalle && (
        <>
          <KpiGrid className="sm:grid-cols-3">
            <KpiTile label="Cliente" value={clienteLabel} />
            <KpiTile label="Falta contador" value={String(faltantes)} tone="danger" />
            <KpiTile label="Total equipos" value={String(filasDelCliente.length)} />
          </KpiGrid>

          <div className="flex flex-wrap items-end justify-between gap-3">
            <SegmentedControl
              label="Alcance"
              options={ALCANCES.map((a) => ({
                value: a.value,
                label:
                  a.value === "todos"
                    ? `${a.label} (${filasDelCliente.length})`
                    : `${a.label} (${faltantes})`,
              }))}
              value={alcance}
              onChange={(v) => setAlcance(v as AlcanceReporte)}
            />
            <div className="flex items-end gap-2">
              <BrandButton
                variant="outline"
                onClick={() => void handleCopiarWhatsapp()}
                disabled={filasVisibles.length === 0}
                title="Copiar la tabla de abajo como texto para pegar en WhatsApp"
              >
                <Copy className="h-4 w-4" />
                Copiar para WhatsApp
              </BrandButton>
              <BrandButton
                variant="outline"
                onClick={() => void handleCopiarMail()}
                disabled={filasVisibles.length === 0}
                title="Copiar la tabla de abajo con el mismo formato del Excel, lista para pegar en un mail"
              >
                <Mail className="h-4 w-4" />
                Copiar para mail
              </BrandButton>
              {idProcesoValido ? (
                <a
                  href={detalleContadorProcesoApi.getXlsxUrl(Number(idProcesoValido), alcance)}
                  className={brandButtonClasses({ variant: "outline" })}
                  title="Descarga el mismo listado de abajo en un Excel, listo para mandarle al cliente"
                >
                  <Download className="h-4 w-4" />
                  Descargar XLSX
                </a>
              ) : (
                <span
                  className={cn(brandButtonClasses({ variant: "outline" }), "cursor-not-allowed opacity-60")}
                  title="Elegí un proceso puntual en el selector para descargar el Excel de ese anexo"
                >
                  <Download className="h-4 w-4" />
                  Descargar XLSX
                </span>
              )}
            </div>
          </div>

          <DetalleContadorTabla filas={filasVisibles} sort={sort} onToggleSort={toggleSort} />
        </>
      )}

      {!idGrupo && !cargando && (
        <p className="text-sm text-muted-foreground">
          Elegí un cliente para ver todo su parque de equipos.
        </p>
      )}

      {cargando && !detalle && (
        <p className="text-sm text-muted-foreground">Cargando el parque del cliente…</p>
      )}
    </div>
  );
}
