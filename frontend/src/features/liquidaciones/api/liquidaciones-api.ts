import { configApi } from "./config-api";
import { geolocalizacionApi } from "./geolocalizacion-api";
import { liquidacionesCoreApi } from "./liquidaciones-core-api";
import { matchingSucursalesApi } from "./matching-sucursales-api";
import { sigesApi } from "./siges-api";

/** API del feature, compuesta por sub-clientes por responsabilidad (espeja los
 * routers del backend). El objeto agregado conserva el contrato histórico para
 * los consumidores; código nuevo puede importar el sub-cliente que necesite. */
export const liquidacionesApi = {
  ...liquidacionesCoreApi,
  ...configApi,
  ...sigesApi,
  ...geolocalizacionApi,
  ...matchingSucursalesApi,
};
