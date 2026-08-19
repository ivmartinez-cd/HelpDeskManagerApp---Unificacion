"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  AuditarPinesResult, EstadoAsistenteKm, HallazgoTier0, HallazgoTier1, HallazgoTier1b,
  PinSospechoso, ResultadoConsultarGeoref, ResultadoConsultarNominatim,
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

function HallazgoTier1Item({ hallazgo }: { hallazgo: HallazgoTier1 }) {
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">
          {hallazgo.empresaNombre} — {hallazgo.sucursalNombre}
        </p>
        <Badge variant="danger">provincia distinta</Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">
        Declarada en Gestión: <strong>{hallazgo.provinciaDeclarada ?? "sin dato"}</strong> — el pin cae en{" "}
        <strong>{hallazgo.provinciaGeoref}</strong> según Georef (dato oficial del Estado)
      </p>
      <a
        href={`https://www.google.com/maps?q=${hallazgo.latitud},${hallazgo.longitud}`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-1 inline-block font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
      >
        Ver pin en Maps
      </a>
    </div>
  );
}

function SeccionTier1({ prestadorId }: { prestadorId: string }) {
  const [hallazgos, setHallazgos] = useState<HallazgoTier1[] | null>(null);
  const [consultando, setConsultando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoConsultarGeoref | null>(null);

  const refresh = () =>
    liquidacionesApi.listGeovalidacionTier1(prestadorId).then(setHallazgos).catch(() => setHallazgos([]));
  useEffect(() => { void refresh(); }, [prestadorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const consultar = async () => {
    setConsultando(true);
    try {
      setResultado(await liquidacionesApi.consultarGeoref(prestadorId));
      await refresh();
    } finally { setConsultando(false); }
  };

  return (
    <Tarjeta
      numero="1b"
      titulo="Provincia del pin vs. Gestión (Georef)"
      descripcion="Compara la provincia declarada en Gestión contra la que devuelve el reverse geocoding de Georef (API del Estado argentino, gratuita) para el pin. Repetir esta acción solo consulta lo que todavía no está en cache."
      badge={<Badge variant="success">gratis, no es Google</Badge>}
    >
      <BrandButton size="sm" variant="outline" loading={consultando} onClick={consultar} className="self-start">
        Consultar Georef
      </BrandButton>
      {resultado && (
        <div className="flex flex-wrap gap-2">
          <Badge variant="info">{resultado.consultadas} consultadas</Badge>
          <Badge variant="neutral">{resultado.yaEnCache} ya en cache</Badge>
          {resultado.pendientesPorTope > 0 && (
            <Badge variant="warning">{resultado.pendientesPorTope} pendientes — repetí la acción</Badge>
          )}
        </div>
      )}
      {hallazgos === null ? (
        <div className="flex h-16 items-center justify-center"><Spinner /></div>
      ) : hallazgos.length > 0 ? (
        <div className="flex max-h-[32vh] flex-col gap-2 overflow-y-auto pr-1">
          {hallazgos.map((h) => (
            <HallazgoTier1Item key={h.sigesSucursalId} hallazgo={h} />
          ))}
        </div>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          Sin discrepancias de provincia detectadas sobre lo ya consultado.
        </p>
      )}
    </Tarjeta>
  );
}

function HallazgoTier1bItem({ hallazgo }: { hallazgo: HallazgoTier1b }) {
  return (
    <div className="rounded-[8px] border border-destructive/40 bg-destructive/5 px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">
          {hallazgo.empresaNombre} — {hallazgo.sucursalNombre}
        </p>
        <Badge variant="danger">confirmado por 2 fuentes</Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">
        Declarada: <strong>{hallazgo.provinciaDeclarada ?? "sin dato"}</strong> — Georef y Nominatim
        coinciden: el pin está en <strong>{hallazgo.provinciaGeoref}</strong>
      </p>
      <div className="mt-1 flex items-center justify-between gap-2">
        <a
          href={`https://www.google.com/maps?q=${hallazgo.latitud},${hallazgo.longitud}`}
          target="_blank"
          rel="noopener noreferrer"
          className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
        >
          Ver pin en Maps
        </a>
        <p className="font-body text-[10px] text-muted-foreground">{hallazgo.atribucion}</p>
      </div>
    </div>
  );
}

function SeccionTier1b({ prestadorId }: { prestadorId: string }) {
  const [hallazgos, setHallazgos] = useState<HallazgoTier1b[] | null>(null);
  const [consultando, setConsultando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoConsultarNominatim | null>(null);

  const refresh = () =>
    liquidacionesApi.listGeovalidacionTier1b(prestadorId).then(setHallazgos).catch(() => setHallazgos([]));
  useEffect(() => { void refresh(); }, [prestadorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const consultar = async () => {
    setConsultando(true);
    try {
      setResultado(await liquidacionesApi.consultarNominatim(prestadorId));
      await refresh();
    } finally { setConsultando(false); }
  };

  return (
    <Tarjeta
      numero="1c"
      titulo="Segunda opinión (Nominatim / OpenStreetMap)"
      descripcion="Solo consulta las sucursales que Georef ya marcó con provincia distinta — si Nominatim coincide, son dos fuentes independientes de acuerdo, evidencia fuerte sin gastar Google."
      badge={<Badge variant="success">gratis, no es Google</Badge>}
    >
      <BrandButton size="sm" variant="outline" loading={consultando} onClick={consultar} className="self-start">
        Consultar Nominatim
      </BrandButton>
      {resultado && (
        <div className="flex flex-wrap gap-2">
          <Badge variant="info">{resultado.consultadas} consultadas</Badge>
          <Badge variant="neutral">{resultado.yaEnCache} ya en cache</Badge>
          {resultado.pendientesPorTope > 0 && (
            <Badge variant="warning">{resultado.pendientesPorTope} pendientes — repetí la acción</Badge>
          )}
        </div>
      )}
      {hallazgos === null ? (
        <div className="flex h-16 items-center justify-center"><Spinner /></div>
      ) : hallazgos.length > 0 ? (
        <div className="flex max-h-[32vh] flex-col gap-2 overflow-y-auto pr-1">
          {hallazgos.map((h) => (
            <HallazgoTier1bItem key={h.sigesSucursalId} hallazgo={h} />
          ))}
        </div>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          Sin confirmaciones de dos fuentes sobre lo ya consultado.
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
      <SeccionTier1 prestadorId={prestadorId} />
      <SeccionTier1b prestadorId={prestadorId} />

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
