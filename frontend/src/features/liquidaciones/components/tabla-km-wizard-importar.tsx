"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { SucursalSiges } from "../types/liquidaciones";

/** Paso Importar: trae las sucursales del PST desde Siges y crea las filas
 * nuevas en la Tabla KM (km en 0, se completan en el paso Distancias).
 * No usa Google. */
export function PasoImportar({ prestadorId, onCambio }: {
  prestadorId: string;
  /** Avisar al contenedor que el estado del diagnóstico cambió. */
  onCambio: () => void;
}) {
  const [cargando, setCargando] = useState(true);
  const [sucursales, setSucursales] = useState<SucursalSiges[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [importando, setImportando] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const [importado, setImportado] = useState(false);
  const [verExClientes, setVerExClientes] = useState(false);

  useEffect(() => {
    liquidacionesApi.buscarSucursalesSiges(prestadorId, "")
      .then(page => setSucursales(page.items))
      .catch(() => setError("No se pudieron cargar las sucursales desde Siges"))
      .finally(() => setCargando(false));
  }, [prestadorId]);

  const todasNuevas = sucursales.filter(s => !s.yaCargada);
  const yaCargadas = sucursales.filter(s => s.yaCargada);
  const nuevasActivas = todasNuevas.filter(s => s.actividadReciente);
  const nuevasExClientes = todasNuevas.filter(s => !s.actividadReciente);
  const nuevas = verExClientes ? todasNuevas : nuevasActivas;

  const importar = async () => {
    setImportando(true);
    setProgreso(0);
    try {
      for (const s of nuevas) {
        await liquidacionesApi.createTablaKm({
          prestadorId,
          empresaNombre: s.empresaNombre,
          sucursalNombre: s.sucursalNombre,
          domicilioCliente: s.domicilio ?? undefined,
          localidadCliente: s.localidad ?? undefined,
          provinciaCliente: s.provincia ?? undefined,
          kmsRecorrido: 0,
          umbralViatico: 30,
          aplicaViatico: false,
        });
        setProgreso(p => p + 1);
      }
      setImportado(true);
      onCambio();
      toast.success(`${nuevas.length} sucursales importadas`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al importar");
    } finally {
      setImportando(false);
    }
  };

  if (cargando) return <div className="flex h-40 items-center justify-center"><Spinner /></div>;
  if (error) return <p className="font-body text-sm text-destructive">{error}</p>;

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Estas son las sucursales de clientes que este prestador atiende según Gestión.
        Al importarlas se crean en tu Tabla KM con km en 0 — el km se calcula después,
        en el paso Distancias. Este paso no consulta Google.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="info">{nuevasActivas.length} nuevas activas</Badge>
        {nuevasExClientes.length > 0 && (
          <Badge variant="neutral">{nuevasExClientes.length} ex-clientes</Badge>
        )}
        <Badge variant="neutral">{yaCargadas.length} ya cargadas</Badge>
        {nuevasExClientes.length > 0 && (
          <button
            className="font-body text-xs text-muted-foreground underline-offset-2 hover:underline"
            onClick={() => setVerExClientes(v => !v)}
          >
            {verExClientes ? "Ocultar ex-clientes" : "Mostrar también ex-clientes (sin liquidaciones en 24 meses)"}
          </button>
        )}
      </div>
      {nuevas.length > 0 && !importado && (
        <div className="flex flex-col gap-3">
          <div className="max-h-[30vh] overflow-y-auto rounded-[8px] border border-border divide-y divide-border">
            {nuevas.map(s => (
              <div key={s.sigesSucursalId} className={cn("px-3 py-2", !s.actividadReciente && "opacity-60")}>
                <div className="flex items-center gap-2">
                  <p className="font-body text-sm font-semibold text-foreground">
                    {s.empresaNombre} · {s.sucursalNombre}
                  </p>
                  {!s.actividadReciente && (
                    <Badge variant="neutral">sin actividad</Badge>
                  )}
                </div>
                <p className="font-body text-xs text-muted-foreground">
                  {[s.domicilio, s.localidad, s.provincia].filter(Boolean).join(" · ") || "Sin domicilio en Siges"}
                </p>
              </div>
            ))}
          </div>
          <BrandButton loading={importando} disabled={importando} onClick={importar} className="self-start">
            {importando
              ? `Importando ${progreso}/${nuevas.length}…`
              : `Importar ${nuevas.length} sucursal${nuevas.length !== 1 ? "es" : ""} nueva${nuevas.length !== 1 ? "s" : ""}`}
          </BrandButton>
        </div>
      )}
      {importado && (
        <p className="font-body text-sm font-semibold text-brand-orange">
          ✓ {nuevas.length} sucursales importadas. Podés continuar al siguiente paso.
        </p>
      )}
      {nuevas.length === 0 && !importado && (
        <p className="font-body text-sm text-muted-foreground italic">
          {todasNuevas.length === 0
            ? "Todas las sucursales de este prestador ya están en la Tabla KM. Podés pasar al siguiente paso."
            : "No hay clientes activos nuevos para importar. Usá \"Mostrar también ex-clientes\" si querés importar clientes sin actividad reciente."}
        </p>
      )}
    </div>
  );
}
