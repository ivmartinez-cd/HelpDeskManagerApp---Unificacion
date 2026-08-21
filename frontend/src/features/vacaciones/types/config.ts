export interface SeniorityTier {
  minYears: number;
  maxYears: number;
  days: number;
}

export interface ConfigVacaciones {
  seniorityTiers: SeniorityTier[];
  nextYearOpenMonth: number;
  nextYearOpenDay: number;
  allowAdvanceRequest: boolean;
  maxAdvanceDays: number;
  allowCarryOver: boolean;
  maxCarryOverDays: number;
  minAdvanceNoticeDays: number;
  maxOverlapPercent: number;
  maxOverlapCount: number;
}

export type ConfigUpdatePayload = Partial<ConfigVacaciones>;

export interface Exclusion {
  id: string;
  empleadoAId: string;
  empleadoBId: string;
  empleadoANombre: string;
  empleadoBNombre: string;
}
