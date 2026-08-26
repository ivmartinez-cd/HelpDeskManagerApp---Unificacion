"use client";

import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import { useEffect, useRef } from "react";
import type { EstadoPreventivo, PuntoMapaPreventivo } from "../types/preventivos";
import { numberFormat } from "./preventivos-format";
import { crearIconoCluster, peorEstadoDe } from "./preventivos-mapa-cluster";
import { puntosParaEncuadre } from "./preventivos-mapa-encuadre";
import { crearIconoPunto } from "./preventivos-mapa-icono";
import { ESTADO_META, formatFecha } from "./preventivos-tabla";

const CENTRO_DEFAULT: [number, number] = [-34.6037, -58.3816]; // CABA
const ZOOM_DEFAULT = 11;

type LeafletMarker = import("leaflet").Marker;

// Clases usadas para delegar los clicks de los botones del popup (ver el
// listener de "popupopen" más abajo) — el popup es HTML string, no JSX, así
// que no hay onClick nativo de React acá.
const EDITAR_BTN_CLASS = "preventivos-popup-editar";
const CARGAR_BTN_CLASS = "preventivos-popup-cargar";

function escapeHtml(valor: string): string {
  const div = document.createElement("div");
  div.textContent = valor;
  return div.innerHTML;
}

/** "vencido" es el único estado del módulo cuya etiqueta cambia con la
 * cantidad ("1 vencido" / "3 vencidos"); el resto son frases invariantes
 * ("al día", "sin preventivo", "sin frecuencia", "por vencer"). */
function labelDistribucion(estado: EstadoPreventivo, cantidad: number): string {
  if (estado === "vencido") return cantidad === 1 ? "vencido" : "vencidos";
  return ESTADO_META[estado].label.toLowerCase();
}

function segmentoDistribucion(
  item: PuntoMapaPreventivo["distribucion"][number],
  punto: PuntoMapaPreventivo,
): string {
  let detalle = "";
  if (item.estado === "vencido" && punto.fecha_vencido_min !== null) {
    detalle = ` (${formatFecha(punto.fecha_vencido_min)})`;
  } else if (item.estado === "sin_preventivo" && punto.fecha_tentativa_min !== null) {
    detalle = ` (tentativo ${formatFecha(punto.fecha_tentativa_min)})`;
  }
  return `${numberFormat.format(item.cantidad)} ${labelDistribucion(item.estado, item.cantidad)}${detalle}`;
}

function popupHtml(punto: PuntoMapaPreventivo, canUpdate: boolean): string {
  const distribucionInfo = punto.distribucion
    .map((item) => segmentoDistribucion(item, punto))
    .join(" · ");
  const habilitadosInfo =
    punto.cant_habilitadas > 0
      ? ` · ${numberFormat.format(punto.cant_habilitadas)} habilitado(s)`
      : "";
  const domicilioInfo = punto.domicilio
    ? `<p style="margin:0;font-size:12px;opacity:.7">${escapeHtml(punto.domicilio)}</p>`
    : "";
  const editarInfo = canUpdate
    ? `<button type="button" data-id-sucursal="${punto.id_sucursal}" class="${EDITAR_BTN_CLASS}"
        style="margin-top:4px;align-self:flex-start;border:none;background:none;padding:0;font-size:12px;font-weight:600;color:#c2410c;cursor:pointer;text-decoration:underline">
        Corregir ubicación
      </button>`
    : "";
  const cargarInfo = canUpdate
    ? `<button type="button" data-id-sucursal="${punto.id_sucursal}" class="${CARGAR_BTN_CLASS}"
        style="margin-top:2px;align-self:flex-start;border:none;background:none;padding:0;font-size:12px;font-weight:600;color:#c2410c;cursor:pointer;text-decoration:underline">
        Cargar preventivo
      </button>`
    : "";
  return `<div style="display:flex;flex-direction:column;gap:4px;font-size:13px">
    <p style="margin:0;font-weight:600">${escapeHtml(punto.cliente)}</p>
    <p style="margin:0;font-size:12px;opacity:.7">${escapeHtml(punto.sucursal)} · ${escapeHtml(punto.zona)}</p>
    ${domicilioInfo}
    <p style="margin:0;font-size:12px;font-weight:600">${escapeHtml(distribucionInfo)}</p>
    <p style="margin:0;font-size:12px;opacity:.7">${numberFormat.format(punto.cant_maquinas)} equipo(s)${habilitadosInfo}</p>
    ${cargarInfo}
    ${editarInfo}
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
interface PreventivosMapaCanvasProps {
  puntos: PuntoMapaPreventivo[];
  canUpdate: boolean;
  onEditarUbicacion: (idSucursal: number) => void;
  onCargarPreventivo: (idSucursal: number) => void;
}

export function PreventivosMapaCanvas({
  puntos,
  canUpdate,
  onEditarUbicacion,
  onCargarPreventivo,
}: PreventivosMapaCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const clusterGroupRef = useRef<import("leaflet").MarkerClusterGroup | null>(null);
  // Refs de callback "siempre última": el listener de popupopen se engancha
  // una sola vez (al crear el mapa) y lee acá en vez de en el closure para
  // no depender de la identidad de la prop entre renders.
  const onEditarRef = useRef(onEditarUbicacion);
  useEffect(() => {
    onEditarRef.current = onEditarUbicacion;
  }, [onEditarUbicacion]);
  const onCargarRef = useRef(onCargarPreventivo);
  useEffect(() => {
    onCargarRef.current = onCargarPreventivo;
  }, [onCargarPreventivo]);

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
        // Delegación: el popup es HTML string (no JSX), así que el botón
        // "Corregir ubicación" no tiene onClick de React — se engancha acá,
        // una sola vez, cada vez que Leaflet abre CUALQUIER popup del mapa.
        mapa.on("popupopen", (e) => {
          const popupEl = e.popup.getElement();
          const botonEditar = popupEl?.querySelector<HTMLButtonElement>(`.${EDITAR_BTN_CLASS}`);
          botonEditar?.addEventListener(
            "click",
            () => onEditarRef.current(Number(botonEditar.dataset.idSucursal)),
            { once: true },
          );
          const botonCargar = popupEl?.querySelector<HTMLButtonElement>(`.${CARGAR_BTN_CLASS}`);
          botonCargar?.addEventListener(
            "click",
            () => onCargarRef.current(Number(botonCargar.dataset.idSucursal)),
            { once: true },
          );
        });
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
        marker.bindPopup(popupHtml(punto, canUpdate));
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
  }, [puntos, canUpdate]);

  // `isolate`: Leaflet usa z-index internos hasta 1000 (controles) y 700
  // (popups) sobre `.leaflet-container`, que Leaflet fija en position:relative
  // SIN z-index propio — eso no aísla stacking context, así que esos z-index
  // se comparaban directo contra el z-[100] del modal de "Corregir ubicación"
  // (BrandModal) y el mapa ganaba donde se superponían. `isolate` crea un
  // stacking context nuevo acá: todo lo de adentro del mapa queda contenido,
  // nunca puede pintar por encima de un elemento de afuera sin importar su
  // z-index interno.
  return <div ref={containerRef} className="isolate h-[520px] w-full rounded-[12px]" />;
}
