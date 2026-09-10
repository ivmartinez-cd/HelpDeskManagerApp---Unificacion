/** Un cambio que el prestador aplicó sobre una liquidación ya importada — ver
 * ADR-038 y `ModificacionOut` en el backend. */
export interface ModificacionPrestador {
  id: string;
  liquidacionId: string;
  numeroLiquidacion: string | null;
  numeroIncidente: string;
  tipoCambio: "alta" | "baja" | "modificacion";
  campo: string | null;
  valorAnterior: string | null;
  valorNuevo: string | null;
  detectadaEn: string;
  vistaEn: string | null;
}
