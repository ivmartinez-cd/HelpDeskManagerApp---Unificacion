import { httpClient } from "@/services/http-client";
import type {
  AplicarDistanciasResult,
  AuditarPinesResult,
  CalculoKmPreview,
  EstadoAsistenteKm,
  GeocodeCandidato,
  GeocodificarResultado,
  HallazgoTier0,
  HallazgoTier1,
  HallazgoTier1b,
  PinSospechoso,
  ResultadoConsultarGeoref,
  ResultadoConsultarNominatim,
  ResultadoWorklistTier2,
  SucursalCoordenadas,
  TablaKm,
} from "../types/liquidaciones";
import { fetchCatalogoCompleto } from "./_shared";

/** Geolocalización / distancias (two-step preview→aplicar) y pines. */
export const geolocalizacionApi = {
  estadoAsistenteKm: (prestadorId: string) =>
    httpClient.get<EstadoAsistenteKm>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/asistente-km/estado`,
    ),

  previewCalcularDistancias: (prestadorId: string) =>
    httpClient.post<CalculoKmPreview>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/calcular-distancias/preview`,
    ),

  aplicarCalcularDistancias: (prestadorId: string, previewId: string) =>
    httpClient.post<AplicarDistanciasResult>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/calcular-distancias/aplicar`,
      { previewId },
    ),

  geocodificarFaltantes: (prestadorId: string) =>
    httpClient.post<GeocodificarResultado>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geocodificar-faltantes`,
    ),

  listCoordenadas: (prestadorId: string) =>
    fetchCatalogoCompleto<SucursalCoordenadas>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/coordenadas`,
      new URLSearchParams(),
    ),

  resolverCoordenadas: (
    prestadorId: string,
    sigesSucursalId: number,
    body: { candidatoIdx?: number; latitud?: number; longitud?: number },
  ) =>
    httpClient.put<SucursalCoordenadas>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/coordenadas/${sigesSucursalId}`,
      body,
    ),

  listGeovalidacionTier0: (prestadorId: string) =>
    fetchCatalogoCompleto<HallazgoTier0>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/tier0`,
      new URLSearchParams(),
    ),

  consultarGeoref: (prestadorId: string) =>
    httpClient.post<ResultadoConsultarGeoref>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/tier1/consultar-georef`,
    ),

  listGeovalidacionTier1: (prestadorId: string) =>
    fetchCatalogoCompleto<HallazgoTier1>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/tier1`,
      new URLSearchParams(),
    ),

  consultarNominatim: (prestadorId: string) =>
    httpClient.post<ResultadoConsultarNominatim>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/tier1b/consultar-nominatim`,
    ),

  listGeovalidacionTier1b: (prestadorId: string) =>
    fetchCatalogoCompleto<HallazgoTier1b>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/tier1b`,
      new URLSearchParams(),
    ),

  listPinesSospechosos: (prestadorId: string) =>
    fetchCatalogoCompleto<PinSospechoso>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/pines-sospechosos`,
      new URLSearchParams(),
    ),

  auditarPines: (prestadorId: string, sigesSucursalIds?: number[]) =>
    httpClient.post<AuditarPinesResult>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/auditar-pines`,
      sigesSucursalIds ? { sigesSucursalIds } : undefined,
    ),

  getWorklistTier2: (prestadorId: string) =>
    httpClient.get<ResultadoWorklistTier2>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geovalidacion/worklist`,
    ),

  corregirPin: (prestadorId: string, sigesSucursalId: number) =>
    httpClient.post<void>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/sucursal/${sigesSucursalId}/corregir-pin`,
    ),

  listCuadriculas: (prestadorId: string) =>
    httpClient.get<{ cuadricula: string; sigesBaseSucursalId: number | null }[]>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas`,
    ),

  mapearCuadricula: (prestadorId: string, cuadricula: string, sigesBaseSucursalId: number) =>
    httpClient.put<{ id: string; prestadorId: string; cuadricula: string; sigesBaseSucursalId: number }>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas/${encodeURIComponent(cuadricula)}`,
      { sigesBaseSucursalId },
    ),

  eliminarMapeoCuadricula: (prestadorId: string, cuadricula: string) =>
    httpClient.delete<void>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas/${encodeURIComponent(cuadricula)}`,
    ),

  refrescarDatosSucursales: (prestadorId: string) =>
    httpClient.post<{
      actualizadas: number;
      sinCambios: number;
      noEncontradas: number;
      vinculadas: number;
      cambios: { sucursalNombre: string; empresaNombre: string; domicilioAntes: string | null; domicilioDespues: string | null }[];
      noEncontradasDetalle: { empresaNombre: string; sucursalNombre: string }[];
    }>(`/api/liquidaciones/siges/prestador/${prestadorId}/refrescar-datos-sucursales`),

  buscarLugarFila: (tablaKmId: string) =>
    httpClient.post<{ candidatos: GeocodeCandidato[] }>(
      `/api/liquidaciones/tabla-km/${tablaKmId}/buscar-lugar`,
    ),

  resolverCoordenadasFila: (
    tablaKmId: string,
    body: { candidatoIdx?: number; latitud?: number; longitud?: number },
  ) =>
    httpClient.put<TablaKm>(`/api/liquidaciones/tabla-km/${tablaKmId}/coordenadas`, body),

  recalcularKmFila: (tablaKmId: string) =>
    httpClient.post<TablaKm>(`/api/liquidaciones/tabla-km/${tablaKmId}/recalcular-km`),
};
