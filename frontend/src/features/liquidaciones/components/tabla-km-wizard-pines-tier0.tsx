"use client";

import { useEffect, useState } from "react";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { HallazgoTier0 } from "../types/liquidaciones";

export function Tarjeta({ numero, titulo, descripcion, badge, children }: {
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

export function SeccionTier0({ prestadorId }: { prestadorId: string }) {
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
