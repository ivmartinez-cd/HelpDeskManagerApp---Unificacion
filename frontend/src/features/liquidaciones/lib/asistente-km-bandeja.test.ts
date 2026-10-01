import { describe, expect, it } from "vitest";
import type {
  EstadoAsistenteKm, HallazgoTier1, HallazgoTier1b, ItemWorklistTier2, PinSospechoso,
  PropuestaN2Match, SucursalCoordenadas,
} from "../types/liquidaciones";
import {
  type DatosBandeja, componerBandeja, componerPinesRotos, consecuenciaPendientes,
  filtrarBandeja, resumirBandeja,
} from "./asistente-km-bandeja";

const datos = (over: Partial<DatosBandeja> = {}): DatosBandeja => ({
  estado: { sinCoordenadas: 0, estimacionGeocodificar: 0 } as EstadoAsistenteKm,
  propuestas: [], coordenadas: [], tier0: [], tier1: [], tier1b: [], worklist: null, pines: [],
  noEncontradas: null, ...over,
});

const suc = (id: number, empresa = `Empresa ${id}`) => ({
  sigesSucursalId: id, empresaNombre: empresa, sucursalNombre: `Suc ${id}`, latitud: -34, longitud: -58,
});

const google = (id: number, km: number): PinSospechoso => ({
  ...suc(id), direccion: "Calle 1", latitudSiges: -34, longitudSiges: -58, latitudGeocode: -31,
  longitudGeocode: -64, formattedAddress: "Calle 1, Córdoba", locationType: "ROOFTOP", discrepanciaKm: km,
});
const tier1 = (id: number): HallazgoTier1 => ({ ...suc(id), provinciaDeclarada: "Córdoba", provinciaGeoref: "Santa Fe" });
const tier1b = (id: number): HallazgoTier1b => ({
  ...tier1(id), provinciaNominatim: "Santa Fe", atribucion: "© OSM",
});
const worklistItem = (id: number, motivos: string[]): ItemWorklistTier2 => ({ ...suc(id), domicilio: null, motivos });
const coord = (id: number, estado: SucursalCoordenadas["estado"]) => ({ ...suc(id), estado }) as SucursalCoordenadas;

describe("pines rotos del Asistente de KM", () => {
  it("junta todas las evidencias de una misma sucursal en un solo pin, con la severidad de la más grave", () => {
    const pines = componerPinesRotos(datos({
      tier1b: [tier1b(1)],
      worklist: { certezaAbsoluta: [worklistItem(1, ["fuera_de_argentina"])], requiereVerificacion: [], estimacionLlamadasGoogle: 0 },
    }));
    expect(pines).toHaveLength(1);
    expect(pines[0].evidencias.map((e) => e.fuente)).toEqual(["geometria", "dos_fuentes"]);
    expect(pines[0].severidad).toBe(1);
    expect(pines[0].evidencias[0].texto).toBe("El pin está fuera de Argentina");
  });

  it("no repite la evidencia de una sola fuente cuando la segunda opinión ya confirmó", () => {
    const pines = componerPinesRotos(datos({ tier1: [tier1(1), tier1(2)], tier1b: [tier1b(1)] }));
    const pin1 = pines.find((p) => p.sigesSucursalId === 1)!;
    const pin2 = pines.find((p) => p.sigesSucursalId === 2)!;
    expect(pin1.evidencias.map((e) => e.fuente)).toEqual(["dos_fuentes"]);
    expect(pin2.evidencias.map((e) => e.fuente)).toEqual(["una_fuente"]);
  });

  it("solo una fuente no alcanza para mandarlo al CSV de Gestión", () => {
    const pines = componerPinesRotos(datos({ tier1: [tier1(2)], tier1b: [tier1b(1)] }));
    expect(pines.find((p) => p.sigesSucursalId === 1)!.vaAlCsv).toBe(true);
    expect(pines.find((p) => p.sigesSucursalId === 2)!.vaAlCsv).toBe(false);
  });

  it("explica la discrepancia de Google en km y habilita usar la dirección escrita", () => {
    const [cerca, lejos] = [componerPinesRotos(datos({ pines: [google(1, 3.26)] }))[0], componerPinesRotos(datos({ pines: [google(2, 42.4)] }))[0]];
    expect(cerca.evidencias[0].texto).toBe("El pin de Gestión está a 3.3 km de la dirección escrita, según Google.");
    expect(lejos.evidencias[0].texto).toBe("El pin de Gestión está a 42 km de la dirección escrita, según Google.");
    expect(cerca.pinGoogle?.sigesSucursalId).toBe(1);
    expect(cerca.domicilio).toBe("Calle 1");
  });

  it("menciona 'otra provincia' cuando no hay provincia declarada", () => {
    const pines = componerPinesRotos(datos({ tier1: [{ ...tier1(1), provinciaDeclarada: null }] }));
    expect(pines[0].evidencias[0].texto).toContain("su dirección dice otra provincia");
  });

  it("ordena por severidad (Google primero) y después por empresa", () => {
    const pines = componerPinesRotos(datos({
      tier1: [{ ...tier1(1), empresaNombre: "Beta" }, { ...tier1(2), empresaNombre: "Alfa" }],
      pines: [{ ...google(3, 5), empresaNombre: "Zeta" }],
    }));
    expect(pines.map((p) => p.empresaNombre)).toEqual(["Zeta", "Alfa", "Beta"]);
  });
});

describe("bandeja única de pendientes", () => {
  const completa = () => componerBandeja(datos({
    estado: { sinCoordenadas: 4, estimacionGeocodificar: 4 } as EstadoAsistenteKm,
    propuestas: [{ tablaKmId: "t1", empresaNombre: "ACME", sucursalNombre: "Centro", candidatos: [] } as PropuestaN2Match],
    noEncontradas: [
      { empresaNombre: " acme ", sucursalNombre: "CENTRO" },
      { empresaNombre: "Otra", sucursalNombre: "Norte" },
    ],
    coordenadas: [coord(10, "ambigua"), coord(11, "sin_resultados"), coord(12, "sin_direccion"), coord(13, "resuelta")],
    tier1b: [tier1b(1)],
    worklist: { certezaAbsoluta: [], requiereVerificacion: [worklistItem(20, []), worklistItem(21, [])], estimacionLlamadasGoogle: 2 },
  }));

  it("presenta primero lo roto con certeza, después decisiones, bloques y al final lo manual", () => {
    expect(completa().map((i) => i.tipo)).toEqual([
      "pin_roto", "nombre_candidato", "ubicacion_elegir", "pines_verificar", "sin_ubicacion",
      "ubicacion_sin_resultado", "ubicacion_sin_resultado", "nombre_sin_candidato",
    ]);
  });

  it("no lista como 'sin candidato' una fila que ya tiene propuesta, aunque difiera en mayúsculas o espacios", () => {
    const sinCandidato = completa().filter((i) => i.tipo === "nombre_sin_candidato");
    expect(sinCandidato.map((i) => i.key)).toEqual(["n1-otra::norte"]);
  });

  it("filtra por categoría", () => {
    const items = completa();
    expect(filtrarBandeja(items, "todos")).toHaveLength(items.length);
    expect(filtrarBandeja(items, "pines").map((i) => i.tipo)).toEqual(["pin_roto", "pines_verificar"]);
    expect(filtrarBandeja(items, "nombres")).toHaveLength(2);
    expect(filtrarBandeja(items, "ubicaciones")).toHaveLength(4);
  });

  it("resume conteos y exige atribución de OSM si hay evidencia de dos fuentes", () => {
    expect(resumirBandeja(completa())).toEqual({
      pinesRotos: 1, paraGestion: 1, nombres: 2, ubicaciones: 3, pinesPorVerificar: 2, sinUbicacion: 4, muestraOsm: true,
    });
  });

  it("no agrega bloques vacíos ni atribución OSM sin datos", () => {
    const items = componerBandeja(datos());
    expect(items).toEqual([]);
    expect(resumirBandeja(items).muestraOsm).toBe(false);
  });
});

describe("aviso de pendientes que dejan sucursales sin km", () => {
  const r = (over: Partial<ReturnType<typeof resumirBandeja>>) => ({
    pinesRotos: 0, paraGestion: 0, nombres: 0, ubicaciones: 0, pinesPorVerificar: 0, sinUbicacion: 0, muestraOsm: false, ...over,
  });

  it("no avisa si no queda nada que deje sucursales sin km", () => {
    expect(consecuenciaPendientes(r({ pinesRotos: 5, pinesPorVerificar: 3 }))).toBeNull();
  });

  it("enumera lo pendiente en singular", () => {
    expect(consecuenciaPendientes(r({ nombres: 1, ubicaciones: 1, sinUbicacion: 1 }))).toBe(
      "Quedan 1 nombre sin confirmar, 1 ubicación sin elegir, 1 sucursal sin ubicación: esas sucursales van a quedar SIN km cuando calcules.",
    );
  });

  it("enumera lo pendiente en plural", () => {
    expect(consecuenciaPendientes(r({ nombres: 2, sinUbicacion: 3 }))).toBe(
      "Quedan 2 nombres sin confirmar, 3 sucursales sin ubicación: esas sucursales van a quedar SIN km cuando calcules.",
    );
  });
});
