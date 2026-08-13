"use client";

import { useCallback, useEffect, useState } from "react";
import { BarChart3, RefreshCw, Settings2, TrafficCone } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { configApi } from "../api/config-api";
import { gestionApi } from "../api/gestion-api";
import type {
  Cargo,
  ConfigVacaciones,
  EmpleadoListItem,
  Exclusion,
} from "../types/vacaciones";
import { ConfigAntiguedadTab } from "./config-antiguedad-tab";
import { ConfigCiclosTab } from "./config-ciclos-tab";
import { ConfigReglasTab } from "./config-reglas-tab";
import { ConfigSolapamientosTab } from "./config-solapamientos-tab";

type Tab = "antiguedad" | "reglas" | "ciclos" | "solapamientos";

const TABS = [
  { value: "antiguedad", label: "Antigüedad y Días", icon: BarChart3 },
  { value: "reglas", label: "Reglas de Solicitud", icon: Settings2 },
  { value: "ciclos", label: "Ciclos Anuales", icon: RefreshCw },
  { value: "solapamientos", label: "Solapamientos", icon: TrafficCone },
] as const;

export function ConfiguracionView() {
  const [tab, setTab] = useState<Tab>("antiguedad");
  const [config, setConfig] = useState<ConfigVacaciones | null>(null);
  const [exclusiones, setExclusiones] = useState<Exclusion[]>([]);
  const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([]);
  const [cargos, setCargos] = useState<Cargo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);

  const load = useCallback(() => {
    return Promise.all([
      configApi.getConfig(),
      configApi.listExclusiones(),
      gestionApi.listEmpleados(),
      gestionApi.listCargos(),
    ])
      .then(([cfg, excl, emps, cars]) => {
        setConfig(cfg);
        setExclusiones(excl);
        setEmpleados(emps.filter((e) => e.status === "ACTIVE"));
        setCargos(cars);
        setError(null);
        setDirty(false);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar Configuración:", err);
        setError("No se pudo cargar la configuración. Intentá de nuevo.");
      });
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const actualizar = (patch: Partial<ConfigVacaciones>) => {
    setConfig((c) => (c ? { ...c, ...patch } : c));
    setDirty(true);
    setMensaje(null);
  };

  const guardar = () => {
    if (!config) return;
    if (config.seniorityTiers.length === 0) {
      setMensaje("Tiene que quedar al menos un rango de antigüedad.");
      return;
    }
    setGuardando(true);
    setMensaje(null);
    configApi
      .updateConfig(config)
      .then((cfg) => {
        setConfig(cfg);
        setDirty(false);
        setMensaje("Configuración guardada.");
      })
      .catch((err: unknown) => {
        setMensaje(
          err instanceof ApiError ? err.message : "No se pudo guardar la configuración.",
        );
      })
      .finally(() => setGuardando(false));
  };

  const recargarSolapamientos = () => {
    Promise.all([configApi.listExclusiones(), gestionApi.listCargos()])
      .then(([excl, cars]) => {
        setExclusiones(excl);
        setCargos(cars);
      })
      .catch((err: unknown) => {
        console.error("Error al recargar solapamientos:", err);
      });
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Configuración
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Reglas de vacaciones · Solo admin
          </p>
        </div>
        <div className="flex items-center gap-3">
          {mensaje && (
            <p className="font-body text-xs text-muted-foreground">{mensaje}</p>
          )}
          <BrandButton onClick={guardar} loading={guardando} disabled={!dirty || !config}>
            Guardar cambios
          </BrandButton>
        </div>
      </div>

      <div className="flex w-fit flex-wrap gap-1 rounded-[10px] border border-border bg-card p-1">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTab(t.value)}
            className={
              tab === t.value
                ? "flex items-center gap-1.5 rounded-[7px] bg-brand-orange px-4 py-2 font-body text-[13px] font-semibold text-white"
                : "flex items-center gap-1.5 rounded-[7px] px-4 py-2 font-body text-[13px] font-semibold text-muted-foreground hover:text-foreground"
            }
          >
            <t.icon className="h-3.5 w-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {!config && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }, (_, i) => (
            <BrandSkeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      )}

      {config && !error && (
        <>
          {tab === "antiguedad" && (
            <ConfigAntiguedadTab config={config} onChange={actualizar} />
          )}
          {tab === "reglas" && <ConfigReglasTab config={config} onChange={actualizar} />}
          {tab === "ciclos" && <ConfigCiclosTab config={config} onChange={actualizar} />}
          {tab === "solapamientos" && (
            <ConfigSolapamientosTab
              exclusiones={exclusiones}
              empleados={empleados}
              cargos={cargos}
              onChanged={recargarSolapamientos}
            />
          )}
        </>
      )}
    </div>
  );
}
