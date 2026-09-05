---
name: ebay-lister
description: >
  Creates an eBay.de draft listing by reading an approved action file produced
  by the listing-drafter skill. Trigger this automatically after the
  listing-drafter has saved an action file and the user has approved the draft —
  whenever EBAY_APPLIES is "yes" in the action file. Also trigger when the user
  asks to proceed with, retry, or fix the eBay part of a listing in progress.
  Do not trigger if EBAY_APPLIES is "no" (no-shipping items go to Kleinanzeigen
  and Vinted pickup-only).
---

# eBay Lister

<!-- PLUGIN_VERSION_LINE --> **Plugin version: 2.7.1.** This string is authoritative — use it verbatim for the action file's `PLUGIN_VERSION` and for the `feedback.md` header. A skill loaded via the Skill tool cannot see `.claude-plugin/plugin.json`, so do not try to read it and never guess a version from memory.

Your role: read the approved action file, fill in the eBay listing form field by
field, and save a draft. You make no content decisions — the action file contains
all approved content verbatim. Your job is accurate data entry and form
navigation.

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
  `mcp__Claude_in_Chrome__javascript_tool` instead — even for long description
  texts where paste might seem expedient.
- If a Chrome MCP action fails, diagnose the issue. Do not silently fall back to
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

## Safety rules

1. **Draft only.** Click the draft-save button — labelled "Als Entwurf
   speichern", sometimes just "Speichern" (it sits **below** the blue "Artikel
   kostenlos einstellen" publish button). Never click the blue publish button.
2. **No paid features.** Never select promoted listings, highlighted placements,
   "Angebot bewerben" (Basis/Premium), subtitle fees, or any paid add-on. If
   pre-selected, deselect before saving.
3. **Minimal personal info.** Use the action file's `LOCATION` for location
   fields. Never volunteer additional personal details.
4. **User-provided photos only.** Never use stock images or platform example
   images.
5. **Verify before filling — but never leave a required specific blank.** Fill
   every property the action file confirms. In addition, fill any item-specific
   (Artikelmerkmal) eBay marks as **required (Pflichtangabe, usually flagged with
   `*` or "Pflichtangabe")** whenever its value is clearly derivable from the item
   or action file — type, size, style, material, colour, brand (e.g. a two-piece
   suit → Stil "2-Teiler", a Gr. 48 suit → Größe "48"). If a *required* specific
   is genuinely not derivable, **ask the user** rather than leaving it empty.
   *Optional* specifics that are uncertain stay empty — don't guess those.

## eBay technical notes — how the form actually works

eBay's listing form (`/lstng`) uses **Marko.js**, not React. React state-setting
patterns do not apply. Understanding the save mechanism is critical to not losing
data:

**Two rules before anything else — both cost a full run when ignored:**

1. **Fill text fields with real browser input only.** `triple_click` the field
   (by ref, or by screen coordinates if the ref doesn't take), `type` the value,
   then `Tab` out. A **native value setter plus a synthetic `Event('input')`
   does NOT trigger Marko's auto-save** — the field looks correct on screen and
   is silently gone on the next reload. One run set price, shipping and
   description that way and lost all three. The RTE description script below is
   the single exception, and only because it dispatches a real
   `InputEvent` with `inputType:'insertText'`.
2. **NEVER type an EAN into eBay.de's EAN field** — see the EAN rule in step 1.

**eBay auto-saves each field individually** via XHR to the draft API when a
change is detected:
```
PUT /lstng/api/listing_draft/{draftId}
Body: {"requestId":"...","removedFields":[],"description":"<p>...</p>",...}
```

The "Speichern" button's own PUT request sends **no field data** — it only
finalizes and redirects. This means every field must trigger its own auto-save
XHR before Speichern is clicked, or the data will be lost on reload.

**Description injection.** The editor is a rich-text editor (RTE) inside an
iframe. You need **two** injection paths because **the iframe is sometimes
cross-origin** — on those loads `iframe.contentDocument` throws a `SecurityError`
and the primary method below cannot run at all. Always guard the iframe access and fall back.

**Primary — inject into the iframe (triggers the auto-save XHR):**

Embed the description as a **JSON-encoded string literal** — never paste it
into a raw template literal or quoted string. A backtick, `${`, apostrophe, or
backslash in the text breaks (or executes inside) the page script. JSON-encode
the block yourself when writing the call (escape `\` and `"`, newlines as `\n`):

```js
const descHtml = "..."; // EBAY_DESCRIPTION block as a JSON-encoded string literal

const iframe = document.querySelector('iframe[id*="se-rte"]');
let doc = null;
try {
  doc = iframe.contentDocument || iframe.contentWindow.document; // throws if cross-origin
  if (!doc) throw new Error('no doc');
} catch (e) {
  doc = null; // SecurityError / cross-origin → use the HTML-source fallback below
}

if (doc) {
  const editable = doc.querySelector('[contenteditable="true"]');
  if (!editable) {
    doc = null; // RTE not in the expected shape → fall through to the HTML-source fallback below
  } else {
    editable.focus();
    doc.execCommand('selectAll', false, null);
    doc.execCommand('insertHTML', false, descHtml);
    // A plain Event('input') is sometimes ignored by Marko's auto-save listener.
    // Dispatch a real InputEvent with inputType:'insertText' FIRST — that is what
    // reliably triggers the debounced PUT.
    editable.dispatchEvent(new InputEvent('input', {bubbles: true, composed: true,
      inputType: 'insertText', data: editable.textContent}));
    ['input', 'change', 'keyup'].forEach(evt => {
      editable.dispatchEvent(new Event(evt, {bubbles: true, composed: true}));
      doc.dispatchEvent(new Event(evt, {bubbles: true}));
    });
    iframe.contentWindow.parent.postMessage({type: 'content-change', content: descHtml}, '*');
  }
}

// The script's return value tells you which path was taken:
doc ? 'primary-injected' : 'cross-origin:use-html-source-fallback';
```

**Read the return value.** If it is `cross-origin:use-html-source-fallback`, the
iframe was unreachable (cross-origin) — run the fallback below. Otherwise
(`primary-injected`) the primary path is done; skip the fallback.

**Fallback — HTML-source textarea (use when the iframe is cross-origin).** The
**"HTML-Code anzeigen"** toggle above the editor exposes a normal, same-origin
`<textarea>` you *can* reach. The key is that you must toggle the checkbox back
**off** afterwards so eBay re-parses the textarea into the RTE and fires the
auto-save:

1. Check the **"HTML-Code anzeigen"** checkbox.
2. Set the textarea value via the native setter and fire an `input` event:
   ```js
   const ta = document.querySelector('textarea[name="description"]');
   const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
   setter.call(ta, descHtml);
   ta.dispatchEvent(new Event('input', {bubbles: true}));
   ```
3. **Uncheck "HTML-Code anzeigen"** — this makes eBay re-parse the textarea
   content back into the RTE and fire the auto-save XHR.

**Verify (either path).** After injecting, **wait 4–5 seconds** for eBay's
debounced auto-save. Install an XHR interceptor before injecting and confirm a
PUT to `/lstng/api/listing_draft/...` with `"description":` in the body was
captured. Then reload the draft and check that the RTE `innerHTML` length is
non-zero.

**What does NOT work:**
- `insertText` on the HTML source textarea — Marko ignores it
- Setting `textarea.value` via native setter + events **without toggling
  "HTML-Code anzeigen" off afterwards** — the RTE never re-parses it; the toggle
  is the missing step (see the fallback above)
- Injecting into the iframe without firing events — content appears in DOM but
  no auto-save XHR fires
- Firing only a plain `Event('input')` (no `inputType`) — Marko's auto-save
  listener sometimes ignores it; dispatch a real `InputEvent('input',
  {inputType:'insertText'})` as the primary script does
- Clicking Speichern immediately after injection — auto-save is debounced;
  clicking too fast results in an empty description on reload

## Workflow

Read the action file before starting anything. If `EBAY_APPLIES` is `no`, skip
entirely.

### 1. Navigate, then category / catalog

1. Navigate to `https://www.ebay.de/sell/create`. The prelist search box
   ("Was möchten Sie verkaufen?") sometimes **accepts no keyboard input**
   (neither `type` nor JS value-setting registers). If the search box is unresponsive, **skip it** and navigate directly to the
   identify URL:
   `https://www.ebay.de/sl/prelist/identify?title=[URL-encoded ITEM_TITLE]&isUid=false&sr=sug`
   (add `&caty=[id]` when you know the eBay category ID). This goes straight to
   the condition dialog, bypassing the flaky search box. **The `title=` parameter
   is not optional** — opening `/sl/prelist/identify` bare gives a category dialog
   with no free-text field at all, leaving no way to enter the item.
2. Try `EBAY_CATALOG_EAN` (preferred) or `EBAY_CATALOG_PRODUCT` to find a
   matching catalog entry — but **expect it to fail.** In practice an EAN
   usually does **not** auto-resolve to a catalog product on eBay.de. Do not
   spend many turns hunting for a catalog match; if the first lookup yields no
   confident match, **select the category manually** (by item type) and proceed.
   Manual category selection is the normal, expected path here.
3. If a catalog match *is* found, review each suggested property individually —
   **do NOT click "alle übernehmen"**. Accept only properties confirmed in the
   action file. Leave uncertain fields empty. **Always verify the "Marke"
   specific after any catalog or similar-listing adoption** — catalog entries
   can carry a wrong brand; correct it via the brand search to the item's real
   brand. **Adopting a catalog product also overwrites the title and can move the
   category** — it replaced a drafted 78-character title with its own short form
   on 2026-08-17, and would have switched an in-wall relay to "Smart-Zwischenstecker"
   on 2026-07-24. After any adoption, re-check `ITEM_TITLE` and the category
   against the action file and restore them if they changed.
   **Beware near-identical model names:** eBay proposed "Shelly 1PM Plus" for a
   "Shelly Plus 1PM Mini" — a different product. Read model recommendations
   character by character before accepting.
4. **Honor `EBAY_CATEGORY_HINT`:** If the action file sets
   `EBAY_CATEGORY_HINT` to something other than `NONE`, the prelist suggestion
   is known-wrong for this item type (e.g. a Leerbox that must not go in the
   device category). After the prelist, change the category in the main form
   via **Artikelkategorie > Bearbeiten > Erste Kategorie** and search for the
   hint term. Verify the selected category matches the hint before continuing.

**NEVER type an EAN into the Artikelmerkmale EAN field.** Leave it empty even
when `EBAY_CATALOG_EAN` holds a valid EAN and eBay flags the field as
required — a draft saves fine without it. Typing one starts a catalog lookup
that has, across three runs: hung on an endless spinner that froze the whole
form and disabled Speichern (Marko then stayed corrupt — Speichern could be
force-enabled but sent telemetry only, no data PUT), and pulled in wrong
catalog products (a Bosch radiator thermostat for a smart-home hub, a lighting
category for a Shelly button). The EAN belongs in the description, not in this
field. Use `EBAY_CATALOG_EAN` only for the *prelist* catalog search in step 1.2.

**If an EAN did get typed and you cancelled the catalog dialog, the EAN stays in
the field** — cancelling dismisses the lookup, not the value. Clear the field
explicitly and verify it is empty, or the draft saves with it. And never invent
an EAN to fill the field: a 2026-08-15 run entered a string matching no valid
EAN length (8/12/13/14) and it reached the live listing before the user caught
it. If the item genuinely has no EAN, the field stays empty.

**Catalog-match handling (late catalog dialog).** eBay can still raise a
**late catalog dialog** on its own after the category is set (e.g. from the
title or a prelist match). If this happens:
- **Verify each auto-filled specific individually** — do not blindly accept.
  Click "Weiter" only if all catalog values are correct.
- If the catalog data is wrong (e.g. "Infrarotfilm: Farbfilm" for an instant
  film), click **"Ohne passendes Produkt fortfahren"** to dismiss it.
- After any catalog dialog, the **title resets** to the short search query —
  re-set `ITEM_TITLE` via `triple_click` + `type` and verify `.value`.
- The catalog match may also pre-fill an **auto-price** (e.g. "54,20 €") —
  always overwrite with `EBAY_PRICE` (comma form).
- Adopting a catalog product also **adds a stock photo ("Standardbild") to the
  gallery**. Rule 4 (user photos only) applies: after your uploads, check the
  gallery holds exactly `PHOTO_COUNT` of your photos and remove the stock image
  if it is still there.
- It can set nonsense aspects (**"Herstellungsjahr: 1900er"**) — remove them via
  "Löschen". If removing one raises an **"UPC entfernen"** dialog ("Das
  ausgewählte Artikelmerkmal passt nicht zu diesem UPC"), choose **Beibehalten**
  when the prefilled EAN is the item's own barcode.
- A catalog-prefilled **EAN is verified, not touched**: compare it with the
  packaging, keep it if it matches. The no-typing rule above is about entering
  one yourself.
- **The typed title can revert after the first photo upload** — the upload's
  draft PUT carried the catalog title back (2026-08-23). Re-read the title after
  the photos are up (step 8), not only right after typing it.

**eBay.ai recommended specifics.** After category selection eBay sometimes
shows AI-recommended values for item specifics. Rules:
- **Adopt only verifiable values** — accept a recommendation only when it
  matches information in the action file or is confidently derivable from the
  item. This includes **colour**: check the recommendation against the photos.
- **Some recommendations are simply invented.** "Besonderheiten: Vergoldet"
  was suggested for a plain mains cable on 2026-08-14. Bulk-accepting this panel
  is only safe if you have already read and verified every value in it
  individually — if you have, say so; if not, accept them one at a time.
- **Never accept a compatibility aspect for the brand's own product.**
  "Markenkompatibilität: Für Sonos" on an actual Sonos speaker describes an
  accessory, not the device. Likewise skip an aspect whose only available option
  means something else — "Anschlüsse: SATA I" denotes the SATA generation and is
  meaningless for a power connector; leaving it empty is correct.
- **If the user has forbidden a claim, the AI panel is where it comes back.**
  A run that had been told not to make material claims was offered
  "Metall: Edelstahl" — the exact forbidden claim, pre-filled and plausible.
  Re-check the panel against anything the user ruled out.
- **Numeric aspects are regularly mis-parsed — verify and DELETE wrong ones.**
  The prelist/AI auto-fill has produced "Maximale Leistung: 3 W" for a 15,3 W
  supply and "Maximaler Eingangsstrom: 15 A" for a 0,5 A input. Check every
  auto-filled number against the known specs; remove a wrong value via its
  **"Löschen"** control rather than leaving a misleading spec — an empty
  optional field is always better than a wrong one.
- **NEVER adopt "Herstellergarantie"** — it contradicts the warranty
  disclaimer. eBay recommends it by default (1 Monat / 2 Jahre); always skip it.
- **NEVER adopt unverified weights** — a wrong weight mis-sets shipping.
- **The prelist's own aspect chips are a second, independent error source.**
  The identify page set `Filmformat: Super 400` (a series name) on a 120 roll
  film and `Anzahl der Fotos: 120` (the format read as a count) — neither came
  from the AI panel. After the prelist, read the essential aspects (format,
  type, model, count) back and compare each with the action file; fix via the
  dropdown's "Löschen" + search.
- **Scroll the checkbox into view before clicking its ref** — a ref click on an
  off-viewport recommendation silently does nothing (four in a row, 2026-08-27):
  `scroll_to` the ref, then `left_click`. The panel **re-renders after each
  adoption** and the tiles shift, so re-read (or re-screenshot) before the next
  one rather than clicking a stale position.
- **Click the recommendation checkboxes by ref, never by coordinates.** Do one
  full `read_page` (accessibility dump) of the section and `left_click` each
  target checkbox by its ref — coordinate clicks on this grid have misclicked.
  Verify the resulting checked set afterward.
- If a wrong value was recommended for a **required** specific (e.g.
  "Produktart" set to "Infrarotfilm" for an instant film), search and set the
  correct value manually.

**The layout shifts between clicking an aspect field and typing into it** — the
dropdown closes and the text lands nowhere, so the entry has to be repeated.
Take a screenshot after clicking an aspect field and before typing, and verify
the field is still focused and open.

**Item-specifics (Artikelmerkmale) dropdowns are finicky.** Some are searchable
multi-select fields (e.g. "Anzahl der Steckdosen"). Typing a value can highlight
or select the **wrong** option, and the field may then need a clear-then-search
cycle to recover. When filling these:
- After typing, **verify the highlighted/selected option is the exact one you
  want before confirming it** (read the field state via `javascript_tool` or a
  screenshot of just that field).
- If the wrong option got selected, **clear the field and re-search** rather than
  layering another value on top.
- For a **multi-select** specific, clicking a search result can also leave the
  auto-created **"Eigenen Wert"** (custom) entry selected alongside it — the field
  then shows two chips / a "+1". Deselect the custom entry so only the real value
  remains.
- **Marke: read the current value first, then pick the result by JS, not by
  coordinates.** The brand field can carry a **stale brand from a previous
  listing session** (an "H&M" survived into an inverter listing) — never assume
  it is empty. After typing the brand into the search, click the matching result
  with a JS `textContent` match, not a coordinate click: the list sits above
  other dropdowns and a coordinate click that misses by one row lands on the
  field below (a "+ Hoymiles" click hit the Stromquelle dropdown).
  ```js
  [...document.querySelectorAll('li, [role="option"], button, div')]
    .filter(el => el.textContent.trim() === 'Hoymiles')  // === the brand
    .sort((a, b) => a.textContent.length - b.textContent.length)[0]?.click();
  ```
  Verify the field shows the brand afterwards.
- **Prefer eBay's standard option over a custom value.** If the intended value is
  not in the dropdown but a standard synonym is, use the standard one — e.g.
  colour "Pink" does not exist in eBay's palette, "Rosa" does; pick "Rosa"
  rather than creating "Pink" as an "Eigenen Wert". Custom values only when no
  standard option fits.

**Fill all required (Pflicht) item-specifics — not just the action-file ones.**
eBay flags some Artikelmerkmale as mandatory (a `*` or "Pflichtangabe" label).
Leaving these blank produces an incomplete listing. After category selection:
- Identify which specifics are marked **required** (read the section markup or a
  screenshot of just the Artikelmerkmale block).
- Fill each required one whose value is **confidently derivable** from the item or
  action file (type, size, style, material, colour, brand — e.g. two-piece suit →
  Stil "2-Teiler", Gr. 48 → Größe "48"). For clothing, "Größe" is almost always a
  required specific — fill it from the known size.
- If a required specific's value is **not** derivable, ask the user; do not skip it.
  **Exception — EAN/GTIN:** always leave it empty, known EAN or not, per the
  never-type-an-EAN rule above. Do not ask the user and never invent one.
- *Optional* specifics: fill the ones confirmed in the action file; leave the rest
  empty rather than guessing.

### 2. Basic fields

- **Title:** `ITEM_TITLE`. The prelist/catalog search usually leaves its query
  text in the title field — **clear it with `triple_click` + Delete before
  typing.** Do **not** use `ctrl+a` + Delete: it can fail to select and insert
  the new text *into the middle* of the leftover text, producing a garbled,
  80/80-truncated title. After typing, read `.value` back
  and confirm it equals `ITEM_TITLE`; **if it doesn't match, `triple_click` to
  clear and re-type** before continuing. Use `triple_click` as the general way to
  clear any pre-filled field on this form.
  **If a ref-based `triple_click` doesn't select the field's text** (the field
  keeps the old value after typing, or the selection lands on a nearby element
  like a section heading), `triple_click` on the
  field's **screen coordinates** instead: screenshot, locate the input's visual
  position, click there.
- **Condition:** select the dropdown value named in `EBAY_CONDITION` from the
  action file — **do not assume "Gebraucht".** A new item carries "Neu" (or
  "Neu: Sonstige (siehe Artikelbeschreibung)"); only used items are "Gebraucht".
  **Media categories** (Bücher & Zeitschriften, music, films) use a granular
  5-step scale: **Neu / Neuwertig / Sehr gut / Gut / Akzeptabel** — the action
  file's `EBAY_CONDITION` may be one of these (e.g. "Sehr gut" for a lightly
  used magazine). Select the value as given.
  eBay's condition options are category-dependent: if the exact `EBAY_CONDITION`
  label is **not present** for the chosen category, do not guess — read the
  available options, list them to the user, and wait for them to pick (same
  pattern as the shipping-policy fallback).
- **Zustandsbeschreibung:** `ZUSTANDSBESCHREIBUNG_DE` — German only, physical
  condition only (no accessories, no scope of delivery). **Set it via
  `form_input` with the field's ref, not `type`** — typed text into this field
  has been silently swallowed by a layout shift twice; read the value back to
  confirm it took.

### 3. Description

Inject using the script in the technical notes above. Use the content between
`===EBAY_DESCRIPTION_START===` and `===EBAY_DESCRIPTION_END===` verbatim.

Wait 4–5 seconds after injection and verify the auto-save XHR fired before
continuing.

### 4. Listing type and pricing

- **Listing type:** `LISTING_TYPE`. If Auktion: set `AUCTION_START_PRICE`.
- **Price:** `EBAY_PRICE` — **convert the dot to a German comma before filling.**
  The action file stores prices in machine format with a `.` (e.g. `39.99`), but
  eBay.de's price field reads a dot as a **thousands** separator: entering `39.99`
  renders as **3.999,00 €**. Fill the field with the comma form instead — `39,99`
  (same for `AUCTION_START_PRICE`: `100.00` → `100,00`). **Clear any pre-filled
  value first** — eBay can carry a stale price from a previous draft state into the
  field; `triple_click` the field
  to select the leftover, then type the comma form. **If typing doesn't register,
  `triple_click` the field's screen coordinates and type again — never fall back
  to a native setter here**, the value looks right but is gone on the next reload
  (see the two rules at the top of the technical notes). After filling, read the field's
  `.value` back and confirm it shows the intended amount (not an inflated thousands
  value or a leftover from before); if wrong, clear and re-enter. **If the comma
  was swallowed** (the read-back shows `999,00` for a typed `9,99` — three
  2026-08-27 runs), clear the field and type the **dot form** `9.99` followed by
  Tab: eBay reformats it to `9,99` itself. Whichever form you typed, the
  read-back decides. (eBay converts the comma input back to dotted decimal
  internally in its auto-save XHR — that is expected.)
- **Menge (quantity):** set the field to `EBAY_QUANTITY` (default `1` when the
  field is absent). **Read the value back after setting it and confirm it matches
  the action file** — a 2026-08-15 run published 3 where the user had repeatedly
  said 2. If the action file and what the user said in conversation disagree,
  stop and ask; do not pick one silently.
- **Preisvorschläge:** Enable "Preisvorschläge zulassen". Leave Mindestbetrag
  and Automatisch akzeptieren fields empty.

### 5. Shipping

Select the shipping policy named `SHIPPING_EBAY_POLICY` from the shipping-policy
dropdown (the drafter uses the real policy names from the seller config's
`ebay_shipping_policies`, which must match the account verbatim).

**Set the policy via the real dropdown — `form_input` never sticks.** Setting
the policy combobox with `form_input` (or a JS value set) shows the new value
briefly but **silently reverts to the previous policy** as soon as the next
field is touched. The only reliable path: click the policy field to open the
actual dropdown, then click the matching option. **Both clicks must be real
browser `left_click`s on the ref — a JS `.click()` on the option element does
not register the selection** (two runs). The **kebab menu (⋮)** next to
the field is **not** the picker — it opens policy *management*. After
selecting, **re-read the displayed policy** (JS read) to confirm it still
equals `SHIPPING_EBAY_POLICY` before moving on.

**The preselected policy is inherited from the previous listing, not a sane
default.** Always read the currently selected policy and compare it against
`SHIPPING_EBAY_POLICY`. Never assume the
preselection is correct just because a policy is already set.

**Match on the policy NAME, not its description.** Policies carry both a name
and a description, and descriptions often begin with generic German text like
**"Standardversand für …"** (e.g. a policy named `Paket bis 5 kg DE & EU` may be
described as *"Standardversand für mittelgroße Gegenstände…"*). That leading
word is **description text, not a policy name** — do **not** treat
"Standardversand" as the policy to pick, and do not report it back as the name.
The dropdown lists policies by name; select the option whose **name** matches
`SHIPPING_EBAY_POLICY`. If **no** option name matches, do **not** fall back to
a generically-described option as if that were the name — use the list-and-ask
fallback just below instead.

**Match tolerantly — the dropdown may append a suffix.** eBay shows the offer
count after the policy name, e.g. `Paket bis 5 kg DE & EU (3 Angebote)`. Match an option
whose name **starts with / contains** `SHIPPING_EBAY_POLICY` (ignoring a trailing
`(N Angebote)` suffix), not byte-for-byte. If a policy is already pre-selected and
its name matches the action file modulo that suffix, leave it — no action needed.

If **no** option matches (e.g. a policy was renamed or removed), do not guess:
read the dropdown, **list the available policy names to the user**, and wait for
them to pick one before continuing.

### 6. Returns and payment

- **Returns:** select the option named in `EBAY_RETURNS` from the action file
  (e.g. "No Return Accepted")
- **Payment:** "eBay Managed Payments"

### 7. Paid promotions check

Scan for any pre-selected paid options and deselect them all.

### 8. Upload photos

Skip this step if `PHOTO_FILES` is `NONE` — the user then adds photos
manually after reviewing the draft.

**Never click the photo upload button or photo area** — that opens a native
file picker dialog you cannot see or close. Instead:

1. Locate the hidden file input in the Fotos section: use `find` ("file input
   for photo upload") or `read_page`. The target is an `<input type="file">`,
   typically hidden, with an image `accept` attribute.
2. Upload with `mcp__Claude_in_Chrome__file_upload`, passing the input's ref
   and a path from `PHOTO_FILES`. **One photo per call**, in `PHOTO_FILES`
   order, and **at most ONE `file_upload` per `browser_batch`** — the 10 MB
   size cap applies to the combined payload of the whole batch, not per call.
   Pairing each
   upload with its wait in one batch is fine; multiple uploads are not.
3. Wait 2–3 seconds after each call for the thumbnail to render, then upload
   the next.
4. After the last photo, verify the thumbnail count equals `PHOTO_COUNT`
   (screenshot) and that no catalog stock image remains. Photo uploads trigger
   their own auto-save XHR like other fields — allow it to fire before saving,
   then **read the title back once more**: the first upload's PUT has restored a
   catalog title over the typed `ITEM_TITLE`.
5. **Rejection handling.** If `file_upload` returns "only files the user has
   shared with this session can be uploaded," the staging folder is not
   connected to this conversation and **every** photo will fail identically —
   do not retry each one. Report once that the photos could not be uploaded and
   the user must add them manually, or connect the listing folder and re-run.
   For a single-file rejection (size limit), skip that photo, continue with the
   rest, and list the skipped ones at the end. Never abort the listing over
   photos.

### 9. Save draft

Click the draft-save button (**"Als Entwurf speichern"**, sometimes just
**"Speichern"** — it sits *below* the blue "Artikel kostenlos einstellen", which
publishes; never click the blue one).

**Prefer a JS `.click()` on the draft-save button over a coordinate click** —
coordinate clicks have missed the save button on the other platforms; matching by
text is more reliable. Be careful to select the **draft** button, not the blue
publish button:
```js
[...document.querySelectorAll('button, a')]
  .find(b => /als entwurf speichern|^\s*speichern\s*$/i.test(b.textContent.trim())
             && !/kostenlos einstellen/i.test(b.textContent))?.click();
```
Click **once**, then verify the save (the form leaves the compose state / a draft
confirmation appears). If unsure whether it saved, check the drafts overview rather
than re-clicking. eBay has **no stable per-item draft URL**, so use the drafts
overview link — `https://www.ebay.de/sh/lst/drafts` — as the eBay draft pointer for
the summary.

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

Report the eBay draft URL. The kleinanzeigen-lister skill handles the KA draft,
and the vinted-lister skill handles the Vinted draft when VINTED_APPLIES is
"yes".

Only once drafts for ALL applicable platforms are saved (KA always; Vinted if
VINTED_APPLIES is "yes") — i.e. if other listers still need to run, just report
the eBay URL and continue — write the run feedback file, then present the summary.

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
eBay (Entwürfe-Liste): https://www.ebay.de/sh/lst/drafts
Kleinanzeigen (Entwürfe-Liste): https://www.kleinanzeigen.de/m-meine-anzeigen.html?tab=PROJECTS
[If VINTED_APPLIES=yes: Vinted (Direktlink zum Entwurf): [/items/{id}/edit URL]]

[If photos were uploaded: "Alle [n] Fotos sind hochgeladen."]
[If PHOTO_FILES was NONE or uploads failed: "Fotos bitte manuell hinzufügen:
[which ones / all]."]

Die Entwürfe sind fertig zur Durchsicht. Bitte prüfe sie und veröffentliche sie
selbst, wenn alles passt.
```

**Do not offer to publish, and never publish.** Present the saved drafts and stop —
the user reviews and publishes them. End the run at "drafts saved, ready for your
review"; do not ask "soll ich veröffentlichen?" or wait to publish on their go.
