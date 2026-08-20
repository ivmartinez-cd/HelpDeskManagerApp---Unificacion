"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { DatosAsistente } from "../hooks/use-asistente-km";
import {
  componerBandeja, filtrarBandeja, resumirBandeja,
  type FiltroBandeja, type ItemBandeja, type ResumenBandeja,
} from "../lib/asistente-km-bandeja";
import { ATRIBUCION_ODBL, plural } from "../lib/asistente-km-textos";
import { ItemNombreCandidato, ItemNombreSinCandidato } from "./tabla-km-wizard-bandeja-nombres";
import { ItemPinRoto, ItemPinesVerificar } from "./tabla-km-wizard-bandeja-pines";
import { ItemSinUbicacion, ItemUbicacionElegir, ItemUbicacionSinResultado } from "./tabla-km-wizard-bandeja-ubicaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";
import { VerDetalle } from "./tabla-km-wizard-ui";

const FILTROS: { value: FiltroBandeja; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "pines", label: "Pines rotos" },
  { value: "nombres", label: "Nombres" },
  { value: "ubicaciones", label: "Ubicaciones" },
];

function textoResumen(r: ResumenBandeja): string {
  const partes: string[] = [];
  if (r.pinesRotos > 0) partes.push(`${plural(r.pinesRotos, "pin roto", "pines rotos")} (${r.paraGestion} van al CSV para Gestión)`);
  if (r.nombres > 0) partes.push(`${plural(r.nombres, "nombre", "nombres")} por confirmar`);
  const ubic = r.ubicaciones + r.sinUbicacion;
  if (ubic > 0) partes.push(`${plural(ubic, "ubicación", "ubicaciones")} por resolver`);
  if (r.pinesPorVerificar > 0) partes.push(`${r.pinesPorVerificar} pines a verificar`);
  return partes.length ? `Quedan ${partes.join(", ")}.` : "No hay nada pendiente.";
}

function Item({ item, prestadorId, tope, onCambio }: { item: ItemBandeja; prestadorId: string; tope: number; onCambio: () => Promise<void> }) {
  switch (item.tipo) {
    case "pin_roto": return <ItemPinRoto pin={item} prestadorId={prestadorId} onCambio={onCambio} />;
    case "pines_verificar": return <ItemPinesVerificar item={item} prestadorId={prestadorId} tope={tope} onCambio={onCambio} />;
    case "nombre_candidato": return <ItemNombreCandidato item={item} onCambio={onCambio} />;
    case "nombre_sin_candidato": return <ItemNombreSinCandidato item={item} />;
    case "sin_ubicacion": return <ItemSinUbicacion item={item} prestadorId={prestadorId} tope={tope} onCambio={onCambio} />;
    case "ubicacion_elegir": return <ItemUbicacionElegir item={item} prestadorId={prestadorId} onCambio={onCambio} />;
    case "ubicacion_sin_resultado": return <ItemUbicacionSinResultado item={item} prestadorId={prestadorId} onCambio={onCambio} />;
  }
}

/** Siges es read-only: el CSV para Gestión es el cierre real del flujo. */
export function BotonExportarCsv({ prestadorId }: { prestadorId: string }) {
  const [exportando, setExportando] = useState(false);
  const exportar = async () => {
    setExportando(true);
    try { await liquidacionesApi.exportWorklistCsv(prestadorId); }
    catch (e: unknown) { toast.error(e instanceof Error ? e.message : "No se pudo exportar el CSV"); }
    finally { setExportando(false); }
  };
  return <BrandButton size="sm" variant="outline" loading={exportando} onClick={exportar}>Exportar CSV para Gestión</BrandButton>;
}

/** Cierre del Momento 2: CSV para Gestión (parte del flujo, no un extra) y, como
 * secundario, la auditoría completa con Google (decisión 0.4.c). */
export function CierreBandeja({ prestadorId, resumen, estimacionAuditarPines, tope, onCambio }: {
  prestadorId: string; resumen: ResumenBandeja; estimacionAuditarPines: number; tope: number; onCambio: () => Promise<void>;
}) {
  const [auditando, setAuditando] = useState(false);
  const auditarTodo = async () => {
    setAuditando(true);
    try { await liquidacionesApi.auditarPines(prestadorId); await onCambio(); }
    catch (e: unknown) { toast.error(e instanceof Error ? e.message : "No se pudo verificar con Google"); }
    finally { setAuditando(false); }
  };
  return (
    <div className="flex flex-col gap-2 border-t border-border pt-3">
      <div className="flex flex-wrap items-center gap-3">
        <p className="font-body text-sm text-foreground">
          Para corregir en Gestión: <strong>{plural(resumen.paraGestion, "sucursal", "sucursales")}</strong>
        </p>
        <BotonExportarCsv prestadorId={prestadorId} />
      </div>
      <VerDetalle etiqueta="Más chequeos">
        <p className="mb-2">Compara el pin de Gestión de <strong>todas</strong> las sucursales del prestador con su dirección escrita. Rara vez hace falta: lo gratis ya cubrió la mayoría.</p>
        <BotonConsumoGoogle size="sm" variant="outline" estimacion={estimacionAuditarPines} tope={tope} loading={auditando} onEjecutar={auditarTodo}>
          Verificar todos los pines con Google
        </BotonConsumoGoogle>
      </VerDetalle>
    </div>
  );
}

/** Momento 2: la bandeja única de pendientes. */
export function MomentoRevisar({ prestadorId, datos, pendientesPorTope, onCambio, onSeguirChequeando }: {
  prestadorId: string;
  datos: DatosAsistente;
  pendientesPorTope: number;
  onCambio: () => Promise<void>;
  onSeguirChequeando: () => Promise<void>;
}) {
  const [filtro, setFiltro] = useState<FiltroBandeja>("todos");
  const [chequeando, setChequeando] = useState(false);
  const items = useMemo(() => componerBandeja(datos.bandeja), [datos.bandeja]);
  const resumen = useMemo(() => resumirBandeja(items), [items]);
  const visibles = filtrarBandeja(items, filtro);
  const tope = datos.estado.topePorCorrida;

  const seguir = async () => {
    setChequeando(true);
    try { await onSeguirChequeando(); } finally { setChequeando(false); }
  };

  return (
    <div className="flex flex-col gap-3">
      <p className="font-body text-sm text-foreground">{textoResumen(resumen)}</p>
      {pendientesPorTope > 0 && (
        <div className="flex items-center gap-3">
          <p className="font-body text-xs text-muted-foreground">Quedan {pendientesPorTope} pines por chequear (sin costo).</p>
          <BrandButton size="sm" variant="outline" loading={chequeando} onClick={seguir}>Seguir chequeando</BrandButton>
        </div>
      )}
      {items.length > 0 && (
        <SegmentedControl size="sm" label="Filtrar pendientes" options={FILTROS} value={filtro} onChange={(v) => setFiltro(v as FiltroBandeja)} />
      )}
      {visibles.length > 0 ? (
        <ul className="flex max-h-[48vh] flex-col gap-2 overflow-y-auto pr-1">
          {visibles.map((item) => <Item key={item.key} item={item} prestadorId={prestadorId} tope={tope} onCambio={onCambio} />)}
        </ul>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          {items.length === 0 ? "✓ No hay nada pendiente. Podés pasar a calcular km." : "Nada pendiente en este filtro."}
        </p>
      )}
      {resumen.muestraOsm && <p className="font-body text-[10px] text-muted-foreground">{ATRIBUCION_ODBL}</p>}
      <CierreBandeja prestadorId={prestadorId} resumen={resumen} estimacionAuditarPines={datos.estado.estimacionAuditarPines} tope={tope} onCambio={onCambio} />
    </div>
  );
}
