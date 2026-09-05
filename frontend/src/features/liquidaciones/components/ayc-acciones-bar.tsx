"use client";

import { type ReactNode, useState } from "react";
import { Check, Inbox } from "lucide-react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { EstadoLiquidacion, Liquidacion } from "../types/liquidaciones";

type Accion = "recibir" | "aprobar" | "observar" | "anular";

// Puerto del comportamiento real de Web Agentes (`LiquidationsController` +
// `View/Liquidations/view.ctp`, repo `Web-Agentes`): cada botón solo se
// dibuja si el estado actual lo permite (auditoría de liquidaciones, hallazgo
// "Botones de estado sin gating por estado actual") — mismas reglas que
// valida el backend en `transiciones_ayc.py`, doble check acá para que el
// botón directamente no aparezca. No reproduce la restricción fina por tipo
// de usuario del legacy (mesa de ayuda vs. gerente): esta app no modela esa
// distinción, ambos caen bajo el mismo permiso `liquidaciones.approve`.
const ORIGENES_VALIDOS: Record<"recibir" | "observar" | "aprobar", EstadoLiquidacion[]> = {
  recibir: ["preliquidada", "observada"],
  observar: ["recibida", "aprobada"],
  aprobar: ["recibida", "observada"],
};

function accionValidaDesdeEstado(accion: Accion, estado: EstadoLiquidacion): boolean {
  if (accion === "anular") return estado !== "cerrada";
  return ORIGENES_VALIDOS[accion].includes(estado);
}

const CONFIG: Record<
  Accion,
  {
    label: string;
    titulo: string;
    mensaje: (n: string) => string;
    btnLabel: string;
    btnCls: string;
    triggerCls: string;
    icon?: ReactNode;
  }
> = {
  recibir: {
    label: "Recibir",
    titulo: "Recibir en Canal Directo",
    mensaje: (n) =>
      `¿Marcar la liquidación ${n} como Recibida en Canal Directo? Es el paso previo a aprobarla u observarla.`,
    btnLabel: "Recibir",
    btnCls: "bg-brand-orange text-white hover:opacity-90",
    triggerCls: "border border-border text-foreground hover:bg-muted/50",
    icon: <Inbox size={13} />,
  },
  aprobar: {
    label: "Aprobar",
    titulo: "Aprobar en Canal Directo",
    mensaje: (n) =>
      `¿Aprobar la liquidación ${n} en Canal Directo? El estado local se actualizará a "Aprobada".`,
    btnLabel: "Aprobar",
    btnCls: "bg-brand-orange text-white hover:opacity-90",
    triggerCls:
      "border border-emerald-500/50 text-emerald-700 hover:bg-emerald-500/10 dark:text-emerald-400",
    icon: <Check size={13} />,
  },
  observar: {
    label: "Observar",
    titulo: "Observar en Canal Directo",
    mensaje: (n) =>
      `¿Marcar la liquidación ${n} como Observada en Canal Directo?`,
    btnLabel: "Confirmar",
    btnCls: "bg-amber-500 text-white hover:opacity-90",
    triggerCls:
      "border border-border text-foreground hover:bg-muted/50",
  },
  anular: {
    label: "Anular",
    titulo: "Anular en Canal Directo",
    mensaje: (n) =>
      `¿Anular la liquidación ${n} en Canal Directo y eliminarla del sistema? Esta acción no se puede deshacer.`,
    btnLabel: "Anular",
    btnCls: "bg-destructive text-white hover:opacity-90",
    triggerCls:
      "border border-border text-foreground hover:bg-muted/50",
  },
};

interface Props {
  liquidacion: Liquidacion;
  onActualizado: (updated: Liquidacion) => void;
  onAnulado: () => void;
}

export function AyCAccionesBar({ liquidacion, onActualizado, onAnulado }: Props) {
  const [accion, setAccion] = useState<Accion | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Espejo de liquidaciones_ayc_router.py: recibir/aprobar/observar = approve,
  // anular = delete; "eliminar solo localmente" es DELETE /{id} = update.
  const { can } = useSession();
  const acciones = (["recibir", "aprobar", "observar", "anular"] as Accion[]).filter(
    (a) =>
      (a === "anular" ? can("liquidaciones", "delete") : can("liquidaciones", "approve")) &&
      accionValidaDesdeEstado(a, liquidacion.estado),
  );
  const puedeBorrarLocal = can("liquidaciones", "update");

  if (!liquidacion.numeroLiquidacion || acciones.length === 0) return null;

  const cfg = accion ? CONFIG[accion] : null;

  const open = (a: Accion) => {
    setError(null);
    setAccion(a);
  };

  const handleConfirm = async () => {
    if (!accion) return;
    setLoading(true);
    setError(null);
    try {
      if (accion === "recibir") {
        const updated = await liquidacionesApi.recibir(liquidacion.id);
        onActualizado(updated);
        toast.success("Liquidación marcada como Recibida en Canal Directo");
        setAccion(null);
      } else if (accion === "aprobar") {
        const updated = await liquidacionesApi.aprobar(liquidacion.id);
        onActualizado(updated);
        toast.success("Liquidación aprobada en Canal Directo");
        setAccion(null);
      } else if (accion === "observar") {
        const updated = await liquidacionesApi.observar(liquidacion.id);
        onActualizado(updated);
        toast.success("Liquidación marcada como Observada en Canal Directo");
        setAccion(null);
      } else {
        await liquidacionesApi.anular(liquidacion.id);
        toast.success("Liquidación anulada");
        onAnulado();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar la acción");
    } finally {
      setLoading(false);
    }
  };

  const handleForceLocalDelete = async () => {
    setLoading(true);
    setError(null);
    try {
      await liquidacionesApi.delete(liquidacion.id, true);
      toast.success("Registro local eliminado");
      onAnulado();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al eliminar el registro local");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <span
          className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground"
          title="Liquidación con remito de Canal Directo — cada acción pega a wsAyC, no es solo un cambio local"
        >
          Canal Directo
        </span>
        {acciones.map((a) => (
          <button
            key={a}
            onClick={() => open(a)}
            className={`flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 font-body text-sm font-semibold transition-colors ${CONFIG[a].triggerCls}`}
          >
            {CONFIG[a].icon}
            {CONFIG[a].label}
          </button>
        ))}
      </div>

      {accion && cfg && (
        <BrandModal
          isOpen
          onClose={() => { if (!loading) setAccion(null); }}
          title={cfg.titulo}
          widthPx={420}
          error={error}
        >
          <p className="font-body text-sm text-muted-foreground leading-relaxed">
            {cfg.mensaje(liquidacion.numeroLiquidacion!)}
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            {accion === "anular" && error && puedeBorrarLocal && (
              <button
                onClick={() => void handleForceLocalDelete()}
                disabled={loading}
                className="font-body text-xs text-muted-foreground underline hover:text-foreground disabled:opacity-50"
              >
                Eliminar solo localmente
              </button>
            )}
            <div className="ml-auto flex gap-3">
              <button
                onClick={() => setAccion(null)}
                disabled={loading}
                className="font-body text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => void handleConfirm()}
                disabled={loading}
                className={`rounded-[8px] px-4 py-2 font-body text-sm font-semibold transition-opacity disabled:opacity-50 ${cfg.btnCls}`}
              >
                {loading ? "Procesando..." : cfg.btnLabel}
              </button>
            </div>
          </div>
        </BrandModal>
      )}
    </>
  );
}
