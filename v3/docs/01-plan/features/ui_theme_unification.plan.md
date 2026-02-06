# UI Theme Unification Plan

Author: Codex  
Status: In Progress  
Last Updated: 2026-02-04

## 1. Objective
- Remove hardcoded colors from UI components and unify styling through `UITheme`/`UIStyles`.
- Improve text/input visibility consistency to prevent “invisible label/placeholder” issues.
- Enable easy future theme swap (e.g., mint theme) with minimal edits.

## 2. Scope
### In Scope
- Replace inline `#hex`/`rgba()` colors in UI modules with `UITheme` tokens.
- Centralize background/highlight colors for tables, dialogs, and panels.
- Adjust label/input styles to use `TEXT_PRIMARY` / `TEXT_SECONDARY`.

### Out of Scope
- Visual redesign or layout changes beyond color/style normalization.
- Business logic changes.

## 3. Plan
1. Inventory hardcoded styles in `v3/ui/**` and map to theme tokens.
2. Replace inline colors with `UITheme` constants and update affected styles.
3. Verify key screens: Mixing, Manual Input, Bulk Creation, DHR, Records, Settings.
4. Fix any visibility regressions.

## 4. Risks & Mitigations
- Risk: Style changes reduce contrast on some widgets.  
  Mitigation: Use `TEXT_PRIMARY` for labels and add fallback backgrounds for inputs.

## 5. Definition of Done
- No `#hex`/`rgba()` colors remain in UI modules outside `styles.py` (except tokens).
- Text and input fields are legible on all main screens.
- Screenshots confirm consistent theme usage.
