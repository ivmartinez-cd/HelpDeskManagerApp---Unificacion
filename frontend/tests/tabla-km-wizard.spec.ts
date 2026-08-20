import { test, expect, type Page } from "@playwright/test";

/** Asistente de KM (rediseño 2026-08-20): intro → chequeos → Traer de Gestión →
 * bandeja única. Todo mockeado: no toca backend real ni Google. */

const PID = "aaa";
const PRESTADORES_MOCK = [
  { id: PID, nombre: "San Juan - Gestion Integral", nombreCorto: "SAN JUAN", cuit: null, region: "SAN JUAN", activo: true, sigesEmpresaId: 504, cdPrestadorId: null, sigesBaseSucursalId: 2649, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];
const TABLA_KM_MOCK = [
  { id: "1", prestadorId: PID, spstId: null, empresaNombre: "Gobierno de San Juan", sucursalNombre: "Escuela 20 de Junio", observaciones: null, domicilioCliente: "La Madrid y Mendoza S/N", localidadCliente: "SAN JUAN", provinciaCliente: "San Juan", kmsRecorrido: 0, umbralViatico: 30, aplicaViatico: false, kmsAFacturar: 0, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];
const ESTADO = {
  vinculadoSiges: true, baseConfigurada: true, baseConCoordenadas: true, sucursalesActivas: 2, exClientes: 1,
  sucursalesNuevasPorImportar: 1, filasTablaKm: 1, sinCoordenadas: 1, ambiguasPendientes: 1, filasSinKm: 1,
  noEncontradasEnSiges: 1, pinesSospechososCacheados: 1, estimacionGeocodificar: 1, estimacionDistancias: 4,
  estimacionAuditarPines: 3, topePorCorrida: 200,
};
const SUCURSALES = [
  { sigesSucursalId: 1, empresaNombre: "Gobierno de San Juan", sucursalNombre: "Escuela 20 de Junio", domicilio: "La Madrid y Mendoza S/N", localidad: "SAN JUAN", provincia: "San Juan", yaCargada: true, actividadReciente: true },
  { sigesSucursalId: 2, empresaNombre: "CEVA", sucursalNombre: "San Juan", domicilio: "Ruta 40 km 1", localidad: "SAN JUAN", provincia: "San Juan", yaCargada: false, actividadReciente: true },
  { sigesSucursalId: 3, empresaNombre: "Ex Cliente SA", sucursalNombre: "Depósito", domicilio: null, localidad: null, provincia: null, yaCargada: false, actividadReciente: false },
];
const PROPUESTAS = [{
  tablaKmId: "1", empresaNombre: "Gobierno de San Juan", sucursalNombre: "Escuela ANTONIO QUARANTA",
  candidatos: [
    { sigesSucursalId: 10, sucursalNombre: "Escuela Antonio Pulenta", domicilio: "Laprida e Independencia S/N", score: 0.65, motivo: "difieren en — local trae: quaranta; Siges trae: pulenta" },
    { sigesSucursalId: 11, sucursalNombre: "Escuela Antonio Torres", domicilio: "General Acha 426", score: 0.57, motivo: "difieren en — local trae: quaranta; Siges trae: torres" },
  ],
}];
const COORDENADAS = [{
  sigesSucursalId: 20, empresaNombre: "Cepas Argentinas", sucursalNombre: "San Juan", direccion: "Rastreador Calivar 239, SAN JUAN",
  estado: "ambigua", latitud: null, longitud: null, procedencia: null, formattedAddress: null,
  candidatos: [
    { formattedAddress: "Rastreador Calivar Nte. 239, Rivadavia", latitud: -31.5279, longitud: -68.5947, locationType: "ROOFTOP", tipos: [], partialMatch: false },
    { formattedAddress: "Rastreador Calivar Sur 239, Rivadavia", latitud: -31.5326, longitud: -68.594, locationType: "RANGE_INTERPOLATED", tipos: [], partialMatch: false },
  ],
}];
const TIER1B = [{ sigesSucursalId: 2, empresaNombre: "CEVA", sucursalNombre: "San Juan", provinciaDeclarada: "San Juan", provinciaGeoref: "La Pampa", provinciaNominatim: "La Pampa", latitud: -38.416, longitud: -63.616, atribucion: "Data © OpenStreetMap contributors, ODbL 1.0" }];
const TIER1 = TIER1B.map(({ provinciaNominatim: _n, atribucion: _a, ...h }) => h);
const WORKLIST = {
  certezaAbsoluta: [{ sigesSucursalId: 1, empresaNombre: "Gobierno de San Juan", sucursalNombre: "Escuela 20 de Junio", domicilio: "La Madrid y Mendoza S/N", motivos: ["fuera_de_argentina"], latitud: 40.4167, longitud: -3.7032 }],
  requiereVerificacion: [
    { sigesSucursalId: 30, empresaNombre: "Disco", sucursalNombre: "SM 193", domicilio: "Av. Libertador 2359", motivos: ["pin_compartido"], latitud: -31.52, longitud: -68.56 },
    { sigesSucursalId: 31, empresaNombre: "Disco", sucursalNombre: "SM 412", domicilio: "Av. Libertador 5091", motivos: ["pin_compartido"], latitud: -31.52, longitud: -68.56 },
  ],
  estimacionLlamadasGoogle: 2,
};
const PINES = [{ sigesSucursalId: 40, empresaNombre: "Gobierno de San Juan", sucursalNombre: "ENI N.º 65", direccion: "Rio Gallegos S/N 52, CHIMBAS", latitudSiges: -31.49, longitudSiges: -68.53, latitudGeocode: -51.62, longitudGeocode: -69.21, formattedAddress: "Rio Gallegos, Santa Cruz", locationType: "APPROXIMATE", discrepanciaKm: 2239.026 }];

const page1 = <T,>(items: T[]) => ({ items, total: items.length, page: 1, size: 1000 });
const json = (body: unknown) => ({ status: 200, contentType: "application/json", body: JSON.stringify(body) });

async function mockear(page: Page, escrituras: string[]) {
  await page.route("**/api/**", (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const p = url.pathname;
    if (req.method() !== "GET") escrituras.push(`${req.method()} ${p}`);
    if (p.endsWith("/api/liquidaciones/prestadores")) return route.fulfill(json(page1(PRESTADORES_MOCK)));
    if (p.endsWith("/api/liquidaciones/tabla-km")) return route.fulfill(json(page1(TABLA_KM_MOCK)));
    if (p.endsWith("/api/liquidaciones/spsts")) return route.fulfill(json(page1([])));
    if (p.endsWith("/asistente-km/estado")) return route.fulfill(json(ESTADO));
    if (p.endsWith("/siges/sucursales")) return route.fulfill(json({ items: SUCURSALES, total: SUCURSALES.length, page: 1, size: 200 }));
    if (p.endsWith("/matching/propuestas")) return route.fulfill(json(PROPUESTAS));
    if (p.endsWith("/coordenadas")) return route.fulfill(json(page1(COORDENADAS)));
    if (p.endsWith("/geovalidacion/tier0")) return route.fulfill(json(page1([])));
    if (p.endsWith("/geovalidacion/tier1")) return route.fulfill(json(page1(TIER1)));
    if (p.endsWith("/geovalidacion/tier1b")) return route.fulfill(json(page1(TIER1B)));
    if (p.endsWith("/geovalidacion/worklist")) return route.fulfill(json(WORKLIST));
    if (p.endsWith("/pines-sospechosos")) return route.fulfill(json(page1(PINES)));
    if (p.endsWith("/consultar-georef")) return route.fulfill(json({ consultadas: 0, yaEnCache: 3, sinCoordenadas: 0, pendientesPorTope: 0 }));
    if (p.endsWith("/consultar-nominatim")) return route.fulfill(json({ consultadas: 0, yaEnCache: 1, pendientesPorTope: 0 }));
    return route.continue();
  });
}

async function setFakeSession(page: Page) {
  await page.context().addCookies([{ name: "hdm_session", value: "test-session-token", domain: "localhost", path: "/", httpOnly: true, secure: false }]);
}

test("asistente de KM: intro, chequeos gratis, Traer de Gestión y bandeja única", async ({ page }) => {
  await setFakeSession(page);
  const escrituras: string[] = [];
  await mockear(page, escrituras);

  await page.goto("/liquidaciones/configuracion/tabla-km");
  await page.waitForLoadState("networkidle");
  await page.selectOption('select[aria-label="Filtrar por PST"]', PID);
  await page.getByRole("button", { name: /Asistente de KM/ }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Este asistente deja tu Tabla KM al día en tres momentos:")).toBeVisible();
  await expect(dialog.getByText("Nada consulta Google sin mostrarte antes cuántas consultas cuesta.")).toBeVisible();
  await page.screenshot({ path: "test-results/tabla-km-wizard-intro.png" });

  await dialog.getByRole("button", { name: "Empezar" }).click();
  // Momento 1 con los conteos completos de Gestión (paginación de a 200).
  await expect(dialog.getByText("Gestión tiene 2 sucursales activas de este prestador.", { exact: false })).toBeVisible();
  await expect(dialog.getByText("importar 1 sucursal nueva con actividad")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Traer de Gestión", exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/tabla-km-wizard-traer.png" });

  // Tras "Empezar" solo corrieron los chequeos gratis: nada escribió en la Tabla KM.
  expect(escrituras.filter((e) => !e.includes("/consultar-"))).toEqual([]);

  // Bandeja única: pines rotos primero, después decisiones, atribución ODbL visible.
  await dialog.getByRole("button", { name: /Revisar pendientes/ }).click();
  await expect(dialog.getByText("El pin está fuera de Argentina")).toBeVisible();
  await expect(dialog.getByText("El pin está en La Pampa, pero su dirección dice San Juan. Dos fuentes independientes lo confirman.")).toBeVisible();
  await expect(dialog.getByText(/2239 km de la dirección escrita/)).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Usar la dirección escrita" })).toBeVisible();
  await expect(dialog.getByText('¿"Escuela ANTONIO QUARANTA" es esta sucursal de Gestión?')).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Sí, es esta" })).toHaveCount(1);
  await expect(dialog.getByText("Datos de mapa © OpenStreetMap contributors (ODbL)")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Exportar CSV para Gestión" })).toBeVisible();
  // Nada de jerga técnica en la vista por defecto.
  await expect(dialog.getByText(/Tier|Georef|Nominatim|worklist/)).toHaveCount(0);
  await page.screenshot({ path: "test-results/tabla-km-wizard-bandeja.png" });

  // Filtro: solo nombres.
  await dialog.getByRole("radio", { name: "Nombres" }).click();
  await expect(dialog.getByText("El pin está fuera de Argentina")).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: "Sí, es esta" })).toHaveCount(1);
});
