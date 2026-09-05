---
name: kleinanzeigen-lister
description: >
  Creates a Kleinanzeigen.de draft listing by reading an approved action file
  produced by the listing-drafter skill. Trigger this automatically after the
  listing-drafter has saved an action file and the user has approved the draft —
  this skill always applies (Kleinanzeigen is always listed, even for no-shipping
  items). Also trigger when the user asks to proceed with, retry, or fix the
  Kleinanzeigen part of a listing in progress.
---

# Kleinanzeigen Lister

<!-- PLUGIN_VERSION_LINE --> **Plugin version: 2.7.2.** This string is authoritative — use it verbatim for the action file's `PLUGIN_VERSION` and for the `feedback.md` header. A skill loaded via the Skill tool cannot see `.claude-plugin/plugin.json`, so do not try to read it and never guess a version from memory.

Your role: read the approved action file, fill in the Kleinanzeigen listing form,
and save a draft. You make no content decisions — the action file contains all
approved content verbatim. Your job is accurate data entry and form navigation.

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

- Never use `mcp__computer-use__*` for any browser action — not navigation, not
  clicking, not filling fields.
- Never use clipboard (`write_clipboard` / `read_clipboard`) to transfer text
  into a browser. Use `mcp__Claude_in_Chrome__form_input` or
  `mcp__Claude_in_Chrome__javascript_tool` instead.
- If a Chrome MCP action fails, diagnose the issue. Do not silently fall back to
  computer-use.

## Verification — prefer cheap JS reads over screenshots

Screenshots are expensive (each is a large image held in context). For **state
verification**, prefer a short `javascript_tool` snippet that returns text or
numbers over taking a screenshot:
- Checkbox state: `document.querySelector('#id').checked` → true/false
- Field value: `document.querySelector('sel').value`
- Selected option / label: read `.textContent` of the selected element
- Thumbnail / item count: `document.querySelectorAll('sel').length` → a number

Reserve screenshots for what a JS read genuinely can't capture: a final visual
confirmation, an unexpected error banner whose markup you can't predict, or
ambiguous rendering. Wherever this skill says "screenshot to confirm", a JS read
that returns the same fact is preferred unless a visual is specifically needed.

## Safety rules

1. **Draft only.** Click "Entwurf speichern". Never publish directly.
2. **No paid features.** Never select "Anzeige hervorheben", "Angebot bewerben",
   or any paid promotion. If pre-selected, deselect before saving.
3. **Minimal personal info.** Use the action file's `LOCATION` for location
   fields. Never volunteer additional personal details.
4. **User-provided photos only.** Never use stock images or platform images.
5. **German only.** Kleinanzeigen is German only — no English text anywhere.

## Workflow

Read the action file before starting anything. If `KA_APPLIES` is `no`, skip
entirely.

### 1. Navigate

Navigate to `https://www.kleinanzeigen.de/p-anzeige-aufgeben.html`

### 2. Select category

Select the appropriate category for the item type. Important:

- Desktop PCs and thin clients: **Elektronik > PCs** — there is no "Computer"
  intermediate level on Kleinanzeigen. Do not try "Elektronik > Computer > ...".
- **Category picker drill-down can be sticky.** The first JS `.click()` on a
  parent category may not expand its subcategories (KA uses hash-routing that
  sometimes swallows the event). If clicking a category doesn't expand it,
  **verify** the subcategory list appeared; if not, follow up with a
  **coordinate click** on the same row. A double-click can also work.
- **Re-read the row coordinates after each level opens.** Opening the
  subcategory column shifts the parent rows by roughly 35 px, so a coordinate
  captured before the click lands on the neighbouring category afterwards
  (a y=398 click meant for "Elektronik" hit "Freizeit, Hobby &
  Nachbarschaftshilfe"). Take a fresh screenshot or ref read per level rather
  than reusing coordinates across levels.
- **Never batch category clicks — one level at a time.** Fast sequential
  clicks through the tree (e.g. several levels in one `browser_batch` without
  waits) can **reset the whole selection** via the hash-routing. Click one
  level, wait ~3 s, verify that level expanded/registered, then click the
  next. This is the one deliberate exception to the batching rule below —
  category navigation is click → wait → verify → click. **The first click after
  a page load is regularly swallowed** (every 2026-08-27/30 run) — a row that
  only highlights without opening its column needs a second click, not a
  different strategy.
- **Verify a category click by the URL, not the screenshot.** KA encodes the
  selected path in the location hash (`#?path=…`). Reading that fragment is the
  reliable signal that a click registered; a screenshot can look plausible while
  the selection never took.
- **Condition may render as a modal dialog** (not always a dropdown), and the
  **first attempt often has no effect** — the modal closes without adopting
  the value. Open it by clicking the **chevron at the right edge of the Zustand
  row** (a click on the row's middle scrolls the page or toggles without
  opening). The row toggles on every click, so **never batch open + select**:
  click, confirm the modal is open (JS read of the dialog), *then* click the
  option. After selecting the value inside the modal, click **"Bestätigen"**,
  then **verify the condition was actually adopted** (JS read of the displayed
  value or a targeted screenshot). If it wasn't, reopen the modal and repeat
  once — select, Bestätigen, verify.

### 3. Fill fields

**Choose the category before typing the title.** Selecting a category rebuilds
the form and **destroys an already-typed title** — this cost two re-entries on a
single item in the 2026-08-14 run. The step order here (category in step 2,
fields in step 3) is deliberate; do not reorder it for convenience.

**The price field does not accept synthetic typing.** `computer type` lands the
click but the value never appears. Use `form_input` against the field's `ref` —
this appears to be true of `#ad-price-amount` generally, not a one-off.

**Setting text fields reliably (Title, Description, Price).** Kleinanzeigen's
text inputs sometimes **silently reject typed text** — the field stays empty after
`type`.

Current field IDs (verified 2026-07-24): **`#ad-title`**, **`#ad-price-amount`**,
**`#ad-description`**. Kleinanzeigen renames these periodically, so treat them as
a starting point, not gospel: if a selector returns `null`, fall back to `find` /
`read_page` and use the ref you get — do not conclude the field is missing.

Use this order and **verify `.value` after each**:
1. **`mcp__Claude_in_Chrome__form_input` with the field's `ref`** (from `find` /
   `read_page`) — this is the most reliable primitive; prefer it over `type`.
2. If the field is still empty, set it via the **native setter + `input` event**.
   Write the value as a **JSON-encoded string literal** (escape `\` and `"`,
   newlines as `\n`) — never paste raw text into a single-quoted or template
   literal; an apostrophe or backtick in the text breaks the script:
   ```js
   const el = document.querySelector('#ad-title');        // or #ad-price-amount / #ad-description
   const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
   const value = "VALUE";                                 // JSON-encoded string literal
   Object.getOwnPropertyDescriptor(proto.prototype, 'value').set.call(el, value);
   el.dispatchEvent(new Event('input', {bubbles: true}));
   ```
3. Re-read `el.value` and confirm it holds the intended text before moving on.

- **Title:** `KA_TITLE` if present in the action file (it is the ≤65-char
  Kleinanzeigen-fit title); otherwise `ITEM_TITLE`. Plain text, no formatting.
  Set it with the reliable method above and verify `.value` — a titleless draft is
  a real failure mode.
- **Description:** content between `===KA_DESCRIPTION_START===` and
  `===KA_DESCRIPTION_END===` verbatim
- **Price:** `KA_PRICE` — always as "Festpreis"
- **Condition:** `CONDITION_DROPDOWN_KA` from the condition dropdown. **Some
  categories have no condition field at all** (e.g. Elektronik > Weitere
  Elektronik) — if no Zustand dropdown/modal exists for the
  chosen category, skip it and move on; this is not an error.
- **Location:** `LOCATION`

**Scrolling:** with the cursor over the description textarea, a scroll only
moves the textarea. Scroll with the cursor in the right margin (x ≈ 1200).

### 4. Shipping

**If `SHIPPING_OFFERED` is "yes":**

The form shows a **Versandmethoden** row. Based on the item category, KA
pre-selects a recommended set of methods and lists them inline (e.g. "DHL Paket
2 kg / Hermes Päckchen / Hermes S-Paket"), with a chevron (›) at the right edge
to open the picker.

Reference methods per size (KA's size picker only offers Klein / Mittel / Groß):
| KA size | Methods to keep checked |
|---|---|
| Klein | Per SHIPPING_KA_METHODS — envelope items: Hermes Päckchen + DHL Paket 2 kg; small box: DHL Paket 2 kg + Hermes S-Paket |
| Mittel | DHL Paket 5 kg, Hermes M-Paket |
| Groß | Per SHIPPING_KA_METHODS in action file |

**Primary flow — direct recommendation checkboxes:**

1. **Check the inline pre-selection first** (screenshot). If it already matches
   `SHIPPING_KA_METHODS` exactly, leave it and skip the modal.
2. Click the chevron (›) on the Versandmethoden row to open the **"Empfehlung
   für dein Produkt"** modal. It lists the recommended methods as direct,
   pre-checked checkboxes. (A **"Versandmethoden auswählen"** button, when one
   is shown, may not open the modal on the first click — the chevron at the
   row's right edge is the reliable opener.)
3. Uncheck any method not in `SHIPPING_KA_METHODS` so exactly the wanted methods
   remain checked. (Reference the table above by visible label.)
4. Click **"Bestätigen"** to close the modal.
5. Screenshot to confirm the row now reflects exactly the selected methods.

**Fallback — full size picker** (only if the recommended checkboxes do NOT
include the methods you need, e.g. wrong size category):

1. In the modal, click **"Andere Versandmethoden"** to enter size selection.
2. Select the size radio matching `SHIPPING_KA_SIZE` (Klein / Mittel / Groß; or
   **Individueller Versand** for custom).
3. Click the **dialog-scoped "Weiter"** (there are multiple "Weiter" in the DOM
   — use the one inside the modal).
4. Toggle method checkboxes to match `SHIPPING_KA_METHODS` (table above).
   **After a size switch nothing is pre-checked** — tick every wanted method
   yourself; "Fertig" stays greyed out until at least one is checked.
5. Click **"Fertig"** or **"Bestätigen"** to close. Screenshot to confirm.
6. **Re-read the price field after any change in the shipping modal** — it came
   back empty after a method was deselected (2026-08-27) and had to be set
   again.

**If `SHIPPING_OFFERED` is "no":**

Select "Nur Abholung".

### 4b. Direkt kaufen — set per the action file

The **"Direkt kaufen"** option (buy-now with Käuferschutz, shown when shipping
is offered) is set from the action file's `KA_DIREKT_KAUFEN` field:

- **`yes`:** after the price/shipping are set, find the **"Direkt kaufen"**
  toggle/checkbox — it typically appears near the price or shipping section
  once Versand is active — and make sure it is **on**. Never deactivate it.
- **`no`:** make sure the toggle is **off** — deactivate it if KA pre-enabled it.
- **`NONE` or absent** (older action files): leave the toggle as KA presents it.
- Verify the final state with a cheap JS read of the toggle's
  `checked`/`aria-checked` state (or a screenshot of just that control) before
  saving.
- If Versand is not offered (Nur Abholung) and the "Direkt kaufen" option is
  therefore unavailable, that's fine — it only applies to shipped Festpreis items.

### 5. Paid promotions and marketing check

Ensure none of the following are checked (deselect if pre-selected):
- `#ad-feature-highlight` — Highlight (paid)
- `#ad-feature-multibumpup` — Wiederholtes Hochschieben (paid)
- `#ad-feature-topad` — Top-Anzeige (paid)
- `#ad-feature-hpgallery` — Galerie (paid)
- `#ad-marketing-consent` — Marketing-Einwilligung (opt-in)

These have known IDs, so confirm them with a single cheap JS read instead of a
screenshot — all five must come back `false` (or `null` if absent):
```js
['#ad-feature-highlight','#ad-feature-multibumpup','#ad-feature-topad',
 '#ad-feature-hpgallery','#ad-marketing-consent']
  .map(s => [s, document.querySelector(s)?.checked ?? null])
```
**Note:** These checkboxes may be **absent** on the draft compose page (they
can appear only at publish time). A `null` read is fine — it means the checkbox
doesn't exist yet and no paid feature is selected. Do not search for them if
they're not in the DOM.

### 6. Upload photos

Skip this step if `PHOTO_FILES` is `NONE` — the user then adds photos
manually after reviewing the draft.

**Never click the "Bilder hinzufügen" button or photo area** — that opens a
native file picker dialog you cannot see or close. Instead:

1. Locate the hidden file input in the Bilder section: use `find` ("file
   input for photo upload") or `read_page`. The target is an
   `<input type="file">`, typically hidden, with an image `accept` attribute.
2. Upload with `mcp__Claude_in_Chrome__file_upload`, passing the input's ref
   and a path from `PHOTO_FILES`. **One photo per call**, in `PHOTO_FILES`
   order, and **at most ONE `file_upload` per `browser_batch`** — the 10 MB
   size cap applies to the combined payload of the whole batch, not per call.
   Kleinanzeigen
   uploads each image to the server immediately.
3. **Re-find the file input after upload 1.** The file input ref invalidates
   after the **first** upload ("Element is no longer in the document"), then a
   freshly fetched ref stays stable for the rest.
   After the first `file_upload`, always `find` a new ref before upload 2. On
   any stale-ref error on later uploads, re-find before retrying.
4. Wait 2–3 seconds after each call for the thumbnail to render, then upload
   the next.
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

### 7. Save draft — exactly once

**Save by JS `.click()`, not a coordinate click.** Coordinate clicks on the save
button have **missed** in practice — and a retried click then created a
**second, duplicate draft**. Click the button by matching its
text and calling `.click()`:
```js
[...document.querySelectorAll('button, a')]
  .find(b => /entwurf speichern/i.test(b.textContent))?.click();
```

**Save EXACTLY ONCE — duplicate drafts are a real failure.** Clicking
"Entwurf speichern" twice creates two complete drafts.
After the single click:
1. Wait ~2–3 s, then **verify the save succeeded** — the **"Zu meinen Entwürfen"**
   dialog/confirmation appears, or the URL leaves the compose form. A cheap JS read
   for the confirmation text or a URL check is enough.
2. **If you cannot tell whether it saved, do NOT click save again.** Instead open
   the drafts list (`https://www.kleinanzeigen.de/m-meine-anzeigen.html?tab=PROJECTS`)
   and check whether the draft is already there. Re-clicking save is what produces
   the duplicate — checking the list is safe.
3. If a genuine duplicate already exists from an earlier attempt, tell the user so
   they can delete the extra one; do not silently leave two drafts.

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

Kleinanzeigen has **no stable per-item draft URL** — after saving, the dialog
offers **"Zu meinen Entwürfen"**. Use the drafts-list link
`https://www.kleinanzeigen.de/m-meine-anzeigen.html?tab=PROJECTS` (reachable via
Meins → Anzeigen → Entwürfe → "Fortsetzen") as the KA draft pointer for the
summary. Do **not** claim KA has no link, and do **not** substitute a later
`/s-anzeige/...` published-listing URL — that does not exist at draft time.
If that link does not land on the drafts list, try `?type=DRAFT` instead of
`?tab=PROJECTS` — 2026-08-17 runs reported both spellings and disagreed with each
other, so treat whichever works as current and note it in `feedback.md`. Two
2026-09 runs found that **both** land on the active-ads list and no "Entwürfe"
link exists in the DOM (it may only render once drafts exist); in that case
report the "Entwurf gespeichert" dialog as the confirmation and give the
Meins → Anzeigen → Entwürfe path as the pointer.

**Kleinanzeigen caps drafts: 5 concurrent, 60-day lifetime.** A batch of three
items exhausted it on 2026-08-08 with two pre-existing drafts, and on
2026-08-23 the cap swallowed a fully filled form with six uploaded photos.
**When more than one item is planned for KA in this session, count the existing
drafts before the first form** — via the drafts list if it is reachable,
otherwise ask the user how many drafts they have. Free slots = 5 minus that.
Never fill a form for which no slot is free, and never delete a draft
yourself. If a save fails for no visible reason, check for the cap before
debugging the form, and tell the user which old drafts need clearing — this is
an account limit, not a bug in the run.

### If login or CAPTCHA appears

Pause and tell the user. Wait for them to handle it, then resume.

## After saving

Report the Kleinanzeigen draft URL. The ebay-lister skill handles the eBay
draft (if EBAY_APPLIES is "yes") and the vinted-lister skill handles the
Vinted draft (if VINTED_APPLIES is "yes").

Only once drafts for ALL applicable platforms are saved (KA always; eBay if
EBAY_APPLIES is "yes"; Vinted if VINTED_APPLIES is "yes") — i.e. if other
listers still need to run, just report the KA URL and continue — write the run
feedback file, then present the summary.

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
Kleinanzeigen (Entwürfe-Liste): https://www.kleinanzeigen.de/m-meine-anzeigen.html?tab=PROJECTS
[If EBAY_APPLIES=yes: eBay (Entwürfe-Liste): https://www.ebay.de/sh/lst/drafts]
[If VINTED_APPLIES=yes: Vinted (Direktlink zum Entwurf): [/items/{id}/edit URL]]

[If photos were uploaded: "Alle [n] Fotos sind hochgeladen."]
[If PHOTO_FILES was NONE or uploads failed: "Fotos bitte manuell hinzufügen:
[which ones / all]."]

Die Entwürfe sind fertig zur Durchsicht. Bitte prüfe [sie / die Anzeige] und
veröffentliche [sie / die Anzeige] selbst, wenn alles passt.
```

**Do not offer to publish, and never publish.** Present the saved drafts and stop —
the user reviews and publishes them. End the run at "drafts saved, ready for your
review"; do not ask "soll ich veröffentlichen?" or wait to publish on their go.
