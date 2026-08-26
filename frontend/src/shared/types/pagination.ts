/** Envelope de paginación que devuelve todo endpoint de colección del backend
 * (ver `Page[T]` en `src/shared/presentation/schemas/pagination.py`). */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
