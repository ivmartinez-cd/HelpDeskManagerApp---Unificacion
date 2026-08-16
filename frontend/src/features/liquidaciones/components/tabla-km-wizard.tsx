"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  CalculoKmPreview, GeocodificarResultado, PrestadorLiquidacion, SucursalSiges,
} from "../types/liquidaciones";
import { PasoCalcular } from "./tabla-km-wizard-calcular";
import { PasoGeocodificar } from "./tabla-km-wizard-geocodificar";
import { PasoPines } from "./tabla-km-wizard-pines";

const PASOS = ["Importar", "Geocodificar", "Distancias", "Pines"] as const;
type Paso = 0 | 1 | 2 | 3;

function Indicador({ actual }: { actual: Paso }) {
  return (
    <div className="mb-6 flex items-center justify-center">
      {PASOS.map((nombre, i) => (
        <div key={nombre} className="flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full font-heading text-sm font-bold transition-colors",
              i < actual && "bg-brand-orange/20 text-brand-orange",
              i === actual && "bg-brand-orange text-white",
              i > actual && "border-2 border-border text-muted-foreground",
            )}>
              {i < actual ? "✓" : i + 1}
            </div>
            <span className={cn("font-body text-[10px] font-bold uppercase tracking-[.06em]",
              i === actual ? "text-brand-orange" : "text-muted-foreground"
            )}>{nombre}</span>
          </div>
          {i < PASOS.length - 1 && <div className={cn("mb-5 mx-3 h-[2px] w-12 flex-shrink-0 rounded-full transition-colors",
            i < actual ? "bg-brand-orange/40" : "bg-border")} />}
        </div>
      ))}
    </div>
  );
}

function PasoImportar({ prestadorId, onImportado }: {
  prestadorId: string; onImportado: () => void;
}) {
  const [cargando, setCargando] = useState(true);
  const [sucursales, setSucursales] = useState<SucursalSiges[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [importando, setImportando] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const [importado, setImportado] = useState(false);

  useEffect(() => {
    liquidacionesApi.buscarSucursalesSiges(prestadorId, "")
      .then(page => setSucursales(page.items))
      .catch(() => setError("No se pudieron cargar las sucursales desde Siges"))
      .finally(() => setCargando(false));
  }, [prestadorId]);

  const nuevas = sucursales.filter(s => !s.yaCargada);
  const yaCargadas = sucursales.filter(s => s.yaCargada);

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
      onImportado();
      setImportado(true);
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
        Sucursales de clientes asignadas a este PST en Siges. Las que ya están en tu Tabla KM
        se muestran como &quot;ya cargada&quot; — solo se importan las nuevas.
        Los km recorrido quedan en 0 para que los completes a mano.
      </p>
      <div className="flex flex-wrap gap-2">
        <Badge variant="info">{nuevas.length} nuevas</Badge>
        <Badge variant="neutral">{yaCargadas.length} ya cargadas</Badge>
      </div>
      {nuevas.length > 0 && !importado && (
        <div className="flex flex-col gap-3">
          <div className="max-h-[30vh] overflow-y-auto rounded-[8px] border border-border divide-y divide-border">
            {nuevas.map(s => (
              <div key={s.sigesSucursalId} className="px-3 py-2">
                <p className="font-body text-sm font-semibold text-foreground">
                  {s.empresaNombre} · {s.sucursalNombre}
                </p>
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
      {nuevas.length === 0 && (
        <p className="font-body text-sm text-muted-foreground italic">
          Todas las sucursales de este PST ya están en la Tabla KM. Podés pasar al siguiente paso.
        </p>
      )}
    </div>
  );
}

export function TablaKmWizard({
  prestador, onClose, onAplicado,
}: {
  prestador: PrestadorLiquidacion; onClose: () => void; onAplicado: () => void;
}) {
  const [paso, setPaso] = useState<Paso>(0);
  const [geoResumen, setGeoResumen] = useState<GeocodificarResultado | null>(null);
  const [preview, setPreview] = useState<CalculoKmPreview | null>(null);
  const ir = (n: number) => setPaso(Math.max(0, Math.min(3, n)) as Paso);

  return (
    <BrandModal isOpen onClose={onClose} title={`Configurar km — ${prestador.nombreCorto}`} widthPx={900}>
      <Indicador actual={paso} />
      <div className="min-h-[300px]">
        {paso === 0 && <PasoImportar prestadorId={prestador.id} onImportado={onAplicado} />}
        {paso === 1 && <PasoGeocodificar prestadorId={prestador.id} resumen={geoResumen} setResumen={setGeoResumen} />}
        {paso === 2 && <PasoCalcular prestador={prestador} preview={preview} setPreview={setPreview} onAplicado={onAplicado} />}
        {paso === 3 && <PasoPines prestadorId={prestador.id} />}
      </div>
      <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
        {paso < 3 ? (
          <button className="font-body text-sm text-muted-foreground hover:text-foreground" onClick={() => ir(paso + 1)}>
            Omitir este paso →
          </button>
        ) : <span />}
        <div className="flex gap-2">
          {paso > 0 && <BrandButton variant="outline" onClick={() => ir(paso - 1)}>← Anterior</BrandButton>}
          {paso < 3
            ? <BrandButton onClick={() => ir(paso + 1)}>Siguiente →</BrandButton>
            : <BrandButton onClick={onClose}>Finalizar</BrandButton>}
        </div>
      </div>
    </BrandModal>
  );
}
