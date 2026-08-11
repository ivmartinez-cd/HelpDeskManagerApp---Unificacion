---
name: ui-design-handoff
description: Use this skill whenever building, migrating, or restyling UI for a business module in this HelpDeskManager-Unificacion monorepo — e.g. "migremos SDS Insumos", "portemos VacaSync/Calendario-Web", "hagamos la UI de Liquidacion-Prestadores", "pasemos Printer-Logs-Analyzer al padre", or any work under frontend/src/features/*, frontend/src/app/(app)/*. This project is a strangler-fig rewrite of 6 legacy apps into one Next.js + FastAPI stack, and every module being ported has (or should have) a pixel-fidelity design handoff prepared beforehand — never invent a visual design from scratch when a handoff exists or should exist. Also trigger for any request to "make it look like the old app", reskin a module, or apply brand/marca styling.
---

# UI design handoff for module migrations

This repo is unifying 6 legacy apps (HelpDeskManager-Web, SDSInsumos, Calendario-Web/VacaSync,
Liquidacion-Prestadores, Printer-Logs-Analyzer, STC Cloud) into one Next.js 15 + FastAPI stack.
Business logic gets re-characterized against the old app's real behavior (see
`INTEGRACION_APPS_PLAN.md` / `ARCHITECTURE_GUIDE.md` at the repo root), but the **UI is not
something to design fresh** — each module either already has, or needs, a hi-fi design handoff
that pins colors, typography, spacing and interactions to the real brand. Treat that handoff as
the source of truth the same way `CONTADORES_CARACTERIZACION.md` is the source of truth for
Contadores' business logic.

## 1. Find (or request) the handoff before writing any component

Design handoffs live in folders at the repo root named `design_handoff_<something>/` (e.g.
`design_handoff_mesa_de_ayuda/`), each with a `README.md`
describing screens/tokens/interactions plus the original static `.dc.html` reference files and
an `assets/` folder with the real exported PNGs/logos. Before touching UI for a module:

1. Search the repo root for a `design_handoff_*` (or similarly named) folder that matches the
   module you're building. If more than one candidate exists for the same app (this has happened
   before — a duplicate upload with an extra suffix), diff them; the more complete one usually has
   more screens documented.
2. Read that folder's `README.md` in full — tokens, screen-by-screen layout, interactions,
   assets — before writing or editing a single component. Skimming it leads to exactly the kind
   of rework this project has already paid for once (see the "second pasada" pattern below).
3. **If no handoff exists yet for the app/module you're about to build UI for, stop and ask the
   user for one** (or for the brand manual / reference screenshots) instead of guessing colors,
   spacing, or layout. This project's whole design language comes from the client's real brand
   manual, not from generic SaaS defaults — inventing "reasonable-looking" UI here has been
   explicitly rejected before.

## 2. Recreate, don't copy

The `.dc.html` files are static HTML/CSS/JS references, not production code. The task is to
**recreate** that design inside the real stack — real routing, real state, real API calls to the
already-migrated backend — never to ship the reference HTML as-is or wire it to fake data. Reuse
whatever primitives already exist in `frontend/src/shared/components/ui/` before adding new ones;
extend that shared system rather than reimplementing a button/modal/input inside a feature folder.

## 3. Brand purity

This client (Canal Directo) has multiple business lines with distinct brand colors, but only the
**Institucional** line applies to this app: naranja `#F7941D` and gris `#58595B`. Other lines that
appear in the client's brand manual — violeta `#662D91` (DaaS), celeste `#3DB1CA` (Cartelería
Digital / Digital Signage), magenta `#E32D91` (Digitalización) — are **excluded on purpose**, per
an explicit client decision. Don't reach for them as "just an accent" even if a handoff mockup
happens to show one (flag it to the user instead of copying it silently — this has already
happened once with a magenta notification dot and an "Alta" badge that got recolored to orange).

## 4. Known traps in this codebase's design system

These have each cost a rework pass already — check for them proactively instead of rediscovering
them:

- **`rounded-lg`/`rounded-md`/`rounded-sm` are not 8/6/4px here.** They're remapped to
  `var(--radius)` (24px, see `--radius` in `frontend/src/app/globals.css`) for the app's default
  "chunky" look. For pixel fidelity to a handoff, always use arbitrary values (`rounded-[8px]`,
  `rounded-[12px]`, `rounded-[16px]`...), never the semantic Tailwind names.
- **The app runs dark-by-default** (`.dark` class on `<html>`). Any shared primitive that uses
  dark-aware tokens (`bg-background`, `text-muted-foreground`, `dark:` variants —
  `shared/components/ui/{input,button,modal}.tsx` etc.) will render dark **even inside a
  container whose own background is forced to white**, because `dark:` depends on the class on
  `<html>`, not on an ancestor's inline style. For a brand surface that must always look light
  regardless of the app's theme, build/use literal, non-dark-aware primitives instead (see
  `frontend/src/shared/components/ui/brand-form.tsx` and `brand-modal.tsx` for the established
  pattern: `BrandInput`, `BrandFileInput`, `BrandButton`, `BrandModal`, etc.). Don't assume
  forcing a parent's background is enough to isolate children from the theme.
- **Verify the frontend's response types against what the backend actually serializes**, not
  against what an existing e2e test mocks. FastAPI schemas here often use
  `serialization_alias` (camelCase over the wire) — a frontend type that "looks right" but was
  never checked against a real backend response has caused a silent runtime crash before
  (`Cannot read properties of undefined`). Confirm field names live, e.g. with an authenticated
  Playwright pass or a direct API call, when wiring a new panel to a real endpoint for the first
  time.

## 5. Confirm behavior questions, don't assume

Handoffs describe visuals; they usually leave gaps for how a module's *real* interactive/business
behavior should map onto that visual (e.g. "should this legacy multi-page flow become one modal
or a stacked pair of modals?", "does this KPI tile need real data or is it a placeholder for now?").
When the handoff is ambiguous or its mockup implies functionality that doesn't exist yet
(fake ticket tables, placeholder KPIs), ask the user rather than inventing scope — this project's
history shows the user has specific, sometimes surprising preferences here (e.g. explicitly
rejecting fake dashboard data, explicitly choosing nested modals over a separate management page).

## 6. Record real decisions somewhere durable

If a session produces a non-obvious design decision (a scoping call, a deviation from the handoff,
a new shared primitive), make sure it ends up in this repo's own working docs
(`INTEGRACION_APPS_PLAN.md` or equivalent) — not only in chat — so the next session/module
migration doesn't have to rediscover it.
