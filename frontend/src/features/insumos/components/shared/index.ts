/** Primitivos compartidos del módulo Insumos — los consume más de una
 * pantalla, por eso viven acá y no duplicados por feature.
 *
 * `import { StatusBadge, TonerBar } from "@/features/insumos/components/shared"`
 */
export { ConfirmationModal, type ConfirmationVariant } from "./confirmation-modal";
export {
  DateRangePicker,
  rangeForPreset,
  type DateRangePresetKey,
} from "./date-range-picker";
export { DateRangePickerPopover } from "./date-range-picker-popover";
export { SortableHeader, type SortableColumn } from "./sortable-header";
export { StatusBadge, toneForStatusKey, type StatusTone } from "./status-badge";
export { TonerBar, tonerLevelColor, type TonerBarSize } from "./toner-bar";
export {
  TrendChart,
  type TrendAnnotation,
  type TrendPeriodOption,
} from "./trend-chart";
