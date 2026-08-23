"use client";

import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import { useEffect, useRef } from "react";
import type { EstadoPreventivo, PuntoMapaPreventivo } from "../types/preventivos";
import { numberFormat } from "./preventivos-format";
import { crearIconoCluster, peorEstadoDe } from "./preventivos-mapa-cluster";
import { puntosParaEncuadre } from "./preventivos-mapa-encuadre";
import { crearIconoPunto } from "./preventivos-mapa-icono";
import { ESTADO_META } from "./preventivos-tabla";

const CENTRO_DEFAULT: [number, number] = [-34.6037, -58.3816]; // CABA
const ZOOM_DEFAULT = 11;

type LeafletMarker = import("leaflet").Marker;

function escapeHtml(valor: string): string {
  const div = document.createElement("div");
  div.textContent = valor;
  return div.innerHTML;
}

function popupHtml(punto: PuntoMapaPreventivo): string {
  const meta = ESTADO_META[punto.peor_estado];
  const vencidoInfo =
    punto.peor_estado === "vencido" && punto.dias_vencido_max !== null
      ? ` · hace ${numberFormat.format(punto.dias_vencido_max)} días`
      : "";
  const habilitadosInfo =
    punto.cant_habilitadas > 0
      ? ` · ${numberFormat.format(punto.cant_habilitadas)} habilitado(s)`
      : "";
  return `<div style="display:flex;flex-direction:column;gap:4px;font-size:13px">
    <p style="margin:0;font-weight:600">${escapeHtml(punto.cliente)}</p>
    <p style="margin:0;font-size:12px;opacity:.7">${escapeHtml(punto.sucursal)} · ${escapeHtml(punto.zona)}</p>
    <p style="margin:0;font-size:12px;font-weight:600">${escapeHtml(meta.label)}${vencidoInfo}</p>
    <p style="margin:0;font-size:12px;opacity:.7">${numberFormat.format(punto.cant_maquinas)} equipo(s)${habilitadosInfo}</p>
  </div>`;
}

/** Leaflet vanilla, no react-leaflet: con Next 16 + Turbopack, react-leaflet
 * arrastra un `import "leaflet"` estático que revienta el build de
 * producción ("window is not defined") aun detrás de next/dynamic
 * ssr:false — ver preventivos-mapa-icono.ts. Acá la librería (y el plugin de
 * clustering) se cargan con `import()` dentro de un efecto, nunca a nivel
 * de módulo. Clustering: sucursales muy cercanas o en el mismo punto exacto
 * (ej. varios locales de un mismo shopping) se agrupan en una burbuja con
 * contador; al hacer click hace zoom y, si ya está al máximo, las abre en
 * abanico (spiderfy, comportamiento default del plugin) para que cada pin
 * siga siendo clickeable. */
export function PreventivosMapaCanvas({ puntos }: { puntos: PuntoMapaPreventivo[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const clusterGroupRef = useRef<import("leaflet").MarkerClusterGroup | null>(null);

  useEffect(() => {
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelado = false;
    // leaflet.markercluster es un UMD viejo escrito para <script> clásico: su
    // factory referencia el identificador global `L` directo (sin requerir
    // "leaflet"), así que hay que exponer window.L y recién después cargar el
    // plugin — cargarlos en paralelo lo deja evaluando antes de que exista L.
    import("leaflet").then(async (mod) => {
      if (cancelado || !containerRef.current) return;
      const L = mod.default;
      (window as unknown as { L: typeof L }).L = L;
      await import("leaflet.markercluster");
      if (cancelado || !containerRef.current) return;
      if (!mapRef.current) {
        const mapa = L.map(containerRef.current).setView(CENTRO_DEFAULT, ZOOM_DEFAULT);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(mapa);
        mapRef.current = mapa;
      }
      const mapa = mapRef.current;
      if (clusterGroupRef.current) {
        mapa.removeLayer(clusterGroupRef.current);
      }

      const estadoPorMarker = new WeakMap<LeafletMarker, EstadoPreventivo>();
      const grupo = L.markerClusterGroup({
        showCoverageOnHover: false,
        iconCreateFunction: (cluster) => {
          const estados = cluster
            .getAllChildMarkers()
            .map((m) => estadoPorMarker.get(m) ?? ("al_dia" as EstadoPreventivo));
          return crearIconoCluster(L, cluster.getChildCount(), peorEstadoDe(estados));
        },
      });

      const ubicados = puntos.filter(
        (p) => p.ubicado && p.latitud !== null && p.longitud !== null,
      );
      for (const punto of ubicados) {
        const marker = L.marker([punto.latitud as number, punto.longitud as number], {
          icon: crearIconoPunto(L, punto.peor_estado),
        });
        marker.bindPopup(popupHtml(punto));
        estadoPorMarker.set(marker, punto.peor_estado);
        grupo.addLayer(marker);
      }
      grupo.addTo(mapa);
      clusterGroupRef.current = grupo;

      const posiciones: [number, number][] = ubicados.map((p) => [
        p.latitud as number,
        p.longitud as number,
      ]);
      if (posiciones.length === 0) return;
      const encuadre = puntosParaEncuadre(posiciones);
      if (encuadre.length === 1) {
        mapa.setView(encuadre[0], 14);
      } else {
        mapa.fitBounds(encuadre, { padding: [32, 32], maxZoom: 15 });
      }
    });
    return () => {
      cancelado = true;
    };
  }, [puntos]);

  return <div ref={containerRef} className="h-[520px] w-full rounded-[12px]" />;
}
