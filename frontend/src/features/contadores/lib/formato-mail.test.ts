import { describe, expect, it } from "vitest";
import type { DetalleContadorRow } from "../types/detalle-contador-proceso";
import { formatearTablaMailHtml, formatearTablaMailTexto } from "./formato-mail";

const fila = (over: Partial<DetalleContadorRow>): DetalleContadorRow =>
  ({
    empresa: "Acme", sucursal: "Centro", modelo: "M404", serie: "S1", sector: null,
    estado_maquina: "Activa", direccion_ip: "10.0.0.1", mascara_ip: null, ...over,
  }) as DetalleContadorRow;

describe("tabla de contadores para pegar en un mail (texto)", () => {
  it("titula con el cliente y separa las columnas pedidas por tabulador", () => {
    const texto = formatearTablaMailTexto([fila({})], "Acme SA");
    const [titulo, vacio, encabezado, linea] = texto.split("\n");
    expect(titulo).toBe("Detalle de Contadores — Acme SA");
    expect(vacio).toBe("");
    expect(encabezado).toBe("Empresa\tSucursal\tModelo\tSerie\tSector\tEstado Máquina\tDirección IP\tMáscara IP");
    expect(linea).toBe("Acme\tCentro\tM404\tS1\t\tActiva\t10.0.0.1\t");
  });

  it("ordena por empresa y después por sucursal", () => {
    const texto = formatearTablaMailTexto(
      [fila({ empresa: "Beta", sucursal: "A" }), fila({ empresa: "Acme", sucursal: "Zárate" }), fila({ empresa: "Acme", sucursal: "Ávila" })],
      "X",
    );
    expect(texto.split("\n").slice(3).map((l) => l.split("\t").slice(0, 2).join("/"))).toEqual([
      "Acme/Ávila", "Acme/Zárate", "Beta/A",
    ]);
  });
});

describe("tabla de contadores para pegar en un mail (HTML)", () => {
  it("cuenta los equipos en singular y plural", () => {
    expect(formatearTablaMailHtml([fila({})], "X")).toContain(">1 equipo</td>");
    expect(formatearTablaMailHtml([fila({}), fila({ serie: "S2" })], "X")).toContain(">2 equipos</td>");
  });

  it("escapa el HTML del cliente y de las celdas", () => {
    const html = formatearTablaMailHtml([fila({ sector: "<b>Depósito & Co</b>" })], "A&B <SA>");
    expect(html).toContain("Detalle de Contadores — A&amp;B &lt;SA&gt;</td>");
    expect(html).toContain("&lt;b&gt;Depósito &amp; Co&lt;/b&gt;");
    expect(html).not.toContain("<b>");
  });

  it("arma una fila por equipo con las 8 columnas y estilos inline", () => {
    const html = formatearTablaMailHtml([fila({}), fila({ serie: "S2" })], "X");
    expect(html.match(/<th /g)).toHaveLength(8);
    expect(html.match(/<td style="border-bottom/g)).toHaveLength(16);
    expect(html).not.toContain("<style");
    expect(html).toContain('colspan="8"');
  });
});
