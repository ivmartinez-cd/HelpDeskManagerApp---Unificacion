/** Un comentario de la bitácora de Web Agentes de una liquidación — ver
 * `EntradaBitacoraOut` en el backend. `fecha` viene sin zona (hora de Siges,
 * Argentina) y el navegador la interpreta como local. */
export interface EntradaBitacora {
  id: number;
  fecha: string;
  usuario: string;
  autor: string | null;
  esCanal: boolean;
  texto: string;
}
