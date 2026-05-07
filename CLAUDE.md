# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project

Personal fitness plan tracker. Single-page apps that run entirely in the browser — no build step, no backend, no dependencies. Open the HTML file directly to use.

- `fitness_plan.html` — the main app: weekly meal plan, recipes, workouts, grocery list, low-motivation cards.
- `sync.py` — local helper that bakes in-browser edits into the HTML and pushes to GitHub. Stdlib-only Python. Auto-exits after 10 min idle.
- `start.command` — double-click in Finder to start `sync.py` (if not running) and open the page. The user's normal entry point.
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

**Commit and push as you work — don't wait until the end of a task.** Every meaningful change must be committed locally and pushed to `origin/main` before moving on, so the user never loses progress and can revert any individual change cleanly.

- Make a clean commit for each meaningful change; descriptive messages focused on the *why*, not just the *what*.
- Push to `origin/main` immediately after each commit. Don't accumulate unpushed commits.
- One logical change per commit. Don't batch unrelated edits, even if they're small.
- If a single user request spans multiple logical changes (e.g., "add recipes + fix grocery dedup + remove a note"), make a separate commit for each.
- The git identity is set locally in this repo (not globally) — don't change global git config.
- `.gitignore` excludes `.DS_Store`, `.claude/settings.local.json`, and the `fitness_plan copy*.html` local snapshots.
- Never force-push to `main`, never amend pushed commits, never skip hooks.

## Backlog

Things flagged by the user that aren't done yet. Pick these up when the user
returns to them — don't proactively implement without confirmation.

- **Reordering** — drag-and-drop to move meals between days (and likely
  reorder recipes within a category, exercises within a workout). Will need
  pointer-based DnD that works on iOS Safari (touch events, not just HTML5
  DnD). Track ordering as an array of ids in `S.mealPlanOrder` etc., applied
  during render. Don't break the existing `mealPlanEdits` row-key scheme.
- **Cross-unit grocery aggregation** — current `computeGrocery()` merges only
  when normalized name+unit match. Items like "Olive oil (2 tbsp)" + "Olive
  oil (¼ cup)" stay split. The user wants them combined: convert all volumes
  to a common base (e.g. ml or tbsp), sum, then display in the most natural
  unit. Mass needs the same treatment. Counted items (`unit: 'x'` / `'-'`)
  stay separate. Avoid converting across volume↔mass unless we add per-
  ingredient density data — for now, mixed systems should display as
  "X cups + Y oz" rather than incorrectly converting.
- **Day-card → workout jump** — clicking a day card in the Schedule section
  should open the matching workout `<details>` (push/pull/legs) and scroll
  it into view. Each day card already has the workout class baked in
  (`.day-card.push/.pull/.legs/.pottery/.rest`); rest/pottery cards should
  no-op or just open Schedule. Add an `onclick` that finds
  `#workout-<class>`, ensures the workouts section `<details>` is open,
  then `scrollIntoView({ behavior: 'smooth' })`. Small change — but mind
  that the workouts section itself is a `<details>` that may be collapsed.

## Editing model — important

- Built-in recipes (`RECIPES` const) and built-in workouts/meal-plan HTML are **never mutated at runtime**. User edits live in localStorage overrides (`recipeEdits`, `mealPlanEdits`, `exerciseNameEdits`).
- Edits sync to GitHub via `sync.py` (see below). Without it running, edits are per-device.

## Cross-device sync (`sync.py`)

In-browser edits travel to GitHub through this loop:

1. The HTML page contains a `<script type="application/json" id="user-data">` block.
2. The page POSTs the user's localStorage state to `http://localhost:7777/sync` whenever they click **Save Changes**, and on a 3-second debounce after every edit.
3. `sync.py` writes the payload into the data block, runs `git add`, `git commit`, `git push origin main`.
4. On another device, after `git pull`, the page's `loadState()` reads the embedded block as a fallback when localStorage is empty — picking up the edits seamlessly.

To use:
- **Normal flow:** double-click `start.command` in Finder. It launches `sync.py` if not already running, then opens `fitness_plan.html` in the default browser. Safe to run repeatedly.
- **Manual flow:** `python3 sync.py` from a terminal.

The page sends a heartbeat to `http://localhost:7777/heartbeat` every 60 seconds while the tab is visible. `sync.py` auto-exits after 10 minutes without a heartbeat — closing the tab or walking away reclaims the port. Reopening means running `start.command` again.

`sync.py` only ever modifies `fitness_plan.html` and only ever commits with the message `Sync user edits from browser`. If the helper is offline, edits stay in localStorage until you start it again.

What gets synced (`buildSyncPayload` in the HTML):
- `selectedMeals`, `customRecipes`, `customGroceryItems`
- `recipeEdits`, `mealPlanEdits`, `exerciseSettings`, `exerciseNameEdits`

What stays per-device (intentionally not synced — it's session state, not data):
- `mealLog` (today's eaten meals), `workoutLog` (today's done sets), `groceryChecked` (today's shopping checks), `hideChecked` (UI toggle)
