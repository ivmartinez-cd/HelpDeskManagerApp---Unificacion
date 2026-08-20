"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  HallazgoTier1, HallazgoTier1b, ResultadoConsultarGeoref, ResultadoConsultarNominatim,
} from "../types/liquidaciones";
import { Tarjeta } from "./tabla-km-wizard-pines-tier0";

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

export function SeccionTier1({ prestadorId }: { prestadorId: string }) {
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

export function SeccionTier1b({ prestadorId }: { prestadorId: string }) {
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
