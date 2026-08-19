"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { ESTADO_ALERTA_STYLES, TRANSICIONES_ALERTA } from "../lib/alerta-estados";
import type { Alerta, EstadoAlerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";

const CODIGO_ALT009 = "ALT009";

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

function riesgoClass(riesgo: number) {
  if (riesgo > 0.7) return "text-destructive";
  if (riesgo > 0.3) return "text-warning";
  return "text-success";
}

function AlertaRow({ liquidacionId, alerta, numeroIncidente, onChanged, onDescartar, onResolverAlt009 }: {
  liquidacionId: string;
  alerta: Alerta;
  numeroIncidente: string | null;
  onChanged: () => void;
  onDescartar: (alerta: Alerta) => void;
  onResolverAlt009: (alerta: Alerta) => void;
}) {
  const [updating, setUpdating] = useState(false);
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;

  const cambiar = async (estado: EstadoAlerta) => {
    setUpdating(true);
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, { estado });
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar el estado");
    } finally {
      setUpdating(false);
    }
  };

  return (
    <tr className="border-t border-border">
      <td className={tdCls}>
        <span className="font-semibold">{alerta.tipoAlerta}</span>
      </td>
      <td className={`${tdCls} text-muted-foreground`}>{numeroIncidente ?? "—"}</td>
      <td className={tdCls}>
        <div className="max-w-[420px]">{alerta.descripcion ?? "—"}</div>
        {alerta.justificacion && (
          <div className="mt-0.5 text-xs text-muted-foreground">
            Motivo: {alerta.justificacion}
          </div>
        )}
      </td>
      <td className={`${tdCls} text-right tabular-nums ${riesgoClass(alerta.riesgo)}`}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={tdCls}>
        <Badge variant={estilo.variant}>{estilo.label}</Badge>
      </td>
      <td className={`${tdCls} text-right whitespace-nowrap`}>
        {(TRANSICIONES_ALERTA[alerta.estado] ?? []).map((t) => (
          <button
            key={t.estado}
            disabled={updating}
            onClick={() => {
              // Para ALT009 tanto "Revisar" como "Resolver" llevan al mismo lugar: no
              // hay nada que revisar sin antes cargar la sucursal faltante en Tabla KM.
              const abreCargaSucursal =
                alerta.tipoAlerta === CODIGO_ALT009 &&
                !t.pideJustificacion &&
                (alerta.estado === "pendiente" || alerta.estado === "en_revision");
              if (abreCargaSucursal) onResolverAlt009(alerta);
              else if (t.pideJustificacion) onDescartar(alerta);
              else void cambiar(t.estado);
            }}
            className="ml-3 font-body text-xs text-brand-orange hover:underline disabled:opacity-50"
          >
            {t.label}
          </button>
        ))}
      </td>
    </tr>
  );
}

function DescartarModal({ liquidacionId, alerta, onClose, onChanged }: {
  liquidacionId: string;
  alerta: Alerta;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [justificacion, setJustificacion] = useState("");
  const [enviando, setEnviando] = useState(false);

  const descartar = async () => {
    setEnviando(true);
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, {
        estado: "descartada",
        justificacion: justificacion.trim(),
      });
      onChanged();
      onClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al descartar");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title={`Descartar ${alerta.tipoAlerta}`} widthPx={460}>
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          La alerta queda descartada y NO va a volver a aparecer aunque se re-analice
          la liquidación. Dejá escrito el motivo — queda guardado con la alerta.
        </p>
        <textarea
          value={justificacion}
          onChange={(e) => setJustificacion(e.target.value)}
          rows={3}
          placeholder="Ej.: diferencia acordada con el prestador"
          className="w-full rounded-[8px] border border-border bg-background p-3 font-body text-sm text-foreground outline-none focus:border-brand-orange"
        />
        <div className="flex justify-end gap-2">
          <BrandButton variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton
            loading={enviando}
            disabled={!justificacion.trim()}
            onClick={() => void descartar()}
          >
            Descartar alerta
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}

export function AlertasSeccion({ liquidacionId, prestadorId, prestadores, alertas, incidentes, onChanged }: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  alertas: Alerta[];
  incidentes: Incidente[];
  onChanged: () => void;
}) {
  const [filtro, setFiltro] = useState<EstadoAlerta | "todas">("todas");
  const [descartando, setDescartando] = useState<Alerta | null>(null);
  const [resolviendoAlt009, setResolviendoAlt009] = useState<Alerta | null>(null);

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
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/40">
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
                  onChanged={onChanged}
                  onDescartar={setDescartando}
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
          alerta={descartando}
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
