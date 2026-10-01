import { describe, expect, it } from "vitest";
import {
  describirDiferenciaKm, describirDondeCae, enlaceMaps, plural, traducirCodigoTier0, traducirPrecisionGoogle,
} from "./asistente-km-textos";

describe("textos llanos del Asistente de KM", () => {
  it("pluraliza según la cantidad, sin el '(es)' del wizard viejo", () => {
    expect(plural(1, "sucursal", "sucursales")).toBe("1 sucursal");
    expect(plural(3, "sucursal", "sucursales")).toBe("3 sucursales");
    expect(plural(0, "sucursal", "sucursales")).toBe("0 sucursales");
  });

  it("traduce los códigos de Tier 0 y deja legibles los desconocidos", () => {
    expect(traducirCodigoTier0("latlon_invertidas")).toBe("Latitud y longitud parecen intercambiadas");
    expect(traducirCodigoTier0("codigo_nuevo_raro")).toBe("codigo nuevo raro");
  });

  it("traduce la precisión de Google y baja a minúsculas la desconocida", () => {
    expect(traducirPrecisionGoogle("ROOFTOP")).toBe("ubicación exacta");
    expect(traducirPrecisionGoogle("APPROXIMATE")).toBe("ubicación aproximada");
    expect(traducirPrecisionGoogle("OTRO_TIPO")).toBe("otro_tipo");
  });

  it("muestra la diferencia con un decimal debajo de 10 km y entera desde 10", () => {
    expect(describirDiferenciaKm(3.26)).toBe("3.3 km de diferencia");
    expect(describirDiferenciaKm(9.94)).toBe("9.9 km de diferencia");
    expect(describirDiferenciaKm(10)).toBe("10 km de diferencia");
    expect(describirDiferenciaKm(152.7)).toBe("153 km de diferencia");
  });

  it("arma el enlace de Google Maps con la coordenada", () => {
    expect(enlaceMaps(-34.6, -58.38)).toBe("https://www.google.com/maps?q=-34.6,-58.38");
  });

  it("describe dónde cae el pin: provincia, coordenada cruda o sin dato", () => {
    expect(describirDondeCae("Córdoba", -31.4, -64.2)).toBe("Córdoba");
    expect(describirDondeCae(null, -33.123456, 151.2)).toBe("-33.1235, 151.2000");
    expect(describirDondeCae(null, null, -58)).toBe("un punto sin provincia conocida");
  });
});
