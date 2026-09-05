---
name: vinted-lister
description: >
  Creates a Vinted.de listing from an approved action file produced by the
  listing-drafter skill. Trigger this automatically after the listing-drafter
  has saved an action file and the user has approved the draft — whenever
  VINTED_APPLIES is "yes" in the action file. Also trigger when the user asks
  to proceed with, retry, or fix the Vinted part of a listing in progress.
  Skip entirely if VINTED_APPLIES is "no".
---

# Vinted Lister

<!-- PLUGIN_VERSION_LINE --> **Plugin version: 2.7.2.** This string is authoritative — use it verbatim for the action file's `PLUGIN_VERSION` and for the `feedback.md` header. A skill loaded via the Skill tool cannot see `.claude-plugin/plugin.json`, so do not try to read it and never guess a version from memory.

Your role: read the approved action file, fill in the Vinted listing form, and
save a draft. You make no content decisions — all approved content is in the
action file verbatim.

**Precondition — the action file must be validator-green.** Before touching the
browser, run
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_action_file.py" <path to listing.md>`
yourself. (If that path does not resolve, locate it once with
`find / -name validate_action_file.py -path '*plugin*' 2>/dev/null | head -1`.)
On exit 1, **stop and hand back to the drafter to fix the file** — do not list
from a failing action file, and do not "fix" listing content yourself here.
Do not assume the drafter ran the gate: between 2026-07-24 and 08-17, **none of
21 action files passed it** (2–18 errors each, 5 had no action file at all) and
every one of those listings still went live.

## Browser rules

**Chrome MCP only.** Use ONLY `mcp__Claude_in_Chrome__*` tools for all browser
work.

- Never use `mcp__computer-use__*` for any browser action.
- Never use clipboard (`write_clipboard` / `read_clipboard`) to transfer text
  into a browser. Use `mcp__Claude_in_Chrome__form_input` or
  `mcp__Claude_in_Chrome__javascript_tool` instead.
- If a Chrome MCP action fails, diagnose the issue — do not fall back to
  computer-use.

## Verification — prefer cheap JS reads over screenshots

Screenshots are expensive (each is a large image held in context). For **state
verification**, prefer a short `javascript_tool` snippet that returns text or
numbers over taking a screenshot:
- Checkbox / toggle state: `document.querySelector('sel').checked` → true/false
- Field value: `document.querySelector('sel').value`
- Selected option / label: read `.textContent` of the selected element
- Thumbnail / item count: `document.querySelectorAll('sel').length` → a number

Reserve screenshots for what a JS read genuinely can't capture: a final visual
confirmation, an unexpected error banner whose markup you can't predict, or
ambiguous rendering. Wherever this skill says "screenshot to confirm", a JS read
that returns the same fact is preferred unless a visual is specifically needed.
**Exception — the final package-size check (step 8) should still be a
screenshot**, because that field silently reverts and a visual is the reliable
last guard before saving.

## Safety rules

1. **Draft only.** Use "Entwurf speichern" — never click "Hochladen" (publishes
   immediately). The draft is saved as inactive under the seller's "Entwürfe"
   tab.
2. **No paid features.** Skip any promoted listing, boost, or "Extras" upsell.
3. **Minimal personal info.** Do not volunteer personal details beyond what the
   form requires.
4. **User-provided photos only.** Never use stock images or Vinted suggestions.

## Workflow

Read the action file before starting anything. If `VINTED_APPLIES` is `no`,
skip entirely.

**Resuming an interrupted session:** if you find yourself on a `/items/new` form
mid-run (e.g. after a context-compaction event), do **not** assume earlier fields
are filled. Re-verify **every** required field — Title, Kategorie, Marke, Zustand,
Farbe, Größe (apparel), Preis — before saving. The title field in particular can be silently empty
yet still let the draft save (Vinted tolerates an empty title in a draft), so an
interrupted run can produce a titleless draft if you don't re-check.

### 1. Navigate

Navigate to `https://www.vinted.de/items/new` (or the "Artikel verkaufen"
entry point from the Vinted homepage if the direct URL is unavailable).

`/items/new` sometimes lands on a **verification / loading screen** first, where
`find` reports none of the form fields. That is not a failure: wait a few
seconds and re-run `find` before concluding anything is wrong.

### 2. Title (fill this first)

**Set the title before category and details.** Vinted's title field is available
immediately on `/items/new`, and filling it first guards against an interrupted
run saving a titleless draft.

- **Title:** `VINTED_TITLE` if present in the action file; otherwise `ITEM_TITLE`.
  Both are pre-verified to fit Vinted's 50-character limit.

**Setting the title reliably.** Vinted's title field frequently **rejects typed
text** — `triple_click` + `type` leaves it empty because the ref targets the outer
wrapper, not the inner `<input>`. Use this
order and **verify `.value` after each step**:
1. **`mcp__Claude_in_Chrome__form_input` with the title field's `ref`** (from `find`
   / `read_page`) — the most reliable primitive; try it first.
2. If still empty, `triple_click` the field and `type` the title.
3. If still empty, focus the real input via JS, **coordinate-click the placeholder
   field**, then `type` again:
   ```js
   document.querySelector('input[name="title"], #title')?.focus();
   ```
Re-read `.value` after each attempt and stop once it holds the title — a titleless
draft can still save silently, so do not proceed until it is set. If it is **still
empty after all three attempts**, pause and tell the user rather than saving a
titleless draft.

### 3. Select category

**Prefer the category search field over manual drill-down.** The category picker
has a **"Finde eine Kategorie"** search box at the top. Typing the leaf name (the
last segment of `VINTED_CATEGORY`, e.g. "Sonstiges Zubehör") and picking the
matching full-path result is **far more reliable** than scrolling the drill-down
tree. Verify the chosen
result's full path matches `VINTED_CATEGORY` (or its closest valid leaf) before
accepting.

**Re-locate the category field immediately before clicking it.** The form's
layout shifts as fields fill (the description textarea grows), so a position
remembered from an earlier screenshot goes stale and the click lands on the
wrong element. Take a fresh
screenshot or `find` right before the click. **If the dropdown did not open,
the typed search text lands in the description** (a stray "ö" at the end of the
body, 2026-08-27) — after every type into the category search, read the
description's last characters back and strip anything that is not yours.

**Re-typing can commit the wrong suggestion.** When you type into the search
field a second time (e.g. after a no-result first query), the stale result
list's **top entry can get accepted mid-typing**. After every selection —
especially after a corrected search — **read back which leaf is actually
selected** and fix it before moving on.

**Drill-down (fallback).** If the search box is unavailable or returns no usable
match, use `VINTED_CATEGORY` to navigate Vinted's drill-down panel manually.
Subcategories with `>` drill deeper; leaf nodes (which load detail fields) are
radio buttons — click to select.

Vinted often auto-suggests a category when the item title contains a known
product type. Accept the suggestion if it matches `VINTED_CATEGORY` exactly.

**Internal-scroll fallback:** Category lists can be long. If the target
category row is not visible, **scroll the list element itself** — not the
outer page. The list container is typically a `ul` with class
`web_ui__List__width-parent` or similar. Use `mcp__Claude_in_Chrome__javascript_tool`
to scroll the container if `find` does not reveal the row:
```js
document.querySelector('ul.web_ui__List__width-parent').scrollBy(0, 400);
```
Repeat until the row is visible, then click it. Do not attempt to page-scroll
past the category picker — it does not work.

**Page-scroll trap (description textarea).** When scrolling the whole form, wheel
scroll frequently gets captured by the description `<textarea>` and the page
stops moving. Scroll at the **right edge of the viewport (x ≈ 1350)**, away from
the textarea, to move the page reliably.

**Leaf-not-found fallback.** The drafter cannot know Vinted's exact taxonomy for
every item, so the `VINTED_CATEGORY` leaf may not exist verbatim. If the named
leaf is absent under its parent, **read the available sibling leaves and pick the
closest match** rather than aborting — e.g. a two-piece suit → `Anzugsets`. Note
the substitution in the run feedback so the drafter's leaf list can be corrected.
Only ask the user if no sibling is a reasonable match.

**Select the final category once.** The category picker can become sticky and
stop reopening reliably after repeated edits. Choose the correct leaf on the
first attempt; don't exploratory-switch categories mid-run.

**Important:** Clicking a category for the first time on an account may trigger
an email verification flow. If a verification redirect occurs, pause and tell
the user to complete verification in account settings, then return here and
restart from step 1.

### 4. Fill Artikeldetails

After category selection, Vinted loads additional detail fields via an async
API call. **Wait 10–15 seconds** for them to appear before proceeding. The
fields are category-dependent — only fill what is actually present in the form.
A category can require a field the action file has no counterpart for (Tablets:
**Speicher**). Fill it from the description or product knowledge when the value
is certain, and name it in the summary; if it is not derivable, ask.

Typical fields and how to fill them:

**Marke:**
1. Click the Marke row to open the dropdown. **The search input does NOT
   auto-focus** — and a coordinate click + `type` can fail to register.
   **Prefer `form_input` with the "Marke
   suchen" input's `ref`** (from `find`) to enter `VINTED_BRAND` — it is more
   reliable than clicking in and typing.
2. Enter `VINTED_BRAND` from the action file, then **verify the input's `.value`
   actually holds it** (read the field); if empty, click directly into the input
   and retype once (or re-run `form_input` with a fresh ref).
3. Wait ~1–2 seconds for results. **`form_input` sets the value without always
   triggering Vinted's search debounce** — the list then shows "Keine Artikel
   gefunden" and, crucially, no "als Markenname nutzen" entry, even for a brand
   that would match. If that happens, `triple_click` the input and `type` the
   brand instead; the real keystrokes fire the debounce and the entry appears.
4. If the brand appears, click the matching result. **Do not accept a fuzzy
   near-match** — searching "Leicke" returned LEICESTER TIGERS, Leclerc and Foot
   Locker on 2026-08-14. If nothing matches the brand exactly, treat it as "no
   match" and use the fallback below.
5. **If no match is found,** follow `VINTED_BRAND_FALLBACK` from the action file.
   Do not leave Marke blank.
   - `Markenname nutzen` → after typing `VINTED_BRAND`, the result list offers a
     **"„[Marke]" als Markenname nutzen"** entry (use the typed text as a custom
     brand name). This is the right path for a real brand that simply isn't in
     Vinted's database (e.g. niche manufacturers). **Click it via a JS
     textContent match — this is more reliable than scrolling to it:**
     ```js
     [...document.querySelectorAll('li, [role="option"], button, div')]
       .filter(el => el.textContent.includes('als Markenname nutzen'))
       .sort((a, b) => a.textContent.length - b.textContent.length)[0]
       ?.click();
     ```
     (The entry's text contains the typed brand plus "als Markenname nutzen";
     matching on that suffix avoids quote/spacing mismatches. **Include `div`** —
     in practice the entry renders as a plain `div`, not an `li`/`button`. Picking
     the **shortest** matching element clicks the innermost wrapper, not a large
     parent div that swallows the click with no effect.)
     If the click has no visible effect, fall back to a coordinate click on the
     visible entry in the open dropdown.
   - `Keine Marke erkannt` / `Keine Marke` → select that entry from the result
     list (for items with genuinely no brand).
6. If an "Echtheitsnachweis" authenticity notice appears — whether inline under
   the brand field or as a modal dialog — dismiss it:
   - Modal: click "Okay, schließen" or the equivalent close button.
   - Inline: acknowledge/close the banner and continue.

**Plattform** (gaming/platform-specific categories only, when field is present):
1. Click the Plattform row to open the dropdown.
2. **Click the search input inside the dropdown** (it does not auto-focus).
3. Type `VINTED_PLATFORM` from the action file and wait ~2 seconds for results.
4. Click the result.
5. If `VINTED_PLATFORM` is `NONE`, skip this field.

**Selecting options in Zustand/Farbe dropdowns — primary method.** Each option is
an `<li>` that also wraps its **own description text**, so matching on the exact
label (`textContent.trim() === 'Gut'`) fails and clicking the whole `<li>` can hit
the wrong row. Instead, find
the `<li>` whose text **starts with** the label, scroll it into view, then click the
**input control inside it** (`input[type="radio"]` for Zustand, `input[type="checkbox"]`
for Farbe) — not the `<li>` itself:
```js
const li = [...document.querySelectorAll('li')]
  .find(li => li.textContent.trim().startsWith('Gut'));
li?.scrollIntoView({block:'center'});
// then, after it is in view, click li.querySelector('input[type="radio"]')
```
If the inner-input click still doesn't register, fall back to a coordinate click on
the option's radio/checkbox once it is visible in the open dropdown. Note the
option list has its own internal scroll — with 6 Zustand options the lower ones
(e.g. "Gut") start out of view; the `scrollIntoView`
step above handles this, and a coordinate-click fallback must scroll the **list
element** first, not the page.

**Zustand:**
Open the dropdown and select `VINTED_CONDITION` from the action file using the
inner-`input[type="radio"]` method above. **The dropdown often opens only on
the second click** — especially after the Marke selection shifted the layout;
if no dropdown appeared after the first click, click again (and give the list
a moment to render before the JS radio-click, or it returns null). **Before
clicking, re-verify the dropdown position** — small scroll shifts can cause
the click to land on the wrong row (e.g. Farbe instead of Zustand). Take a
fresh screenshot or JS position-read of the dropdown before selecting.

**New-only category restriction.** Some Vinted categories (known: **Powerbanks**)
only allow "Neu"-family conditions — the Zustand dropdown shows just 1 entry
(e.g. only "Neu, mit Etikett"). If the offered conditions **do not include**
the action file's `VINTED_CONDITION` and the item is used in such a category:
**stop Vinted gracefully**. Do NOT force a value via React fiber dispatch or
any internal state mutation. Instead: skip the Vinted draft, tell the user this
category only accepts new items, continue with the other platforms, and note it
in the feedback.

Options top to bottom (full list):
`Neu, mit Etikett` / `Neu` / `Sehr gut` / `Gut` / `Zufriedenstellend` /
`Nicht voll funktionsfähig`. Note that "Neu" startsWith-matches "Neu, mit Etikett"
too — for the plain `Neu`/`Sehr gut`/`Gut` family prefer an exact label match on
the option's own label node, or pick by position. If the dropdown does not close
cleanly after selecting, click **outside the dropdown** to close it. **Never
dispatch a synthetic Escape `KeyboardEvent` at `document` level** — this can
freeze the page. If you must press Escape, press it on the **focused
element** inside the dropdown, not on `document`.

**Farbe:**
Farbe is multi-select (up to 2). Select the colour(s) from `VINTED_COLOR` in the
action file. **Click the colour circle by screen coordinates** — this is the one
field where coordinates beat JS. The option's `<li>` frequently has **no
`input[type="checkbox"]`** at all (the clickable target is a plain inner `<div>`),
a JS `textContent` match closes the dropdown without selecting anything, and a JS
batch selecting two colours has registered only one of them. Order of preference:
coordinate click on the circle → `li.querySelector('div').click()` →
inner-`input[type="checkbox"]`. **Select and verify one colour at a time**, and
prefer the circle in the **"Alle Farben"** section over the "Vorgeschlagen" row —
the suggested row is a different `li` and its click may not register. The
dropdown stays open after selecting — to close it, **click a neutral spot far
from any field row: the far-left edge of the page (x ≈ 150) at the dropdown's
height.** Do **not** click an adjacent field row or label to close it — a
click on the Marke or Zustand row **reopens that field's dropdown** (happened
twice in the v2.6.1 runs). Do **not** rely on `document.body.click()` either —
it does not reliably dismiss the dropdown. The already-made selection survives
the neutral click.
**Verify the colour visually (screenshot), not via `.checked`** — Vinted's colour
checkbox is a custom component whose `.checked` reads `false` even when the colour
is correctly selected on screen.

**`VINTED_COLOR: NONE` does not mean "skip" when Farbe is required.** In some
categories Vinted blocks the save until a colour is set — this happened on all
three battery items on 2026-08-15 and the user had to set Schwarz/Gold, Blau and
Grün by hand. If the field is present and the save is refused, pick the colour
that matches the photos and tell the user which you chose. Only skip the field
when it is genuinely absent from the form.

**Größe** (apparel/shoes categories — a **required** field when present):
Set the size from `VINTED_SIZE` in the action file. Vinted's Größe field is a
dropdown of category-specific size options (e.g. clothing `48`/`M`, shoe `42`).
**Ignore the "Vorgeschlagen" / suggested row at the top** — it can show
misleading values that are not the garment's size. The real
value sits lower, under the "Größen Männer"/"Größen Damen" heading. Select it by
exact label via JS rather than scrolling-and-clicking the `<li>`:
```js
[...document.querySelectorAll('div.filter-grid__option')]
  .find(el => el.textContent.trim() === '48') // === VINTED_SIZE
  ?.click();
```
**Verify the selection visually (screenshot)** — like Farbe/Zustand, the chosen
size may not read back reliably from the DOM. **Do not skip this if the field is
present** — a missing size silently saves a sizeless draft. If
`VINTED_SIZE` is `NONE` (non-apparel item) or the field is absent for this
category, skip it. If the exact size option isn't offered, read the available
sizes, pick the closest, and **flag the substitution explicitly in the final
summary to the user** (not only in the run feedback) — a changed garment size
alters the approved listing data, and the user must be able to correct it
before publishing.

**Material** (apparel/shoes — fill whenever present and known):
Vinted's **Material** is a structured field (not free text in the description).
Set it from `VINTED_MATERIAL` in the action file — open the field, select/enter
the listed composition, and verify it took. Only skip if `VINTED_MATERIAL` is
`NONE` — don't leave a known material unset.

### 5. Fill remaining fields

(The Title was already set in step 2 — verify it is still populated.)

- **Description:** content between `===VINTED_DESCRIPTION_START===` and
  `===VINTED_DESCRIPTION_END===` verbatim
- **Price:** `VINTED_PRICE` — set it **after** category and details; before a
  category is chosen the field ignores input (2026-08-29). Use `triple_click`
  on the field then `type` the value directly. Do not use the JavaScript native
  setter (`Illegal invocation` error). Vinted supports decimal prices — type
  the value as-is (e.g. `24.99`).
  If the typed value does not register (the field stays empty or reverts),
  dispatch a JS `input` event on the field after typing so Vinted's form state
  picks it up:
  ```js
  priceInput.dispatchEvent(new Event('input', {bubbles: true}));
  ```
- **A reopened draft shows an empty price field — that is not data loss.** On
  `/items/{id}/edit` Vinted renders the price input with `value: ""` even though
  the price is stored server-side. Do **not** treat it as unset and do not run a
  second fill-and-save cycle over it; check the draft's displayed price instead.
- **Price-recommendation trap.** Vinted shows a price suggestion (an
  "Optimal"-Vorschlag) near the price field, and a click aimed at a nearby
  detail field can land on it — **silently overwriting the price with the
  suggested value**. After every click in the price/details area, verify which
  element was actually hit; and re-verify the price as part of the final
  pre-save check (step 8).

### 6. Shipping method

Set the shipping **method** according to `VINTED_SHIPPING`:

- **Vinted-Versand:** Select Vinted's integrated shipping option.
- **Selbst verschicken:** Select the self-shipping option.
- **Abholung:** Select local pickup only.

**Do NOT set the package size here.** Vinted pre-selects a package size based on
category ("Empfohlen" badge) — **the recommended default varies by category and
is NOT always "Klein"**, so never assume
it; always read what is selected and set it explicitly. Critically, **it snaps
back to that recommendation whenever you edit any other field afterward**. Setting it now and then touching another field silently
reverts it. The package size is therefore set and verified as the **very last
action before saving** — see step 8.

### 7. Upload photos

Skip this step if `PHOTO_FILES` is `NONE` — the user then adds photos
manually after reviewing the draft.

The photo section ("Fotos hinzufügen") is at the top of the form — scroll
back up to it. **Never click the upload button or photo area** — that opens
a native file picker dialog you cannot see or close. Instead:

1. **Re-locate the hidden file input before EACH upload.** On Vinted the
   `<input type="file">` is **replaced after every upload**, so a ref captured
   earlier goes stale. Immediately before each single-photo call, run `find`
   ("file input for photo upload") or `read_page` to get a fresh ref. The target
   is an `<input type="file">`, typically hidden, with an image `accept`
   attribute.
2. Upload with `mcp__Claude_in_Chrome__file_upload`, passing the **fresh** input
   ref and a path from `PHOTO_FILES`. **One photo per call**, in `PHOTO_FILES`
   order, and **at most ONE `file_upload` per `browser_batch`** — the 10 MB
   size cap applies to the combined payload of the whole batch, not per call.
3. Wait 2–3 seconds after each call for the thumbnail to render, then re-find the
   input and upload the next.
4. Vinted may show photo-based suggestions (category, brand) after an upload.
   Ignore them — the category and brand from the action file are already set.
   Dismiss any suggestion banner that blocks the form.
5. After the last photo, verify the thumbnail count equals `PHOTO_COUNT`
   (screenshot).
6. **Rejection handling.** If `file_upload` returns "only files the user has
   shared with this session can be uploaded," the staging folder is not
   connected to this conversation and **every** photo will fail identically —
   do not retry each one. Report once that the photos could not be uploaded and
   the user must add them manually, or connect the listing folder and re-run.
   For a single-file rejection (size limit), skip that photo, continue with the
   rest, and list the skipped ones at the end. Never abort the listing over
   photos.

### 8. Save draft

Before saving, if you are resuming an interrupted run, re-verify the Title and the
other required fields per the "Resuming an interrupted session" note above — a
draft can save with an empty title and no error.

**Set the package size now — this must be the LAST field you touch before
saving.** Because Vinted reverts the package size to its recommended default when
any other field changes, set and verify it only after every other field is final:
- Set it to match `VINTED_PACKAGE_SIZE` from the action file:
  - **Klein** — large-envelope size (accessories, small electronics, controllers)
  - **Mittel** — shoe-box size (speakers, boxed electronics, small appliances)
  - **Groß** — moving-box size (large items)
- **Note:** Vinted's package-size recommendation can **change after photo
  upload** — one more reason
  this must be set last, after photos are uploaded.
- **Click the radio for the target size by coordinate** (or on the radio input of
  the specific size row). **Do not pick the radio with a JS substring match on the
  size's description text** — the size rows share a wrapping block and a loose
  match hits the first radio in it, selecting the wrong size.
- Then **verify on a final screenshot that the selected size still equals
  `VINTED_PACKAGE_SIZE`** immediately before clicking save — do not edit anything
  else after this check. On the same final check, **confirm the price field
  still equals `VINTED_PRICE`** — a stray click on the price recommendation
  (step 5) can have silently replaced it.

Scroll past any "Extras" upsell section and click **"Entwurf speichern"**.

**Save by JS `.click()`, not a coordinate click.** A coordinate click on the save
button has **missed and navigated to the seller profile instead** —
which both fails to save and can look like a spurious redirect. Click the button by
matching its text:
```js
[...document.querySelectorAll('button, a')]
  .find(b => /entwurf speichern/i.test(b.textContent))?.click();
```
Click **once**. Do not re-click if you're unsure it saved — instead use the
post-save diagnostics below to check.

**Post-save diagnostics:** Wait ~2 seconds, then check the current URL:
- **URL left `/items/new`** (typically redirects to the seller profile): success
  — go to the "Entwürfe" tab on the seller's profile to confirm the draft is
  there and capture the edit URL (`/items/{id}/edit`).
- **Still on `/items/new`**: a hidden validation error blocked saving. Scroll
  to the top of the page and check for visible error banners. **Identify the
  error by its markup, not by German text anywhere on the page** — collect
  elements with `aria-invalid="true"` or an error/`*--error` CSS class. Neutral
  helper text reads exactly like an error otherwise: "Bitte wähle eine
  Sendungsgröße aus" sits permanently under a correctly-filled size field and
  has already caused one misdiagnosis alongside a real caps error. Common causes:
  - **Capitalization error** (`Großbuchstaben` / too many capital letters): the
    title has all-caps words Vinted rejects. Propose using `VINTED_TITLE` from
    the action file if it exists and was normalized, or ask the user to approve
    a title-cased version, then update the title field and retry.
  - **Description too long** ("Gib nicht mehr als 2000 Zeichen bei
    Beschreibung ein"): the Vinted description exceeds the 2000-character hard
    limit. Shorten both disclaimers to the **short variant** (from
    `${CLAUDE_PLUGIN_ROOT}/templates/disclaimers.md`), re-fill the description
    field, and retry once. If still too long, tighten the body text.
  - **Required field empty**: a mandatory detail field (Marke, Zustand, Farbe)
    was not filled. Fill it and retry once.
  - **Other error**: report the exact error message to the user and pause.

**After ANY recovery edit, re-verify the package size before re-clicking
save.** Changing any field can revert the package size to Vinted's recommended
default (step 8) — a corrected title or shortened description silently undoes
it. Re-check that the selected size equals `VINTED_PACKAGE_SIZE`, re-set it if
needed, and only then save again.

**Batch browser actions — mandatory.** Run sequential browser steps (clicks,
waits, screenshots, verification reads, **and JS state reads**) as ONE
`browser_batch` call whenever the next step doesn't depend on output you
haven't seen yet — never as a chain of single calls. This is not just latency:
malformed, run-stalling tool calls have only ever occurred as singletons, while
batched calls never failed. Batching directly shrinks the failure surface.

**Never stall after a failed tool call.** If a tool call errors or fails to
parse, immediately re-issue the intended action in the same turn (preferably as
a `browser_batch`) and continue the workflow. Do not end a turn without either
a tool call or a finished/blocked platform to report. Recovery is always
possible: a correctly formatted call works after any failure.

### If login or CAPTCHA appears

Pause and tell the user. Wait for them to handle it, then resume.

## After saving

Report the Vinted draft URL (`/items/{id}/edit`). Confirm the draft is saved
and not live. **This is the only platform with a stable per-item draft link**
(eBay and Kleinanzeigen drafts have just a drafts-list URL), so it must always
appear in the final summary — capture it at save time from the "Entwürfe" tab,
not only when the user asks for it.

Once all platform drafts are saved, write the run feedback file, then present
the summary.

**Run feedback file — unconditional.** Write a `feedback.md` into the run folder
(`Listings/[YYYY-MM-DD]-[slug]/` — the same folder as `listing.md`) **whether or not other
listers still have to run** — if the run ends early (the user stops it, a platform
is skipped, tooling stays down, context runs out), the lister that was active
writes it, describing how far the run got. The old wording fired only for "the
last applicable lister", so a run that ended mid-way wrote nothing at all.: one or two
short, candid paragraphs of **developer feedback** on this run — what went
smoothly, and any friction or surprises (selector drift, fields that behaved
unexpectedly, manual steps the user had to take, rejected photo uploads, anything
the action file got wrong). This is notes for the plugin's developer to keep
improving the skills, not a buyer-facing artifact — be specific and honest.
**Start the file with a version/date/model header so stale feedback is
identifiable** — make the first line exactly
`> Plugin v[PLUGIN_VERSION] — Lauf [YYYY-MM-DD] — Modell [model], Effort [effort]`.
Take the version from the **Plugin version:** line at the top of this skill — that
line is authoritative and always present, so `unbekannt` is never correct for the
version. Fill `[model]` with the model you are running as (e.g. "Opus 5") and
`[effort]` with your reasoning-effort setting; write `unbekannt` only for a
model/effort you genuinely cannot determine.

**One file per item.** If this run covered several items, each item's folder gets
its own `feedback.md` about that item. Never write one file and copy it into
several folders — a 2026-08-08 batch did that and its shared text asserted facts
true for only one of the three items.

**Append later feedback — do not overwrite.** `feedback.md` is not write-once. If
more feedback surfaces later in the same conversation (e.g. the user critiques the
published listing after the draft was saved), **append** a dated
`## Nutzer-Feedback nach Veröffentlichung (YYYY-MM-DD)` section to the existing
file, keeping the original notes intact. Never replace what is already there —
post-publication criticism belongs in this file too.

Then present the summary. **Draft links differ by platform:** eBay and
Kleinanzeigen have no stable per-item draft URL (only a drafts-list link);
**Vinted is the only one with a direct per-item link** (`/items/{id}/edit`) —
always include it.

```
Alle Entwürfe gespeichert:
[If EBAY_APPLIES=yes: eBay (Entwürfe-Liste): https://www.ebay.de/sh/lst/drafts]
Kleinanzeigen (Entwürfe-Liste): https://www.kleinanzeigen.de/m-meine-anzeigen.html?tab=PROJECTS
Vinted (Direktlink zum Entwurf): [/items/{id}/edit URL]

[If photos were uploaded: "Alle [n] Fotos sind hochgeladen."]
[If PHOTO_FILES was NONE or uploads failed: "Fotos bitte manuell hinzufügen:
[which ones / all]."]

Die Entwürfe sind fertig zur Durchsicht. Bitte prüfe sie und veröffentliche sie
selbst, wenn alles passt.
```

**Do not offer to publish, and never publish.** Present the saved drafts and stop —
the user reviews and publishes them. End the run at "drafts saved, ready for your
review"; do not ask "soll ich veröffentlichen?" or wait to publish on their go.
