export interface Feriado {
  id: string;
  name: string;
  date: string; // YYYY-MM-DD
  deductsVacation: boolean;
}

export interface FeriadoPayload {
  name: string;
  date: string;
  deductsVacation: boolean;
}

export interface ImportFeriadosResult {
  year: number;
  count: number;
  message: string;
}
