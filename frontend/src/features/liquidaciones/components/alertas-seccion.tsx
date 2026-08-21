"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { elegiblesParaEstadoMasivo } from "../lib/alertas-masivo";
import type { Alerta, EstadoAlerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { AlertaRow } from "./alertas-fila";
import { AlertasBulkToolbar } from "./alertas-bulk-toolbar";
import { DescartarModal } from "./alertas-descartar-modal";
import { EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";

function plantillaDesdeAlerta(alerta: Alerta): PlantillaEntrada {
  const ctx = alerta.datosContexto as { empresa?: string; sucursal?: string } | null;
  return {
    empresaNombre: ctx?.empresa ?? "",
    sucursalNombre: ctx?.sucursal ?? "",
    domicilioCliente: "",
    localidadCliente: "",
    provinciaCliente: "",
  };
}

const FILTROS: { valor: EstadoAlerta | "todas"; label: string }[] = [
  { valor: "todas", label: "Todas" },
  { valor: "pendiente", label: "Pendientes" },
  { valor: "en_revision", label: "En revisión" },
  { valor: "resuelta", label: "Resueltas" },
  { valor: "descartada", label: "Descartadas" },
];

export function AlertasSeccion({ liquidacionId, prestadorId, prestadores, alertas, incidentes, onChanged }: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  alertas: Alerta[];
  incidentes: Incidente[];
  onChanged: () => void;
}) {
  const [filtro, setFiltro] = useState<EstadoAlerta | "todas">("todas");
  const [descartando, setDescartando] = useState<Alerta[] | null>(null);
  const [resolviendoAlt009, setResolviendoAlt009] = useState<Alerta | null>(null);
  const [seleccionadas, setSeleccionadas] = useState<Set<string>>(new Set());
  const [aplicandoMasivo, setAplicandoMasivo] = useState(false);

  const resolverAlt009 = async (alerta: Alerta) => {
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, { estado: "resuelta" });
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al marcar la alerta como resuelta");
    } finally {
      setResolviendoAlt009(null);
    }
  };
  const numeroPorIncidente = useMemo(
    () => new Map(incidentes.map((i) => [i.id, i.numeroIncidente])),
    [incidentes],
  );
  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

  if (alertas.length === 0) return null;
  const visibles = filtro === "todas" ? alertas : alertas.filter((a) => a.estado === filtro);

  const alertasSeleccionadas = alertas.filter((a) => seleccionadas.has(a.id));
  const elegiblesRevisar = elegiblesParaEstadoMasivo(alertasSeleccionadas, "en_revision");
  const elegiblesResolver = elegiblesParaEstadoMasivo(alertasSeleccionadas, "resuelta");
  const elegiblesDescartar = elegiblesParaEstadoMasivo(alertasSeleccionadas, "descartada");
  const todasVisiblesSeleccionadas = visibles.length > 0 && visibles.every((a) => seleccionadas.has(a.id));

  function toggleSeleccion(id: string) {
    setSeleccionadas((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleTodasVisibles() {
    setSeleccionadas((prev) => {
      const next = new Set(prev);
      if (todasVisiblesSeleccionadas) visibles.forEach((a) => next.delete(a.id));
      else visibles.forEach((a) => next.add(a.id));
      return next;
    });
  }

  async function aplicarMasivo(estado: "en_revision" | "resuelta", elegibles: Alerta[]) {
    setAplicandoMasivo(true);
    try {
      const resultados = await Promise.allSettled(
        elegibles.map((a) => liquidacionesApi.updateEstadoAlerta(liquidacionId, a.id, { estado })),
      );
      const fallidas = resultados.filter((r) => r.status === "rejected").length;
      if (fallidas > 0) {
        toast.error(`No se pudieron actualizar ${fallidas} de ${elegibles.length} alertas`);
      }
      onChanged();
      setSeleccionadas(new Set());
    } finally {
      setAplicandoMasivo(false);
    }
  }

  return (
    <div id="alertas" className="flex flex-col gap-3 scroll-mt-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-base font-bold text-foreground">
          Alertas
          <span className="ml-2 font-body text-sm font-normal text-muted-foreground">
            {alertas.length.toLocaleString("es-AR")}
          </span>
        </h2>
        <div className="flex gap-1">
          {FILTROS.map((f) => (
            <button
              key={f.valor}
              onClick={() => setFiltro(f.valor)}
              className={`rounded-[8px] px-2.5 py-1 font-body text-xs font-semibold ${
                filtro === f.valor
                  ? "bg-brand-orange text-white"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <AlertasBulkToolbar
        seleccionadas={seleccionadas.size}
        elegiblesRevisar={elegiblesRevisar.length}
        elegiblesResolver={elegiblesResolver.length}
        elegiblesDescartar={elegiblesDescartar.length}
        aplicando={aplicandoMasivo}
        onRevisar={() => void aplicarMasivo("en_revision", elegiblesRevisar)}
        onResolver={() => void aplicarMasivo("resuelta", elegiblesResolver)}
        onDescartar={() => setDescartando(elegiblesDescartar)}
        onLimpiar={() => setSeleccionadas(new Set())}
      />
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/40">
                <th className="py-3 px-4">
                  <input
                    type="checkbox"
                    checked={todasVisiblesSeleccionadas}
                    ref={(el) => {
                      if (el) {
                        el.indeterminate = !todasVisiblesSeleccionadas && visibles.some((a) => seleccionadas.has(a.id));
                      }
                    }}
                    onChange={toggleTodasVisibles}
                    aria-label="Seleccionar todas las alertas visibles"
                    className="cursor-pointer accent-brand-orange"
                    disabled={visibles.length === 0}
                  />
                </th>
                <th className={thCls}>Tipo</th>
                <th className={thCls}>Incidente</th>
                <th className={thCls}>Descripción</th>
                <th className={`${thCls} text-right`}>Riesgo</th>
                <th className={thCls}>Estado</th>
                <th className={`${thCls} text-right`}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((a) => (
                <AlertaRow
                  key={a.id}
                  liquidacionId={liquidacionId}
                  alerta={a}
                  numeroIncidente={numeroPorIncidente.get(a.incidenteId) ?? null}
                  isSelected={seleccionadas.has(a.id)}
                  onToggleSelect={toggleSeleccion}
                  onChanged={onChanged}
                  onDescartar={(alerta) => setDescartando([alerta])}
                  onResolverAlt009={setResolviendoAlt009}
                />
              ))}
            </tbody>
          </table>
          {visibles.length === 0 && (
            <p className="p-4 font-body text-sm text-muted-foreground italic">
              No hay alertas con este estado.
            </p>
          )}
        </div>
      </div>
      {descartando && (
        <DescartarModal
          liquidacionId={liquidacionId}
          alertas={descartando}
          onClose={() => setDescartando(null)}
          onChanged={onChanged}
        />
      )}
      {resolviendoAlt009 && (
        <EntradaModal
          key={`alt009:${resolviendoAlt009.id}`}
          isOpen
          onClose={() => setResolviendoAlt009(null)}
          prestadores={prestadores}
          editing={null}
          defaultPrestadorId={prestadorId}
          plantilla={plantillaDesdeAlerta(resolviendoAlt009)}
          title="Cargar sucursal en Tabla KM"
          onSuccess={() => void resolverAlt009(resolviendoAlt009)}
        />
      )}
    </div>
  );
}
