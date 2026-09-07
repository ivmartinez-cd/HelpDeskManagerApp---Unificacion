"use client";

import { useEffect, useMemo, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Spst, Tarifario, ZonaSigesEstado } from "../types/liquidaciones";

/** Lo que hace falta para mostrar, en una tabla del prestador, la cadena que
 * resuelve el precio de cada fila (SPST → zona de Siges → tarifa): los SPST
 * por id, qué SPST (o la genérica, `null`) tienen tarifa cargada, y la
 * descripción de zona de Siges mapeada a cada uno (clave "" = genérica). Sin
 * vínculo a Siges no hay zonas y se cae al nombre/zona de cobertura del SPST. */
export function useSpstsZonas(prestadorId: string) {
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [spstsConTarifa, setSpstsConTarifa] = useState<Set<string | null>>(new Set());
  const [zonasSiges, setZonasSiges] = useState<ZonaSigesEstado[]>([]);

  useEffect(() => {
    let cancelado = false;
    const cargar = prestadorId
      ? Promise.all([
          liquidacionesApi.listSpsts({ prestadorId }),
          liquidacionesApi.listTarifarios(prestadorId),
          liquidacionesApi.getSigesZonas(prestadorId).then((r) => r.zonas).catch(() => []),
        ])
      : Promise.resolve([[], [], []] as [Spst[], Tarifario[], ZonaSigesEstado[]]);
    void cargar.then(([spstsData, tarifariosData, zonasData]) => {
      if (cancelado) return;
      setSpsts(spstsData);
      setSpstsConTarifa(new Set(tarifariosData.map((t) => t.spstId)));
      setZonasSiges(zonasData);
    });
    return () => { cancelado = true; };
  }, [prestadorId]);

  const spstsPorId = useMemo(() => new Map(spsts.map((s) => [s.id, s])), [spsts]);
  const zonaSigesPorSpst = useMemo(
    () => new Map(zonasSiges.filter((z) => z.mapeada).map((z) => [z.spstId ?? "", z.descripcionSiges])),
    [zonasSiges],
  );
  return { spsts, spstsPorId, spstsConTarifa, zonaSigesPorSpst };
}
