# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project

Personal fitness plan tracker. Single-page apps that run entirely in the browser — no build step, no backend, no dependencies. Open the HTML file directly to use.

- `fitness_plan.html` — the main app: weekly meal plan, recipes, workouts, grocery list, low-motivation cards.
- `tictactoe.html` — standalone game (unrelated to fitness).

## How to run

Open `fitness_plan.html` in any modern browser. There is no build, lint, or test pipeline. To preview changes, reload the file. State persists in `localStorage` under key `fitnessPlan_v1` and is per-device.

## Architecture (`fitness_plan.html`)

Self-contained HTML with `<style>` and `<script>` blocks. The JS is roughly organized into:

- **Constants:** `WORKOUTS`, `RECIPES`, `SECTION_ORDER`, `ING_SECTIONS`. `RECIPES` is the canonical built-in list — never mutate it at runtime.
- **State (`S`):** loaded from `localStorage` on `DOMContentLoaded`, saved on every mutation via `saveState()`. Shape includes:
  - `selectedMeals`, `mealLog`, `groceryChecked`, `customGroceryItems`, `hideChecked`
  - `customRecipes` — user-added recipes (full objects)
  - `recipeEdits` — overrides for built-in recipes, keyed by recipe id (only changed fields stored)
  - `mealPlanEdits` — overrides for meal plan rows, keyed by `<meals-list-id>-<rowIdx>` with `{desc, cal}`
  - `exerciseSettings` — per-day per-exercise `{sets, reps, weight, notes}`
  - `exerciseNameEdits` — overrides for exercise names, keyed by `<day>-<idx>`
  - `workoutLog` — daily workout completion
- **Renderers:** `renderWorkouts()`, `renderRecipes()`, `renderGrocery()` rebuild their sections from `S` + constants. Always re-render after mutating state.
- **Editing:**
  - Recipes: pencil icon opens the modal (`openRecipeModal`); built-ins write to `S.recipeEdits`, customs write to `S.customRecipes`. ↺ resets a built-in by deleting its override.
  - Meals: click `.meal-desc` or `.meal-cal` (in non-`.no-cb` rows) → inline input/textarea. Day total kcal auto-recomputes. Description edits with a single number diff also auto-scale the kcal proportionally (`inferScaleRatio`).
  - Workouts: click name, sets/reps/weight, or notes inline (`startEditCell`).
- **Grocery aggregation:** `computeGrocery()` walks `selectedMeals`, looks up recipes via `getEffectiveRecipe()` (base + edits), and merges ingredients by `normalizeIngName(name) + normalizeUnit(unit) + section`. Both helpers strip parentheticals, plurals, and "extra-virgin" so variants merge cleanly.
- **Display formatting:** `fmtIng()` renders ingredients; items with no unit (`-` or empty) show `(Nx)`, e.g. `Eggs (2x)`.

## Conventions

- Prefer editing the existing const arrays for new built-in content (recipes, workouts) rather than introducing new state.
- When adding a recipe to `RECIPES`, also add its id to the appropriate category in the `cats` array inside `renderRecipes()`.
- Don't add comments that just restate what the code does. Add a short comment only when the *why* is non-obvious.
- Keep changes scoped — one logical change per commit.

## Git / GitHub workflow

The repo lives at `https://github.com/Fremzies/fitness-plan` (private, owner `Fremzies`). The user works from this on multiple devices and treats GitHub as the source of truth.

- Make a clean commit for each meaningful change; descriptive messages focused on the *why*.
- Push to `origin/main` after each commit so the user can pull from any device.
- Don't batch unrelated changes.
- The git identity is set locally in this repo (not globally) — don't change global git config.
- `.gitignore` excludes `.DS_Store`, `.claude/settings.local.json`, and the `fitness_plan copy*.html` local snapshots.

## Editing model — important

- Built-in recipes (`RECIPES` const) and built-in workouts/meal-plan HTML are **never mutated at runtime**. User edits live in localStorage overrides (`recipeEdits`, `mealPlanEdits`, `exerciseNameEdits`).
- Edits do NOT sync across devices automatically — they're per-device localStorage.
- An export-to-HTML feature (bake overrides back into the source file for cross-device sync via git) is on the backlog but not implemented.
