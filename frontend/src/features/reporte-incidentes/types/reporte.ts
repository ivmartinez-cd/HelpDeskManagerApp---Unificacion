/** Tipos del módulo reporte-incidentes. Reflejan los schemas del backend
 * (`backend/src/modules/reporte_incidentes/presentation/schemas/`), que
 * serializan en snake_case sin alias. */

export interface Empresa {
  id: string;
  nombre: string;
}

export interface Conteo {
  nombre: string;
  cantidad: number;
}

export interface ConteoSubcategoria extends Conteo {
  categoria: string;
}

export interface Kpis {
  total: number;
  categoria_principal: string;
  categoria_principal_cantidad: number;
  categoria_principal_pct: number;
  sucursal_principal: string;
  sucursal_principal_cantidad: number;
}

export interface Filtros {
  sucursal: string;
  categoria: string;
  subcategoria: string;
}

export type DimensionFiltro = keyof Filtros;

export interface OpcionFiltro {
  valor: string;
  cantidad: number;
}

export interface OpcionesFiltro {
  sucursales: OpcionFiltro[];
  categorias: OpcionFiltro[];
  subcategorias: OpcionFiltro[];
}

export interface ItemSinReparacion {
  subcategoria: string;
  cantidad: number;
  pct: number;
}

export interface ItemMejora {
  categoria: string;
  subcategoria: string;
  cantidad: number;
  pct: number;
  sucursal_principal: string;
  sucursal_principal_cantidad: number;
  sucursal_principal_pct: number;
  concentrado: boolean;
}

export interface OportunidadesMejora {
  total: number;
  fuera_del_equipo_total: number;
  fuera_del_equipo_pct: number;
  sin_reparacion_total: number;
  sin_reparacion_pct: number;
  sin_reparacion_items: ItemSinReparacion[];
  items: ItemMejora[];
}

export interface CategoriaTaxonomia {
  nombre: string;
  color: string;
  subcategorias: string[];
}

/** Todo el dashboard salvo la tabla. `kpis` y `evolucion` son de la selección
 * filtrada; `categorias`, `subcategorias`, `sucursales` y `oportunidades`, del
 * período completo. */
export interface Reporte {
  empresa: Empresa;
  periodo: string;
  meses: number;
  periodos: string[];
  rango_etiqueta: string;
  generado_en: string;
  pendientes_ia: number;
  pendientes_revision: number;
  filtros: Filtros;
  filtros_activos: boolean;
  opciones: OpcionesFiltro;
  kpis: Kpis;
  evolucion: Conteo[];
  categorias: Conteo[];
  subcategorias: ConteoSubcategoria[];
  sucursales: Conteo[];
  oportunidades: OportunidadesMejora;
  colores: Record<string, string>;
  taxonomia: CategoriaTaxonomia[];
}

export interface Trabajo {
  descripcion: string;
  observ: string | null;
  fecha: string | null;
  estado: string | null;
  tecnico: string | null;
}

export interface Incidente {
  id: string;
  numero: string;
  fecha: string;
  sucursal: string | null;
  maquina: string | null;
  estado: string | null;
  descripcion: string;
  costo: number | null;
  solicitante: string | null;
  tecnico: string | null;
  tipo_trabajo: string | null;
  causa: string | null;
  articulo: string | null;
  fecha_cierre: string | null;
  solucion: string | null;
  trabajos: Trabajo[];
  categoria: string | null;
  subcategoria: string | null;
}

export type CampoOrden =
  | "numero"
  | "fecha"
  | "sucursal"
  | "descripcion"
  | "causa"
  | "solucion"
  | "categoria"
  | "subcategoria";

export interface ResultadoIA {
  casos: number;
  tipificados: number;
  fallidos: number;
  llamadas: number;
}

export interface CategoriaDetalle {
  nombre: string;
  color: string;
  descripcion: string;
  subcategorias: string[];
}

/** Lo que identifica un reporte: cliente + mes final + cantidad de meses. */
export interface PedidoReporte {
  empresaId: string;
  periodo: string;
  meses: number;
}

export const PENDIENTE = "Pendiente de revision";
