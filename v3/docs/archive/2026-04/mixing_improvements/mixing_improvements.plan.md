# Mixing Improvements Plan

Author: Codex  
Status: In Progress  
Last Updated: 2026-02-05

## 1. Objective
- Align work-time behavior with “disabled by default, opt-in to include time”.
- Make LOT auto-assign robust against invalid/empty work date.
- Clarify post-save reset behavior and reduce accidental repeat saves.
- Strengthen input validation for actual amounts.

## 2. Scope
### In Scope
- Work-time include flag default and persistence behavior.
- Auto-assign date validation and failure handling.
- Post-save UI reset rules.
- Validation of actual amount vs. required.

### Out of Scope
- DB schema changes.
- Business logic changes beyond UI behavior and validation.

## 3. Plan
1. Define expected user flows for work-time, auto-assign, save/reset.
2. Map changes to existing panels/controllers.
3. Review edge cases and propose test matrix.

## 4. Risks
- Changing defaults may surprise existing users.
- Over-strict validation may block valid data entry.

## 5. Definition of Done
- Design doc approved.
- Validation rules and reset behavior explicitly documented.
