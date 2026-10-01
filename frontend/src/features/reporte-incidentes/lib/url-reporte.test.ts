import { describe, expect, it } from "vitest";
import { FILTROS_VACIOS, alternarFiltro, leerEstado, urlReporte } from "./url-reporte";

describe("estado del reporte en la URL", () => {
  it("sin empresa no hay reporte que mostrar", () => {
    expect(leerEstado(new URLSearchParams("periodo=2026-09&meses=3"))).toBeNull();
  });

  it("lee el pedido y los filtros; los que faltan quedan vacíos", () => {
    const estado = leerEstado(new URLSearchParams("empresa=42&periodo=2026-09&meses=6&categoria=Toner"));
    expect(estado).toEqual({
      pedido: { empresaId: "42", periodo: "2026-09", meses: 6 },
      filtros: { sucursal: "", categoria: "Toner", subcategoria: "" },
    });
  });

  it("los meses faltantes o fuera de rango se acotan a 1..24", () => {
    expect(leerEstado(new URLSearchParams("empresa=42"))?.pedido).toEqual({
      empresaId: "42",
      periodo: "",
      meses: 1,
    });
    expect(leerEstado(new URLSearchParams("empresa=42&meses=99"))?.pedido.meses).toBe(24);
    expect(leerEstado(new URLSearchParams("empresa=42&meses=abc"))?.pedido.meses).toBe(1);
  });

  it("arma la URL solo con los filtros activos", () => {
    const pedido = { empresaId: "42", periodo: "2026-09", meses: 3 };
    expect(urlReporte(pedido)).toBe("/reporte-incidentes/reporte?empresa=42&periodo=2026-09&meses=3");
    expect(urlReporte(pedido, { ...FILTROS_VACIOS, sucursal: "Casa Central" })).toBe(
      "/reporte-incidentes/reporte?empresa=42&periodo=2026-09&meses=3&sucursal=Casa+Central",
    );
  });

  it("la URL generada se vuelve a leer igual", () => {
    const pedido = { empresaId: "7", periodo: "2025-12", meses: 12 };
    const filtros = { sucursal: "Rosario", categoria: "", subcategoria: "Atasco & papel" };
    const url = urlReporte(pedido, filtros);
    expect(leerEstado(new URLSearchParams(url.split("?")[1]))).toEqual({ pedido, filtros });
  });

  it("clickear un filtro activo lo apaga; uno distinto lo reemplaza", () => {
    const filtros = { ...FILTROS_VACIOS, categoria: "Toner" };
    expect(alternarFiltro(filtros, "categoria", "Toner").categoria).toBe("");
    expect(alternarFiltro(filtros, "categoria", "Rodillo").categoria).toBe("Rodillo");
    expect(alternarFiltro(filtros, "sucursal", "Rosario")).toEqual({
      sucursal: "Rosario",
      categoria: "Toner",
      subcategoria: "",
    });
  });
});
