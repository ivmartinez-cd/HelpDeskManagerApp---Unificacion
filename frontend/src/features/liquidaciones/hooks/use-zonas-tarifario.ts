"use client";

import { useEffect, useMemo, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Spst, ZonaSigesEstado } from "../types/liquidaciones";

/** Lo necesario para nombrar cada zona del tarifario de un prestador: sus SPST
 * por id y la zona de Siges mapeada a cada SPST (clave "" = genérica). */
export function useZonasTarifario(prestadorId: string) {
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [zonasSiges, setZonasSiges] = useState<ZonaSigesEstado[]>([]);

  // SPST del prestador seleccionado — solo para resolver el nombre de la zona
  // cuando no tiene mapeo a Siges; la tarifa en sí guarda el spstId crudo.
  useEffect(() => {
    let cancelado = false;
    const cargar = prestadorId
      ? liquidacionesApi.listSpsts({ prestadorId })
      : Promise.resolve([]);
    void cargar.then((data) => { if (!cancelado) setSpsts(data); });
    return () => { cancelado = true; };
  }, [prestadorId]);
  const spstsPorId = useMemo(() => new Map(spsts.map((s) => [s.id, s])), [spsts]);

  // Zonas de Siges mapeadas a cada SPST (o a la genérica, spstId null): el
  // tarifario se muestra con el nombre de zona tal cual está en Siges, que es
  // lo que la TL compara (pedido de Iván, 2026-09-07). Sin vínculo a Siges no
  // hay zonas y cada grupo cae al nombre del SPST.
  useEffect(() => {
    let cancelado = false;
    const cargar = prestadorId
      ? liquidacionesApi.getSigesZonas(prestadorId).then((r) => r.zonas)
      : Promise.resolve([]);
    void cargar
      .catch(() => [] as ZonaSigesEstado[])
      .then((data) => { if (!cancelado) setZonasSiges(data); });
    return () => { cancelado = true; };
  }, [prestadorId]);
  const zonaSigesPorSpst = useMemo(
    () => new Map(zonasSiges.filter((z) => z.mapeada).map((z) => [z.spstId ?? "", z.descripcionSiges])),
    [zonasSiges],
  );

  return { spstsPorId, zonaSigesPorSpst };
}
