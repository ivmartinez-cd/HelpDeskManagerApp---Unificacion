import { describe, expect, it } from "vitest";
import type { RequestRow } from "../types";
import { partitionBySucursalNotice } from "./sucursal-filter";

const row = (id: string, requiereCambioSucursal: boolean) => ({ id, requiereCambioSucursal }) as unknown as RequestRow;

describe("carga en lote con aviso de cambio de sucursal", () => {
  it("deja afuera del lote las filas con aviso de sucursal, conservando el orden", () => {
    const filas = [row("a", false), row("b", true), row("c", false), row("d", true)];
    const { included, excluded } = partitionBySucursalNotice(filas);
    expect(included).toEqual([filas[0], filas[2]]);
    expect(excluded).toEqual([filas[1], filas[3]]);
  });
});
