"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  AuditarPinesResult, EstadoAsistenteKm, HallazgoTier0, PinSospechoso,
} from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";

function Tarjeta({ numero, titulo, descripcion, badge, children }: {
  numero: string; titulo: string; descripcion: string;
  badge?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="rounded-[8px] border border-border p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-body text-sm font-semibold text-foreground">
            <span className="text-brand-orange">{numero}</span> · {titulo}
          </p>
          <p className="font-body text-xs text-muted-foreground">{descripcion}</p>
        </div>
        {badge}
      </div>
      {children}
    </div>
  );
}

const BADGE_SEVERIDAD: Record<HallazgoTier0["severidad"], BadgeVariant> = {
  alta: "danger",
  media: "warning",
  baja: "neutral",
};

function HallazgoTier0Item({ hallazgo }: { hallazgo: HallazgoTier0 }) {
  const tieneCoords = hallazgo.latitud !== null && hallazgo.longitud !== null;
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">
          {hallazgo.empresaNombre} — {hallazgo.sucursalNombre}
        </p>
        <Badge variant={BADGE_SEVERIDAD[hallazgo.severidad]}>{hallazgo.severidad}</Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">{hallazgo.detalle}</p>
      {tieneCoords && (
        <a
          href={`https://www.google.com/maps?q=${hallazgo.latitud},${hallazgo.longitud}`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1 inline-block font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
        >
          Ver pin en Maps
        </a>
      )}
    </div>
  );
}

function SeccionTier0({ prestadorId }: { prestadorId: string }) {
  const [hallazgos, setHallazgos] = useState<HallazgoTier0[] | null>(null);

  useEffect(() => {
    liquidacionesApi.listGeovalidacionTier0(prestadorId).then(setHallazgos).catch(() => setHallazgos([]));
  }, [prestadorId]);

  return (
    <Tarjeta
      numero="1"
      titulo="Geovalidación básica (Tier 0)"
      descripcion="Coordenadas ausentes, fuera de Argentina, invertidas, pines compartidos entre sucursales distintas y muy lejos de la base. No consulta ningún servicio externo."
      badge={<Badge variant="success">no usa Google</Badge>}
    >
      {hallazgos === null ? (
        <div className="flex h-16 items-center justify-center"><Spinner /></div>
      ) : hallazgos.length > 0 ? (
        <div className="flex max-h-[32vh] flex-col gap-2 overflow-y-auto pr-1">
          {hallazgos.map((h) => (
            <HallazgoTier0Item key={`${h.sigesSucursalId}-${h.codigo}`} hallazgo={h} />
          ))}
        </div>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          ✓ Ningún problema geométrico detectado.
        </p>
      )}
    </Tarjeta>
  );
}

function PinSospechosoItem({ pin, prestadorId, onCorregido }: {
  pin: PinSospechoso; prestadorId: string; onCorregido: () => void;
}) {
  const [corrigiendo, setCorrigiendo] = useState(false);
  const corregir = async () => {
    setCorrigiendo(true);
    try {
      await liquidacionesApi.corregirPin(prestadorId, pin.sigesSucursalId);
      toast.success(`${pin.empresaNombre}: pin corregido`);
      onCorregido();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al corregir pin");
    } finally { setCorrigiendo(false); }
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">{pin.empresaNombre} — {pin.sucursalNombre}</p>
        <Badge variant={pin.locationType === "ROOFTOP" ? "danger" : "warning"}>
          {pin.discrepanciaKm.toFixed(1)} km de diferencia
        </Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">{pin.direccion}</p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex gap-3 font-body text-[11px] font-bold uppercase tracking-wide">
          <a href={`https://www.google.com/maps?q=${pin.latitudSiges},${pin.longitudSiges}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Ver pin de Gestión</a>
          <a href={`https://www.google.com/maps?q=${pin.latitudGeocode},${pin.longitudGeocode}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Ver dirección escrita</a>
        </div>
        <BrandButton type="button" size="sm" variant="outline" loading={corrigiendo} onClick={corregir}>
          Usar la dirección escrita
        </BrandButton>
      </div>
    </div>
  );
}

/** Paso Pines. El listado es cache-first (sin Google); la verificación con
 * Google solo corre tras confirmar el costo. Corregir no consulta nada. */
export function PasoPines({ prestadorId, estado, onCambio }: {
  prestadorId: string; estado: EstadoAsistenteKm; onCambio: () => void;
}) {
  const [pines, setPines] = useState<PinSospechoso[] | null>(null);
  const [auditando, setAuditando] = useState(false);
  const [resultado, setResultado] = useState<AuditarPinesResult | null>(null);
  const [key, setKey] = useState(0);

  useEffect(() => {
    liquidacionesApi.listPinesSospechosos(prestadorId).then(setPines).catch(() => setPines([]));
  }, [prestadorId, key]);

  const auditar = async () => {
    setAuditando(true);
    try {
      setResultado(await liquidacionesApi.auditarPines(prestadorId));
      setKey(k => k + 1);
      onCambio();
    } finally { setAuditando(false); }
  };

  return (
    <div className="flex flex-col gap-4">
      <SeccionTier0 prestadorId={prestadorId} />

      <Tarjeta
        numero="2"
        titulo="Pines vs. dirección escrita (Google)"
        descripcion="Compara el pin del mapa de Gestión contra la dirección escrita de cada sucursal. Si difieren en más de 5 km, el pin probablemente esté mal puesto — conviene usar la dirección escrita. Opcional; corregir no consulta Google."
      >
        {!pines ? (
          <div className="flex h-20 items-center justify-center"><Spinner /></div>
        ) : pines.length > 0 ? (
          <div className="flex max-h-[32vh] flex-col gap-2 overflow-y-auto pr-1">
            {pines.map((p) => (
              <PinSospechosoItem
                key={p.sigesSucursalId}
                pin={p}
                prestadorId={prestadorId}
                onCorregido={() => { setKey(k => k + 1); onCambio(); }}
              />
            ))}
          </div>
        ) : resultado ? (
          <p className="font-body text-sm text-muted-foreground italic">
            ✓ Ningún pin difiere más de 5 km de su dirección. Podés finalizar.
          </p>
        ) : (
          <p className="font-body text-sm text-muted-foreground italic">
            Todavía no hay pines dudosos detectados. &quot;Verificar pines&quot; compara
            cada pin contra su dirección — no modifica nada, solo detecta.
          </p>
        )}
        <BotonConsumoGoogle
          variant="outline"
          size="sm"
          estimacion={estado.estimacionAuditarPines}
          tope={estado.topePorCorrida}
          loading={auditando}
          onEjecutar={auditar}
        >
          Verificar pines
        </BotonConsumoGoogle>
      </Tarjeta>
    </div>
  );
}
