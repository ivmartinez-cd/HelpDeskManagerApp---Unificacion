"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { SortState } from "@/shared/hooks/use-table-sort";

export interface SortableColumn<K extends string> {
  key: K;
  label: string;
  className?: string;
}

interface SortableHeaderProps<K extends string> {
  column: SortableColumn<K>;
  sort: SortState<K>;
  onToggleSort: (key: K) => void;
  thClassName?: string;
}

export function SortableHeader<K extends string>({
  column,
  sort,
  onToggleSort,
  thClassName = "px-4 py-3",
}: SortableHeaderProps<K>) {
  const active = sort.key === column.key;
  const Icon = !active ? ChevronsUpDown : sort.direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <th
      scope="col"
      aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
      className={cn(thClassName, column.className)}
    >
      <button
        type="button"
        onClick={() => onToggleSort(column.key)}
        className={cn(
          "inline-flex cursor-pointer items-center gap-1 uppercase tracking-wide transition-colors hover:text-foreground",
          active && "text-brand-orange",
        )}
      >
        {column.label}
        <Icon className={cn("h-3 w-3", !active && "opacity-40")} aria-hidden="true" />
      </button>
    </th>
  );
}
