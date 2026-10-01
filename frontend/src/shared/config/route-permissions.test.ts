import { describe, expect, it } from "vitest";
import { canAccessPath, moduleForRule, ruleForPath, type AccessChecks } from "./route-permissions";

function checks(permisos: string[], funciones: string[] = []): AccessChecks {
  return {
    can: (module, action) => permisos.includes(`${module}.${action}`),
    hasFeature: (feature) => funciones.includes(feature),
  };
}

describe("canAccessPath", () => {
  it("la raíz de contadores pide exportar, pero sus sub-rutas alcanzan con ver", () => {
    const soloVer = checks(["contadores.view"]);
    expect(canAccessPath("/contadores", soloVer)).toBe(false);
    expect(canAccessPath("/contadores", checks(["contadores.export"]))).toBe(true);
    expect(canAccessPath("/contadores/proyeccion", soloVer)).toBe(true);
  });

  it("una ruta de función se abre con la función, sin permiso de acción", () => {
    const conFuncion = checks([], ["contadores-coberturas"]);
    expect(canAccessPath("/contadores/coberturas", conFuncion)).toBe(true);
    expect(canAccessPath("/contadores/coberturas", checks([]))).toBe(false);
  });

  it("alcanza con cualquiera de las acciones de la regla", () => {
    expect(canAccessPath("/tareas-varias", checks(["tareas-varias.approve"]))).toBe(true);
    expect(canAccessPath("/tareas-varias", checks(["wati.view"]))).toBe(false);
  });

  it("ignora la query string y deja pasar lo que no está mapeado", () => {
    expect(canAccessPath("/wati?x=1", checks(["wati.view"]))).toBe(true);
    expect(canAccessPath("/", checks([]))).toBe(true);
    expect(ruleForPath("/watis")).toBeNull();
  });
});

describe("moduleForRule", () => {
  it("toma el módulo de la primera acción, o el prefijo de la función", () => {
    expect(moduleForRule(ruleForPath("/wati")!)).toBe("wati");
    expect(moduleForRule(ruleForPath("/contadores/coberturas")!)).toBe("contadores");
  });
});
