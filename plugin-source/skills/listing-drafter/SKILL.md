---
name: listing-drafter
description: >
  Drafts marketplace listings for eBay.de, Kleinanzeigen.de, and Vinted.de and
  produces a machine-readable action file that the platform-specific lister
  skills consume. Use this skill whenever the user wants to sell or list any
  item — even if they don't explicitly say "listing". Trigger on: "I want to
  sell X", "help me list this", "erstelle eine Anzeige", "eBay Anzeige",
  "Kleinanzeigen", "Vinted", sharing photos of an item for sale, or asking
  about resale price on any of these platforms. This skill covers Steps A
  (gather info), B (write draft), and C (approval) of the listing workflow.
  The ebay-lister, kleinanzeigen-lister, and vinted-lister skills run
  automatically afterward for the platforms the user selected.
---

# Listing Drafter — eBay.de, Kleinanzeigen.de & Vinted.de

<!-- PLUGIN_VERSION_LINE --> **Plugin version: 2.7.2.** This string is authoritative — use it verbatim for the action file's `PLUGIN_VERSION` and for the `feedback.md` header. A skill loaded via the Skill tool cannot see `.claude-plugin/plugin.json`, so do not try to read it and never guess a version from memory.

Your role: gather item information, ask which platforms to list on, write the
complete listing descriptions for those platforms only, get user approval, save
an action file, then hand off to the platform skills.

**This is a drafting skill. You do not touch any browser.**

**The action file you save is the single authoritative handoff artifact.** The
ebay-lister, kleinanzeigen-lister, and vinted-lister skills read nothing else —
every approved word, price, and field value must be in that file.

## Seller configuration

At the start of every run, read the seller config:

```
[listing base folder]/.claude/de-marketplace-listing.local.md
```

(The listing base folder is the current working directory — the same folder the
A0b scan uses.) Its YAML frontmatter holds everything seller-specific; the
field-by-field reference is `${CLAUDE_PLUGIN_ROOT}/templates/config-template.md`:

- `platforms` — which of `ebay`, `kleinanzeigen`, `vinted` this seller uses.
  Step A0 offers only these; a platform not listed is never drafted and its
  `*_APPLIES` field is `no`. Absent → all three.
- `location` / `location_zip` — the platforms' location field (ZIP form when a
  form requires it)
- `pickup_area` — the area named in the Kleinanzeigen pickup sentence
- `languages` — `bilingual` (German + English blocks on eBay/Vinted),
  `german-only`, or `english-only` (see Language rules)
- `disclaimers` — `yes`/`no`: whether descriptions end with the legal
  disclaimers from `${CLAUDE_PLUGIN_ROOT}/templates/disclaimers.md`
- `pricing_style` — `psychological` (.99) or `verbatim`
- `ka_direkt_kaufen` — `yes`/`no`: enable Kleinanzeigen "Direkt kaufen" on
  shipped Festpreis listings
- `ebay_returns` — the returns option to select on eBay, verbatim
- `ebay_shipping_policies` — the account's business-policy names by size tier

Rules in this file that reference a config value assume the config has been
read. **If the config file does not exist**, tell the user to run
`/listing-setup` (the normal path), or — if they want to proceed now — ask for
the values this run needs (platforms, location, pickup area, and eBay policies
when eBay is selected; the other fields default to `languages: bilingual`,
`disclaimers: no`, `pricing_style: psychological`, `ka_direkt_kaufen: no`,
`ebay_returns: No Return Accepted`) and offer to save them as the config
afterward. Without configured `ebay_shipping_policies`, eBay cannot be listed —
policy selection is by verbatim name.

## Planning approach

Always design the eBay listing first — it is the richest platform with the most
fields and strictest formatting. Then adapt the content for Kleinanzeigen and
Vinted. This ensures the best content drives all listings rather than the
simpler platforms constraining the richer one.

## Product verification

When given an EAN or model number, look it up before writing anything. Different
model numbers within the same product line can have significantly different
specs, accessories, and connectivity options — never assume based on the product
family name alone.

- Confirm: exact product name/variant, included accessories, connectivity,
  distinguishing features.
- If eBay's catalog later suggests properties, tell the user to review them
  individually and not blindly accept all — this is documented in the action file
  for the ebay-lister.
- If you cannot verify a specification, leave it out or ask the user.

## Content rules

These rules apply to everything you write. They exist because listing platforms
hold sellers legally accountable for description accuracy.

1. **No baseless condition claims.** Never write "no signs of use", "no
   scratches", "like new", "einwandfreier Zustand", "keine weiteren Mängel",
   "keine Kratzer", "no other issues", or any positive claim the user did not
   explicitly state. You do not know the item's condition better than the seller.
   This includes functionality: **"voll funktionsfähig" is a positive claim** and
   may only be written if the user confirmed the item works (asked in A3).
   Default when the user gives no detail: "Gebraucht mit Gebrauchsspuren." —
   with "aber voll funktionsfähig" only after user confirmation, and "Funktion
   nicht geprüft." when functionality is unknown or untested.
   **The mirror image also holds:** once the user HAS confirmed something
   ("es funktioniert"), write exactly that, plainly — do not decompose it into
   partial claims ("Lüfter läuft"), re-hedge it, or pad it with observed
   details the user didn't state (paste residue, suspected wear). "Gebraucht,
   voll funktionsfähig. Siehe Fotos." beats a cautious paragraph.
2. **No invented provenance.** Do not add "aus einem professionellen Einsatz",
   "aus Firmenbestand", "aus Büroauflösung", or similar background claims unless
   the user said so.
3. **Tone.** Factual, concise, friendly. No marketing fluff. Mention relevant
   flaws honestly.
4. **Confirm everything.** Title, catalog match, full description text, shipping,
   price — all shown and confirmed before being written to the action file.
5. **EAN / model number.** If the user doesn't provide one and it isn't obvious
   from images, ask before writing anything.
6. **Photos — staged for automatic upload.** The lister skills upload photos
   into each platform's form via the browser's file input, using the paths in
   `PHOTO_FILES`. Your job: locate the photo files the user provided, stage
   them in Step D, and record paths and count in the action file. If no file
   paths can be located, set `PHOTO_FILES: NONE` — the listers then save
   drafts without photos and the user adds them manually.
7. **No backticks and no `${` sequences anywhere in a description block.** The
   listers inject description text into browser-side JavaScript; these
   characters break (or execute inside) the injected script. The validator
   rejects files containing them.
8. **No unverified availability or scarcity claims.** "Wird nicht mehr
   produziert", "nur noch schwer zu bekommen", "selten", "vergriffen" are
   factual claims about the market, and they directly justify the price. Verify
   them against a current source or leave them out. On 2026-08-08 a run wrote
   that a Polaroid edition was discontinued, taken unchecked from product
   research; the user corrected that it is still sold — *"Verfügbarkeitsaussagen
   gehören verifiziert oder weggelassen — sie beeinflussen direkt den Preis."*
9. **Before calling something missing, check it was ever included.** "Ohne
   Netzteil" reads as a defect only if the item ships with one. The Brother
   ADS-1800W is sold without a PSU from the factory and runs over USB-C; the
   2026-07-24 draft listed that as a deficiency and undersold the item until the
   user corrected it. Look up the retail scope of delivery, then decide whether
   the absence is a flaw, a neutral fact, or not worth mentioning.
10. **For known form factors, the photo outranks the datasheet.** Three picoPSU
    specs were wrong on 2026-08-14 because manufacturer pages were trusted over
    the visible hardware — a 20-pin latch read as "24-polig (20+4)", a P4/ATX12V
    connector read as a 3.5-inch port, a DC jack claimed on a board that has it
    only on the cable. Where a connector, port or plug type is visible in the
    photos, describe what is actually there.
11. **Do not abandon a correct finding just because it is questioned.** If the
    user doubts something you established from evidence, do not silently delete
    it and do not dig in either: name the individual features that support it,
    say which one photo would settle the question, and ask for it. On 2026-08-06
    the user asked to strike "Gen 2" from a Sonos listing; the run listed four
    distinguishing features, cited the variant model number PL5G2EU1, and
    requested a photo of the rear — which showed a single Ethernet port (Gen 1
    has two). The user reversed. That photo belongs in the listing anyway. This
    is the complement to rule 1: rule 1 governs claims you cannot establish,
    this one governs claims you can.

## Title character limits

Each platform enforces a title length limit. Always verify the proposed title
fits within these limits before presenting it to the user.

| Platform | Limit |
|---|---|
| eBay | 80 characters |
| Kleinanzeigen | 65 characters |
| Vinted | 50 characters |

`ITEM_TITLE` is the eBay/canonical title (≤ 80 chars). Kleinanzeigen and Vinted
have tighter limits and each get their own derived title when needed:

- If the natural title is ≤ 50 characters, one title works for all platforms
  (`KA_TITLE: NONE`, `VINTED_TITLE: NONE`).
- If 51–65 characters: it fits eBay and KA; derive a ≤ 50-char `VINTED_TITLE`.
- If 66–80 characters: it fits eBay only; derive a ≤ 65-char `KA_TITLE` and a
  ≤ 50-char `VINTED_TITLE`.
- If it exceeds 80 characters, shorten the eBay `ITEM_TITLE` to fit 80 first,
  then derive the KA and Vinted versions from that.

Keep the most identifying words — brand, model, key specs — when truncating.
Never truncate mid-word. Always show any truncated title to the user for
confirmation.

**All-caps normalization for Vinted:** Vinted rejects titles with "too many
capital letters" ("Überschrift enthält zu viele Großbuchstaben"). The filter
looks at the **overall share of capitals, not just single words** — two
patterns trigger it:

1. **Any all-caps word of 4+ characters** (e.g. `BLACKKUBE`, `LOGITECH`,
   `ANKER`): derive a `VINTED_TITLE` where those words are title-cased (first
   letter upper, rest lower). Preserve short intentional acronyms (`USB`,
   `RAM`, `HDMI`, `4K`, `PS5`).
2. **Model codes — drop them from the Vinted title, always.** Any ALLCAPS model
   code trips this filter, however short: `UACC-DAC-SFP10-1M` and `10G DAC` do,
   but so does a single 5-character code — `Bosch Smart Home Heizkörperthermostat
   II BTH-RA` was rejected even though no word has 4+ capitals. Title-casing the
   segments is not enough. Derive a `VINTED_TITLE` that **drops the model code
   in favor of descriptive words**, keeping at most one short acronym — e.g.
   `UniFi UC-DAC-SFP+ Kabel 0,5m` (rejected) →
   `UniFi SFP+ Kabel 0,5m Direct Attach` (passes), and
   `… Heizkörperthermostat II BTH-RA` → `Bosch Smart Home Heizkörperthermostat II`
   (passes; a roman numeral is fine). The full model code stays in `ITEM_TITLE`
   (eBay/KA) and in the Vinted description body.

Set `VINTED_TITLE` even if the title is ≤ 50 characters when either
normalization is needed. Always show the adjusted Vinted title to the user for
confirmation.

## Description title rule

Every description starts with the item title. This applies to all platforms and
both language blocks.

- **eBay:** `<p><strong>[title]</strong></p>` as the first element of each block
  (German block and English block).
- **Kleinanzeigen:** The title as the first line of the description body (plain
  text — KA does not support bold in descriptions).
- **Vinted:** The title as the first line of each block (German block and English
  block). Plain text — Vinted has no rich text formatting.

For Kleinanzeigen, use `KA_TITLE` if one was derived; otherwise `ITEM_TITLE`.
For Vinted, use `VINTED_TITLE` if one was derived; otherwise use `ITEM_TITLE`.

## Legal disclaimers

**This whole section applies only when the seller config sets
`disclaimers: yes`.** With `disclaimers: no`, omit the disclaimers everywhere —
every "disclaimer" item in the description-structure sections below is skipped,
descriptions simply end with their last content element, and the validator
skips its disclaimer checks.

When enabled, these must appear verbatim as the last element of every
description, separated from the body by a blank line. Do not paraphrase,
shorten, or alter in any way.

**Paste, don't retype.** The disclaimers (and the correct `<small>`-wrapped /
plain-text forms for each platform) live as a copy-paste file at
`${CLAUDE_PLUGIN_ROOT}/templates/disclaimers.md`. When assembling the action
file, copy the blocks from that file rather than reproducing this legal text
from memory — the validator enforces the exact wording. The text is reproduced
inline below for reference.

### eBay — German (use EXACTLY this text):

```
Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche aus grob fahrlässiger bzw. vorsätzlicher Verletzung von Pflichten des Verkäufers sowie für jede Verletzung von Leben, Körper und Gesundheit.

Zwischenverkauf vorbehalten.
```

### eBay — English (use EXACTLY this text):

```
This item is sold without any warranty. This exclusion does not apply to claims for damages arising from grossly negligent or intentional breach of duty by the seller, nor to any injury to life, body, or health.

Subject to prior sale.
```

### Kleinanzeigen — German only (use EXACTLY this text — different from eBay):

```
Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche aus grob fahrlässiger bzw. vorsätzlicher Verletzung von Pflichten des Verkäufers sowie für jede Verletzung von Leben, Körper und Gesundheit.

Zwischenverkauf bleibt stets vorbehalten. Vertragsannahme erfolgt bei Versand durch Absendung, bei Abholung durch Übergabe.
```

The Kleinanzeigen disclaimer has a **longer "Zwischenverkauf" sentence** — the
two versions are not interchangeable. On eBay, wrap the disclaimer in `<small>`
tags so it renders in a smaller font than the body.

## Condition rules

Ask the user for a free-text condition description in their language. From their answer,
derive the dropdown value for **all three platforms** — eBay, Kleinanzeigen, and
Vinted each have their own. **Never assume "used."** Map the item's actual state
to the matching row below; a genuinely new item must get the new-item values on
every platform.

**Unified condition mapping — derive one row, fill all four fields:**

| Item state | `EBAY_CONDITION` (eBay dropdown) | `CONDITION_DROPDOWN_KA` | `VINTED_CONDITION` |
|---|---|---|---|
| New, still in original packaging / sealed (OVP) | Neu | Neu | Neu, mit Etikett |
| New / unused, but opened or without OVP/tags | Neu: Sonstige (siehe Artikelbeschreibung) | Neu | Neu |
| Lightly used, minimal wear | Gebraucht | Sehr Gut | Sehr gut |
| Used, visible wear | Gebraucht | Gut | Gut |
| Significant wear, still functional | Gebraucht | In Ordnung | Zufriedenstellend |
| Not fully functional / defective | Defekt | Defekt | Nicht voll funktionsfähig |

**The OVP nuance for Vinted matters.** Vinted's on-screen definition of
**"Neu, mit Etikett"** explicitly covers *"originalverpackt"* (still in original
packaging) — it is **not** limited to clothing tags. Vinted's plain **"Neu"**
means new/unused but **without** OVP. So a brand-new boxed electronic item (OVP,
unopened or as-good-as-new in its box) maps to **"Neu, mit Etikett"**, not
"Neu". Only drop to "Neu" when the item is genuinely new/unused but no longer in
(or never had) its original packaging.

- eBay condition labels are **category-dependent** — the exact dropdown wording
  can vary. Set `EBAY_CONDITION` to the label from the table; the ebay-lister
  matches it and, if that exact label is absent for the chosen category, lists
  the available options and asks. For most categories "Neu" and "Gebraucht" are
  present; "Neu: Sonstige (siehe Artikelbeschreibung)" is the usual eBay label
  for new-but-opened goods.
- **eBay media categories use a granular 5-step scale, not Neu/Gebraucht.**
  Bücher & Zeitschriften (and similar media categories: books, magazines, music,
  films) offer **Neu / Neuwertig / Sehr gut / Gut / Akzeptabel** instead of the
  binary labels. For media items set
  `EBAY_CONDITION` from that scale directly — lightly used → **"Sehr gut"**,
  visible wear → **"Gut"**, significant wear → **"Akzeptabel"** — so the lister
  doesn't have to re-map "Gebraucht" itself.
- **"New" means genuinely new — not a vague compliment.** Only use the top two
  rows when the user states the item is actually new/unused. Vague positive
  claims like "so gut wie neu", "basically new", "kaum benutzt" are **not** new:
  map them to the *Lightly used* row (Sehr Gut / Sehr gut) and do not add
  unverified claims like "keine Kratzer" to the text.
- In the listing **text** for KA "Sehr Gut" items, write **"wenig sichtbare
  Gebrauchsspuren"** (not "kaum sichtbare" — it reads more naturally and is
  accurate).

**eBay Zustandsbeschreibung:** German (English under `languages: english-only`).
Describe the physical condition of
the item only — never include accessories, scope of delivery, or other
non-condition information in this field. For a genuinely new item this field can
be a short positive-but-factual note (e.g. "Neu und unbenutzt, originalverpackt")
only if the user confirmed that state.

## Pricing rules

- **eBay** (with `pricing_style: psychological`, the default): Always .99 cent
  prices — but **never change a leading digit to get there.** The cent trick
  only ever touches the cents:
  - Price ends in a round **0** → subtract one cent: €45 → €44.99, €250 →
    €249.99, €39.50 → €39.99.
  - Price already ends in **9** → just append the cents: €299 → **€299.99**,
    €199 → €199.99, €49 → €49.99.
  - **€299 → €298.99 is always wrong.** A 2026-08-06 run did exactly that and
    the seller rejected the price on sight: prices are trimmed by a cent, except
    when they already end in 9 — then the cents are appended, so 299 means
    299.99. Note the opposite over-correction is also wrong — user-stated
    prices **are** adjusted by a cent; only the direction depends on the last
    digit.

  With `pricing_style: verbatim`, keep the user's stated price as-is.
- **Kleinanzeigen:** Round UP to the next full Euro. No cents supported (this
  is a platform constraint, independent of `pricing_style`).
- **Vinted:** If the user states a Vinted price (or a general asking price),
  keep it verbatim — e.g. "Preis: €25" → VINTED_PRICE 25. Only when the drafter
  derives the price (price research, or the user says "you suggest") apply the
  configured `pricing_style` — psychological: €45 → €44.99; verbatim: as
  researched/stated.
- **Derived prices are ONE price, formatted per platform.** When the drafter
  derives the price, derive a single asking price and format it per platform:
  eBay per `pricing_style`, KA rounded up to full euros, **Vinted per
  `pricing_style` exactly like eBay**. Under `psychological`, a derived
  VINTED_PRICE is never a round euro amount and never lower than EBAY_PRICE —
  a cheaper Vinted price only exists when the user asked for it or named a
  platform-specific reason. (Two v2.6.1 runs set a derived Vinted price to a
  round euro below eBay; the user had to correct both.)
- **Price research:** Before asking the user for a price, search eBay.de for
  recent completed/sold listings for the same item. Present the average as
  context. Always let the user set the final price.
- **KA price type:** Always "Festpreis". If the user wants an eBay auction, ask
  separately for the KA and Vinted prices.

## Language rules

**Talk to the seller in the language they write in.** The German questions and
labels quoted in this file are examples for German-speaking sellers; an
English-speaking seller gets the same questions, draft headings and summaries
in English. The action file's field names and enum values never change.

`languages` in the seller config decides what the **buyer** reads:

- `bilingual` (default): German block first, then English — as described below.
- `german-only`: **only the German block** on every platform — no `<hr>`/`---`
  separator, no English block anywhere; set `CONDITION_TEXT_EN: NONE`.
- `english-only`: **only the English block** on eBay and Vinted — no
  `<hr>`/`---`, no German block; titles and the English disclaimers only;
  `ZUSTANDSBESCHREIBUNG_DE` is written in English (the field keeps its name).
  Kleinanzeigen stays German regardless (its disclaimer exists only in
  German), so `CONDITION_TEXT_DE` is still required when KA applies and may be
  `NONE` otherwise.

- **eBay:** Fully bilingual. First a complete German block (title through
  disclaimer), then `<hr>`, then a complete English block (title through
  disclaimer). Each block is entirely self-contained. Under `german-only` /
  `english-only` only that one block exists.
- **Kleinanzeigen:** German only. No English text anywhere (regardless of the
  `languages` setting).
- **Vinted:** Bilingual — same structure as eBay but in plain text (no HTML).
  German block first, `---` separator, then English block. Each block ends with
  the eBay disclaimer verbatim.

## eBay description structure

### German block:
1. `<p><strong>[title]</strong></p>`
2. Opening sentence in passive voice: "Verkauft wird ein/eine [product] –
   [brief descriptor]." (not first-person "Verkaufe einen/eine")
3. Main description (item details, what's included, specs)
4. Condition sentence (user's words)
5. Legal disclaimer in German, in `<small>` tags

### English block (after `<hr>`):
1. `<p><strong>[title in English]</strong></p>`
2. Opening: "For sale: a [product] – [brief descriptor]."
3. Main description in English (same content)
4. Condition sentence in English (translation of user's words)
5. Legal disclaimer in English, in `<small>` tags

## Kleinanzeigen description structure

1. Item title (plain text, first line of description body) — `KA_TITLE` if
   derived, otherwise `ITEM_TITLE`
2. Main description in German
3. Condition sentence in German
4. Pickup/shipping line (`pickup_area` from the seller config):
   - If shipping offered: "Abholung in [pickup_area] oder Versand nach Vorkasse."
   - If no shipping: "Abholung in [pickup_area]."
   - **CRITICAL:** Always write the config's `pickup_area` — never the
     `location` value. The LOCATION field carries the city (used for KA's
     location filter) while the pickup sentence names the more specific
     `pickup_area` (e.g. LOCATION "[city]" vs pickup sentence
     "[city]-[district]"). These are different things. Do not substitute one for
     the other.
5. Legal disclaimer (Kleinanzeigen version, verbatim — only when
   `disclaimers: yes`)

## Vinted description structure

Vinted descriptions are shorter and more casual than eBay or Kleinanzeigen,
but follow the same bilingual structure with legal disclaimer (one block only
under german-only / english-only). **No HTML** —
Vinted has no HTML rendering, so use plain text throughout, including for the
disclaimer (omit `<small>` and all other tags).

Structure: German block first, then `---` on its own line, then English block.

**Hard limit: the whole Vinted description must stay ≤ 2000 characters.**
Vinted rejects longer descriptions at save time ("Gib nicht mehr als 2000
Zeichen bei Beschreibung ein").
Count the complete `VINTED_DESCRIPTION` block (both language blocks incl. the
`---` separator). Use the **full** disclaimers when they fit; when the bilingual
text would exceed 2000 characters, switch **both** blocks to the **short
disclaimer variant** (first + last sentence — copy from
`${CLAUDE_PLUGIN_ROOT}/templates/disclaimers.md`, "Vinted short variant"):

- German: "Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft."
  + blank line + "Zwischenverkauf vorbehalten."
- English: "This item is sold without any warranty." + blank line +
  "Subject to prior sale."

If it is still over 2000 characters after that, tighten the body text. Never
truncate a disclaimer any other way, and never mix variants (both blocks use
the same variant).

### German block:
1. Item title (plain text — first line)
2. Main description (2–4 sentences: what it is, key specs or notable details,
   what's included)
3. Condition sentence — `CONDITION_TEXT_DE` **verbatim**. The "shorter and
   more casual" rule applies to the body only; the condition sentence is the
   one thing that must read identically on every platform (the validator
   checks it, and two 2026-08-30 runs tripped it by paraphrasing here). Budget
   for it: if title + body + the verbatim condition + the full disclaimers
   cannot fit 2000 characters, start from the short disclaimer variant instead
   of showing the user a long draft that has to be redone.
4. eBay German disclaimer verbatim, plain text (copy from the Legal disclaimers
   section above, no tags)

### English block (after `---` separator):
1. Item title in English (plain text — first line)
2. Same content in English
3. Condition sentence — `CONDITION_TEXT_EN` verbatim
4. eBay English disclaimer verbatim, plain text (copy from the Legal disclaimers
   section above, no tags)

Do not add a shipping or pickup line — Vinted communicates shipping to buyers
through its own system.

**When to set VINTED_APPLIES=no:** Very large items that cannot be shipped
practically (large furniture, major appliances), items Vinted has no category
for, items very unlikely to have an audience there, or **used items in Vinted
categories that only allow "Neu" condition** (new-only categories — known:
**Powerbanks**; identifiable when the Zustand dropdown offers only one entry).
A used powerbank cannot be listed on Vinted at all — the category restricts
condition to new-only, and forcing a value through React internals is forbidden.
When you encounter a known new-only category and the item is used, set
`VINTED_APPLIES: no` and note it in the draft. For most items — electronics,
clothing, accessories, books, games, cameras, home goods, peripherals — set
VINTED_APPLIES=yes. If the user did not select Vinted in Step A0, set
VINTED_APPLIES=no regardless.

**Vinted shipping mapping from KA size:**
- Klein, Mittel → VINTED_SHIPPING: Vinted-Versand (platform's integrated pre-paid
  label system)
- Groß → VINTED_SHIPPING: Selbst verschicken (user ships independently)
- No shipping offered → VINTED_SHIPPING: Abholung

## Quantity

If the user is selling **more than one identical unit**, that count belongs in
`EBAY_QUANTITY` — it is the only place it can live, and eBay is the only one of
the three platforms with a quantity field.

- **Never invent quantity language in the description text.** Kleinanzeigen and
  Vinted have no quantity concept, so sentences like "ich habe 2 Sets verfügbar"
  must not appear there (seller rule, 2026-08-15: never mention multiple units
  on a platform that has no field for them). On KA/Vinted, describe exactly one
  unit.
- **Carry the number the user actually stated.** In the 2026-08-15 run the user
  said two sets, repeatedly, it was never written into a field, and eBay went
  live with **three**. A count that lives only in the conversation gets lost at
  the handoff; put it in the field.
- Selling several units on KA/Vinted means several separate listings, one per
  unit — mention that to the user rather than implying multiples in one ad.

## Shipping configuration

Ask whether shipping is offered. If yes:

- Ask: DE only or DE + EU?
- Ask for Kleinanzeigen package size. **Kleinanzeigen's size picker only offers
  Klein / Mittel / Groß — there is no "Sehr Klein".** Padded-envelope items use
  **Klein** with envelope-friendly methods.
  **Methods are a floor, not a fixed pair. Never switch off a larger method.**
  Pick the smallest method the item genuinely fits, then leave every larger
  method that KA offers switched on. The buyer chooses and pays for the method
  they want — restricting the choice upward only costs sales and costs the
  seller nothing (seller rule, 2026-08-17: if a buyer wants a bigger method,
  they pay for it). Earlier versions of this skill
  prescribed exactly two methods per size and deactivated the rest; that is
  what produced the Shelly and battery corrections.

  - **Klein** — Hermes Päckchen **only if the item is genuinely letter-sized**:
    the hard limit is **longest + shortest side ≤ 37 cm**, flat, no box.
    Päckchen is simply too small for anything else, so this is a physical test,
    not a judgement call — measure or estimate the actual parcel. A 5 m coiled
    mains cable failed this test in the 2026-08-14 run while still matching the
    word "cable"; word categories like *cables, RAM, SIM cards, HDDs, small
    peripherals* are a hint, never the test. If it fits: Hermes Päckchen **plus**
    DHL Paket 2 kg **plus** Hermes S-Paket. If it does not: leave Päckchen off
    and start at DHL Paket 2 kg + Hermes S-Paket.
  - **Mittel:** DHL Paket 5 kg + Hermes M-Paket (and anything larger KA offers).
    Note the real dialog limits — read them, do not assert them from memory:
    Hermes M-Paket is **longest + shortest side ≤ 80 cm, ≤ 25 kg**, DHL Paket
    5 kg allows up to **120 × 60 × 60 cm**.
  - **Groß:** activate all four — Hermes L-Paket (ab 9,90 €), DHL Paket 10 kg
    (10,49 €), 20 kg (18,99 €), 31,5 kg (23,99 €). KA drops the now-too-small
    presets by itself when the size changes; you do not deselect them manually.

`SHIPPING_KA_SIZE` is one of: **Klein / Mittel / Groß**. It drives the KA shipping
methods and the Vinted package size — but **not** the eBay policy, which is chosen
independently below.

**eBay shipping policy — estimate size/weight, pick from the configured
policies:**

The seller config's `ebay_shipping_policies` maps the account's business-policy
names to a size ladder. Estimate the item's actual shipped dimensions and
weight from product knowledge and the photos, then pick the policy of the
matching tier.

**`standard` is the default for practically everything — the letter tiers are a
narrow, justified exception.** Letter-tier drafts have been corrected back to
the `standard` policy by hand several times; the size estimate downgrades too
eagerly. A letter tier requires the item to be genuinely small **and flat**
— it ships in an envelope as-is. **"Flat" is a measurement, not a material:**
a Maxibrief takes up to **35 × 25 × 5 cm and 1 kg**, so a thin cardboard pack
is letter-tier even though it is rigid and boxed — instant-film packs
(~11 × 8.5 × 2 cm), magazines, blister-packed batteries. The 2026-08-23 runs
drafted instax packs as `standard` and every one was corrected by hand: a box
barely two centimetres deep is letter format. Anything deeper
than ~5 cm, bulky, or that would tear or bulge an envelope is `standard`,
however light it is. **If you are not confident it fits those dimensions, it is
`standard`.**

**The letter tier has a positive trigger too — do not read the rule as "never".**
It is the same physical test as Hermes Päckchen above: longest + shortest side
**≤ 37 cm**, flat, ships as-is in an envelope. An item that passes that test
takes the letter tier even though `standard` is the general default — flat
blistered batteries were drafted as `standard` in the 2026-08-15 run and the
user corrected all three by hand. An item that fails it takes `standard` even
when it is tiny and light: sealed-OVP adapters and a rigid metal I/O shield were
drafted as `letter_large` in the 2026-08-17 run, annotated "Brief-Tier", and were
wrong. Apply the same test to both platforms in the same run — if KA gets
Päckchen, eBay gets the letter tier, and vice versa.

| Estimated shipped item | Config tier (`SHIPPING_EBAY_POLICY` = that tier's policy name) |
|---|---|
| Fits a Großbrief (≤ 35 × 25 × 2 cm, ≤ 500 g): SIM, single thin cable, thin flat accessory | `letter_minimal` |
| Fits a Maxibrief (≤ 35 × 25 × 5 cm, ≤ 1 kg): thin accessory, flat adapter, film pack, magazine, thin cardboard pack | `letter_large` |
| **Everything else — default**: any box deeper than ~5 cm or bulky item, incl. small ones (smart-home devices, thermostats, hubs, sensors, boxed electronics, speakers) | `standard` |
| As above, **DE-only scope** | `standard_de_only` |
| Heavier / larger boxed | `larger` |
| Heavy and/or large | `largest` |

Set `SHIPPING_EBAY_POLICY` to the configured policy name **verbatim** (exact
spacing and casing) — the ebay-lister selects it by name. If the matching tier
is **not configured** (the seller has no such policy), use the nearest
configured tier — preferring the larger one — and note that to the user. If a
DE-only scope is wanted at a tier with no DE-only policy, use the DE&EU policy
of the right size (shipping EU as well is harmless) and note that to the user.

Show the chosen eBay policy **and a one-line size/weight reasoning** to the user
in the draft, and let them override if needed.

No shipping → Kleinanzeigen + Vinted with `VINTED_SHIPPING: Abholung`
(subject to the user's Step A0 selection and the VINTED_APPLIES criteria), no
eBay. Set `EBAY_APPLIES: no` in the action file.

## Platform-specific metadata (for action file)

**eBay:**
- Listing type: Sofort-Kaufen or Auktion (ask per item)
- Preisvorschläge: always enabled, no minimum, no auto-accept threshold
- Returns: `ebay_returns` from the seller config → `EBAY_RETURNS` in the
  action file
- Payment: "eBay Managed Payments"
- Catalog: an EAN/model number often does **not** auto-resolve to an eBay
  catalog product. Record `EBAY_CATALOG_EAN`/`EBAY_CATALOG_PRODUCT` when known,
  but treat manual category selection as the realistic path — do not promise the
  lister a catalog match will be found.
- **Accessory-without-device rule (formerly the Leerbox rule):** An item that is
  an accessory *for* a device rather than the device itself — original packaging,
  a Leerbox, a case, a bag, a strap, a stand, a cable for a named model — **must
  never** go in the device's own eBay category. For empty packaging eBay will
  take the listing down; for other accessories the category is simply wrong and
  the prelist will fight you. Use the accessory category for the product family
  (or `Sammeln & Seltenes > Weitere Sammelgebiete > Sonstige` for pure packaging)
  and record the path in `EBAY_CATEGORY_HINT` so the lister steers there.

  **The tell is the item name containing the device name.** A "Yashica Mat 124G
  Bereitschaftstasche" is a *bag*; on 2026-07-24 both eBay and Vinted proposed the
  camera category and offered the camera body as the catalog product. Whenever the
  title contains a device model but the item is not that device, expect every
  platform's suggestion to be wrong and set the hint up front. The same applies to
  the Vinted leaf — see the camera-accessory leaf below.
- **`EBAY_CATEGORY_HINT`** (default `NONE`): When you know the prelist
  suggestion will pick the wrong eBay category for this item type (Leerbox,
  cross-category items, niche categories), set this field to the correct
  category path or search term. The ebay-lister uses it to steer the category
  picker. Leave `NONE` for normal items where the prelist search is expected to
  find the right category. Known paths: instant film and film rolls live in
  `Foto & Camcorder > Analoge Fotografie > Fotografischer Film` (the older
  `Filme > Sofortbildfilm` path no longer exists); its required *Produktart*
  offers only Farbe / Schwarzweißfilm (plus Infrarot variants) — a colour film
  is "Farbe", not "Farbfilm". On Kleinanzeigen, film goes to
  `Elektronik > Foto > Zubehör`.

**Kleinanzeigen:**
- Price type: always Festpreis
- Direkt kaufen: `ka_direkt_kaufen` from the seller config → `KA_DIREKT_KAUFEN`
  in the action file (`NONE` when no shipping — the option only exists for
  shipped Festpreis listings)
- Location: `location` from the seller config (`location_zip` if more detail
  required)
- Category for desktop PCs / thin clients: Elektronik > PCs (no "Computer" level)
- Title format for accessories: use ", mit [Zubehör]" or ", ohne [Zubehör]" after
  a `|` separator — not `+`

**Vinted category rules:**
- `VINTED_CATEGORY` must be a full leaf path — the node that, when selected,
  loads detail fields (Marke, Zustand, Farbe, etc.). Parent-only nodes are not
  valid values.
- `Elektronik` alone is **not valid** — it is a parent-only node.
- Any path ending before a leaf (e.g. `Elektronik > Computer & Zubehör`) is
  **not valid**.
- **Generic electronics accessories fallback:** if the item is an unclassified
  electronics accessory (cables, chargers, batteries, adapters, USB hubs,
  small gadgets), use exactly:
  `Elektronik > Andere Geräte & Zubehör > Sonstiges Zubehör`
  Do not invent `Elektronik > Sonstiges` — this category does not exist.
- **Common leaf paths for electronics:**
  - Chargers/batteries/cables/adapters: `Elektronik > Andere Geräte & Zubehör > [leaf]`
    (Ladegeräte / Kabel / Adapter / Batterien & Netzteile / Powerbanks / Sonstiges Zubehör)
  - Mice: `Elektronik > Computer & Zubehör > Mäuse`
  - Tablets and e-readers: `Elektronik > Tablets, E-Reader & Zubehör > Tablets`
    (there is no `Computer & Zubehör > Tablets`; drafted once, 2026-08-29). This
    leaf has an extra required **Speicher** field with no action-file
    counterpart — the lister fills it from the description and reports it.
  - Magazines: `Bücher & andere Medien > Zeitschriften` — no brand or colour
    field, condition only.
  - Gaming controllers: `Elektronik > Videospiele & Konsolen > Controller`
  - Cameras: `Elektronik > Kameras & Zubehör > Kameras > [leaf]`
    (known leaves: Sofortbildkameras / **Filmkameras** — the analog-camera leaf
    is named "Filmkameras", NOT "Analoge Kameras", which does not exist on
    Vinted)
  - Camera bags and cases (Bereitschaftstasche, Kameratasche, Hülle):
    `Elektronik > Kameras & Zubehör > Zubehör > Kamerahüllen & -taschen` — a real
    leaf, and the correct one for a bag. Do **not** fall back to
    `Sonstige Fotografie-Ausstattung` for these. Searching the Vinted category
    picker for the plural "Kamerataschen" returns nothing; search **"Tasche"**.
  - Photo accessories / mixed photo lots (Konvolut, lenses, filters): use
    the catch-all `Elektronik > Kameras & Zubehör > Sonstige Fotografie-Ausstattung`
    (the specific `… > Kameras > [leaf]` paths are for actual cameras only;
    `Sonstige Fotografie-Ausstattung` is for mixed photo gear, not for film —
    use the Film leaf below for film rolls and instant film — and not for bags,
    which have their own leaf above)
  - Instant film / film rolls (Sofortbildfilm, analog film):
    `Elektronik > Kameras & Zubehör > Zubehör > Film` — this leaf has NO
    Farbe/Größe fields, so set `VINTED_COLOR: NONE` for film items.
    **This leaf allows only the condition "Neu, mit Etikett" and explicitly bans
    used or tested items.** That is a constraint on what may be listed here, not
    a licence to relabel: if the film is opened, expired-but-used, or its box is
    damaged, it does not become "Neu, mit Etikett" — set `VINTED_APPLIES: no`
    rather than over-claiming. A 2026-08-08 run listed a torn-open Golden
    Moments box as "Neu, mit Etikett" on this basis.
  - Power supplies / chargers (Netzteil, Ladegerät, PSU): searching "Netzteil"
    in the Vinted picker returns exactly these leaves — **Effektpedale,
    Computer-Netzteile, Steckdosenleisten, Einwegbatterien, Akkubatterien,
    Akkuladegeräte, Wechselrichter**. A generic desktop/universal PSU goes to
    `Computer-Netzteile`; Vinted's own title-based suggestion offers
    "Laptop-Ladegeräte", which is wrong unless the item really is a laptop
    charger.
  - Ear-tips / ear-cushions (Ohrstöpsel, Ear-Tips, Ersatzaufsätze): `Audio,
    Kopfhörer & Hi-Fi > Zubehör für Audiogeräte > Ohrhörer-Aufsätze` — note this
    is a top-level "Audio, Kopfhörer & Hi-Fi" category, **not** under "Elektronik"
  - Smart plugs / smart-home devices (Shelly, smarte Steckdosen, Schalter,
    Relais): `Home > Werkzeuge & Heimwerken > Smart Home & Sicherheit > Smarte
    Steckdosen & Schalter` — under the top-level "Home" category, **not**
    "Elektronik"
  - Thermostats (Heizkörperthermostat, Raumthermostat, smart or not): the
    sibling leaf `Home > Werkzeuge & Heimwerken > Smart Home & Sicherheit >
    Smarte Thermostate` — not "Smarte Steckdosen & Schalter". Vinted makes no
    room-vs-radiator distinction; both go here
  - **`Home > Werkzeuge & Heimwerken > Smart Home & Sicherheit` — the complete
    leaf list** (verified in the 2026-07-24 run; there are no others):
    Smart-Home-Hubs / Smarte Türschlösser / Smarte Thermostate / Smarte Rauch- &
    Gaswarnmelder / Smarte Lichter & Glühlampen / Smarte Steckdosen & Schalter /
    Video-Türklingeln / Überwachungskameras / Vorhängeschlösser.
    **There is no leaf for sensors or motion detectors** — a Bewegungsmelder,
    Tür-/Fensterkontakt or similar sensor goes under `Smart-Home-Hubs`. Do not
    draft `Sicherheitskameras & Sensoren`; that leaf does not exist (drafted
    once, 2026-07-24)
  - Picture frames (Bilderrahmen): `Home > Wohnaccessoires > Rahmen` — there
    is no "Bilderrahmen" leaf and nothing under "Dekoration"; the only other
    search hit ("Kinder > Möbel & Deko > Deko & Andenken") is wrong
- **Common leaf paths for menswear** (Vinted's leaf names differ from the obvious
  word — verify against this list):
  - **Two-piece suit → `Herren > Anzüge & Blazer > Anzugsets`** (NOT "Anzüge",
    which does not exist as a leaf). Siblings: Blazer / Anzughosen / Westen /
    Hochzeitsanzüge / Sonstiges.
  - Shirts: `Herren > Hemden` (leaf); T-shirts/Henleys: `Herren > T-Shirts`.
- **The drafter cannot know every Vinted leaf name.** Give your best leaf path; the
  vinted-lister verifies it against the live picker and, if the exact leaf is
  absent, substitutes the closest available sibling and notes it in the run
  feedback. Write the most specific path you're confident about.
- **Do not invent a leaf that merely sounds plausible.** Vinted's taxonomy is
  narrower than product categories suggest, and a fabricated leaf costs the
  lister a search-and-substitute cycle. When the list above covers the parent
  branch, pick from it. When it doesn't and you are unsure, name the **parent**
  branch plus your best guess, and say in the draft that the lister will pick
  the closest live leaf — an honest approximation beats a confident invention.

## Workflow

### Step A0: Select marketplaces

Before anything else, ask which platforms to include using a multiselect
question. Offer **only the platforms in the seller config's `platforms`**, all
pre-selected (the common case is all of them):

"Für welche Plattformen soll ich die Anzeige erstellen?"
- [x] eBay.de
- [x] Kleinanzeigen.de
- [x] Vinted.de

If the config names a single platform, skip the question and say which one
you are drafting for. A platform missing from the config is not offered and
not mentioned — the user adds it via `/listing-setup`.

Record the answer. Only draft description blocks for the selected platforms.
Set KA_APPLIES, EBAY_APPLIES, and VINTED_APPLIES accordingly (these can be
further restricted by logic — e.g., EBAY_APPLIES=no if no shipping — but they
can never be "yes" for a platform the user deselected).

### Step A: Gather all information

Collect everything before writing. Ask in logical groups — multiple related
questions per message is fine. Do not touch any website.

**A0b. Determine the item source — default to scanning the listing folder.**

When the user gives a **vague "just list something"** request (e.g. "list this",
"verkauf das", "stell was ein", "list whatever's in there") **without naming a
specific item or attaching/pointing to specific photos**, do NOT ask "what do you
want to list?" and "where are the photos?". Instead, **look in the listing folder
for the photos the user dropped there** and work from those — this is the normal
way the user starts a run:

1. The listing **base folder** is the current working directory — the
   connected listing folder (the one `/listing-setup` marked). It holds the `Listings/` subfolder (structured per-item
   runs) plus any **temporary photo subfolders** the user created for items they
   want listed. **Sanity-check this before scanning:** the cwd must itself
   contain a `Listings/` subfolder — that marker identifies the listing base.
   If it does not, you are NOT in the listing folder (wrong cwd): do not scan,
   classify, or consume anything there; fall back to asking the user (item 6).
2. `ls` the base folder's immediate children. A **temp photo folder** is a direct
   child directory that (a) is **not** `Listings/`, (b) is not a hidden/system
   entry (`.git`, `.DS_Store`, etc.), (c) does **not** contain a `.consumed*`
   marker file (those folders were already processed by a previous run — skip
   them), (d) contains at least one image file (`.jpg` / `.jpeg` / `.png` /
   `.webp` / `.heic` / `.heif`), and (e) is a real directory, **not a symlink**
   — never scan or consume a symlinked entry (it can point outside the base
   folder). Also treat any loose image files sitting
   directly in the base folder as a source.
3. **Exactly one** temp folder (or one group of loose images) → use it as the item
   to list. **Record its full absolute path** from the `ls` output — Step D will
   delete the temp folder **by this exact stored path**, never by re-deriving it
   from the item slug. **Look at the photos** to identify the product, do the usual
   product research (A1), then continue Step A normally. You still confirm
   condition, shipping, price and title with the user — you just don't ask what the
   item is or where its photos are.
4. **Several** temp folders → list them to the user and ask which to start with;
   handle **one item per run** (one full draft → approval → lister cycle each).
   If the user says "list them all", process them sequentially, one complete run
   per folder. **When more than one item is headed for Kleinanzeigen, say up
   front that KA allows at most 5 drafts at once** — a 2026-08-23 batch lost a
   fully filled form (six photos uploaded) to that cap on the fourth item. The
   user can clear old drafts before the browser work starts.
5. **Mixed source** (a temp folder *and* loose images in the base folder both
   present) → do not silently combine them. Ask the user which is the item to list.
6. **None found** → fall back to the normal flow: ask the user what they want to
   list and for photos (A1/A2 below).

Photos discovered this way are real **on-disk files**, so they populate
`PHOTO_FILES` directly — the "chat attachments are vision-only" caveat (A2) does
not apply. The temp source folder is **consumed** at the end of staging (Step D
deletes it once its photos are safely copied into the item folder).

If the user *did* name a specific item or attach chat photos, skip this scan and
gather normally.

**A1. Product identification**
- Item name, brand, EAN or model number (ask if not provided and not obvious)
- Look up the model number — confirm with the user what you found
- **Ask for dimensions when size decides the purchase** (enclosures, furniture,
  frames, bags, cases). Facts handed in after the drafts exist must be patched
  into three platforms by hand (2026-08-23).
- Film boxes print ISO/DIN as "3200/36°" — the number after the slash is DIN,
  never the frame count (an Ilford 120 roll was nearly drafted as a 36-exposure
  135 film, 2026-08-30).
- **EAN from photos:** If the EAN is on the packaging photo, crop generously
  (the whole corner / label area, full resolution, rotated upright if needed)
  before running a barcode decoder. If automated decoding fails, read the
  plaintext digits from the image — they are usually legible even when the
  barcode itself can't be scanned.

**A2. Images**
- Acknowledge images if provided ("Ich sehe [n] Fotos des Artikels")
- Determine whether the photos exist **on disk**, since automatic upload needs
  real files:
  - **If the photos came from the A0b folder scan**, they are already on disk in
    the temp source folder — record those paths; nothing more to ask.
  - If the user pointed to a folder or on-disk files, locate those paths.
  - **Chat attachments are vision-only** — you receive the pixels, not the
    original file or its path, so you cannot faithfully write an upload-quality
    copy to disk. If the only photos are chat attachments, tell the user that the
    originals need to be on disk: after the draft is approved you will create the
    item folder and ask them to drop the originals in there (see Step D). They may
    also place them in the `Listings/` folder now.
- If no on-disk photos can be obtained, the listers save drafts without photos and
  the user adds them manually — continue.
- Note the count for the action file
- **1-photo advisory:** If only 1 photo is available, suggest adding 2–3 more
  (multiple angles improve buyer confidence and sell faster) — but do not block
  the listing on it.

**A3. Condition**
- Ask for free-text condition description in the seller's language (translate
  it for the other language block when bilingual)
- **Ask about functionality as its own question** ("Funktioniert alles /
  getestet?"). "Voll funktionsfähig" may only be written if the user confirms
  it — it is a positive claim like any other (content rule 1). If the user
  hasn't tested the item or doesn't know, the description says "Funktion
  nicht geprüft." instead; the dropdown condition stays whatever the visual
  state supports.
- Map to the platform dropdown values for **all three** platforms using the
  unified table in "Condition rules" — `EBAY_CONDITION`, `CONDITION_DROPDOWN_KA`,
  and `VINTED_CONDITION`. Do not default to "used": ask/confirm whether the item
  is new (and if so, whether it is still in original packaging — that decides
  Vinted "Neu, mit Etikett" vs "Neu").
- Default **only** if the user gives no condition detail and the item is
  evidently used: "Gebraucht mit Gebrauchsspuren." — plus the functionality
  statement per the bullet above ("aber voll funktionsfähig" if confirmed,
  "Funktion nicht geprüft." if unknown).

**A4. Shipping**
- "Bietest du Versand an?"
- If yes: scope (DE / DE+EU) + KA size (Klein/Mittel/Groß). Estimate the item's
  shipped size/weight and pick the eBay policy from the configured ladder
  (default: the `standard` tier), then confirm with the user.

**A5. Listing type and price**
- Sofort-Kaufen or Auktion?
- Research eBay.de recent sold listings, present average price
- Ask user for price — show: "eBay: €[per pricing rules] / Kleinanzeigen: €[rounded up]
  Festpreis / Vinted: €[price] — passt das?"
- If Auktion: also ask for KA Festpreis

**A5b. Vinted detail fields** (only when VINTED_APPLIES=yes)

Determine the following before writing the draft — they must appear in the action
file verbatim:

- **VINTED_BRAND:** What the brand would be called in Vinted's brand search
  (often matches product brand exactly). Set `VINTED_BRAND_FALLBACK` to what the
  lister should do if the search finds no match:
  - The item **has a real brand** that may not be in Vinted's database (e.g.
    Phomemo, a niche manufacturer) → `VINTED_BRAND_FALLBACK: Markenname nutzen`.
    The lister selects the "„[Marke]" als Markenname nutzen" entry (uses the typed
    brand as a custom brand name). Keep `VINTED_BRAND` as the real brand name.
  - The item has **genuinely no brand** (unbranded generic) →
    `VINTED_BRAND_FALLBACK: Keine Marke erkannt` (or `Keine Marke`).
- **VINTED_COLOR:** Choose one or two colors from Vinted's palette that best
  describe the item: Schwarz, Grau, Weiß, Creme, Beige, Aprikose, Orange, Rot,
  Pink, Lila, Blau, Grün, Braun, Silber, Gold, Bunt, Klar. Use product knowledge
  or images — ask the user only if truly ambiguous.
- **VINTED_PLATFORM:** Only for categories like `Videospiele & Konsolen > Controller`.
  Leave `NONE` for most items.
- **VINTED_MATERIAL:** For **apparel and shoes, fill this whenever the
  composition is known** — from a care-label photo, the user's statement, or
  reliable product research (e.g. "100% Schurwolle", "Leder", "Baumwolle").
  **Never infer the material from the EAN/article number** — the same model
  often ships in many different blends. If the composition is genuinely unknown, ask
  the user or leave `NONE` — do not guess. Leave `NONE` for electronics and other
  items where material is not a meaningful attribute.
- **VINTED_SIZE:** For apparel and shoes, set the size as it appears in Vinted's
  Größe selector (clothing `48`/`M`, shoes `42`, etc.) — it is a **required** field
  for those categories. Take it from the user's stated size or the garment label.
  Leave `NONE` for non-apparel items (electronics, etc.).
- **Item-specifics for eBay (apparel especially):** Capture the attributes eBay
  marks as required Artikelmerkmale so the ebay-lister can fill them — for clothing
  that means at least **Größe** and **Stil** (e.g. a two-piece suit → Stil
  "2-Teiler"), plus material/colour/type where known. You don't add separate action
  fields for these; record them in the condition/product notes and the title so the
  lister can derive them. The ebay-lister fills required specifics from confidently
  known values and asks the user only when a required one isn't derivable.
- **VINTED_PACKAGE_SIZE:** Derive from `SHIPPING_KA_SIZE`:
  Klein → Klein / Mittel → Mittel / Groß → Groß. **Exception:** items that
  don't belong in an envelope default to `Mittel` (shoe-box) even if the KA
  size came out Klein — that covers electronics shipped in their original box
  (OVP) **and rigid or bulky bare items** (a metal CPU cooler, a cast-iron
  bracket): Vinted "Klein" means large envelope, and a stiff object that would
  tear or bulge one ships in a small box.

**A6. Catalog match and title**
- State which catalog product you'll match to
- Propose a title and check its length against the limits in the
  "Title character limits" section above
- If the title exceeds a platform limit, propose a shortened version
- Get confirmation on the final title(s)

**Completion check:**
- [ ] Marketplaces selected
- [ ] Product verified (model, specs, accessories)
- [ ] Condition determined for all platforms (EBAY_CONDITION + CONDITION_DROPDOWN_KA + VINTED_CONDITION); new items not defaulted to "used"
- [ ] Shipping confirmed (or confirmed no shipping)
- [ ] Price confirmed (eBay per pricing_style + KA full euro + Vinted)
- [ ] Title confirmed and within character limits for all selected platforms
- [ ] If VINTED_APPLIES=yes: VINTED_BRAND, VINTED_COLOR, VINTED_CATEGORY (exact leaf), VINTED_PACKAGE_SIZE determined; VINTED_SIZE set for apparel/shoes (NONE otherwise)

### Step B: Write the complete draft

**This is your main deliverable.** After Step A, your next message must be the
complete draft text below. Do not navigate to any website. Just write the text.

Every word, exactly as it will appear on the platforms. Not a summary. Not an
outline. The actual sentences, the actual HTML, the actual legal disclaimers
copied verbatim.

Only include description blocks for the platforms that were selected in Step A0
and are applicable (EBAY_APPLIES=yes, KA_APPLIES=yes, VINTED_APPLIES=yes).
Omit description blocks for unselected or inapplicable platforms.

Use this exact format:

---

=== VOLLSTÄNDIGER LISTING-ENTWURF ===

**PLATTFORMEN:** [eBay.de] [Kleinanzeigen.de] [Vinted.de] ← only selected ones

**TITEL:** [title]
[If a shorter KA title was needed: **KA-TITEL (≤65 Zeichen):** [ka title]]
[If a shorter Vinted title was needed: **VINTED-TITEL (≤50 Zeichen):** [vinted title]]

**EBAY-KATALOG:** [catalog product name + EAN]

**ZUSTAND:** eBay: [EBAY_CONDITION] (Beschreibung: "[condition text in German]") / KA: [dropdown value] / Vinted: [VINTED_CONDITION]

**VERSAND:** KA [Klein/Mittel/Groß] / eBay [exact policy name] ([one-line size/weight reasoning]) / Vinted: [Vinted-Versand / Selbst verschicken / Abholung]
(or: Kein Versand — Kleinanzeigen + Vinted Abholung, kein eBay)

**ANGEBOTSTYP:** [Sofort-Kaufen / Auktion ab €X] / Preisvorschläge: Aktiviert

**PREISE:** eBay €[per pricing rules] / KA €[full euro] / Vinted €[price — verbatim if user-stated, per pricing_style if derived]

[If VINTED_APPLIES=yes: **VINTED-DETAILS:** Kategorie: [exact leaf path] / Marke: [brand or "Keine Marke erkannt"] / Farbe: [color(s)] / Größe: [size or "—"] / Paketgröße: [Klein/Mittel/Groß]]

**FOTOS:** [count] Fotos ([werden beim Erstellen der Entwürfe automatisch hochgeladen / keine Dateipfade gefunden — du lädst sie manuell hoch])

--- EBAY-BESCHREIBUNG (exakter Wortlaut) ---
[Only if eBay is selected and EBAY_APPLIES=yes]

[Complete HTML — German block starting with <p><strong>[title]</strong></p>,
then <hr>, English block starting with <p><strong>[title]</strong></p>
(only the configured block under german-only / english-only, no <hr>).
Include all <p>, <strong>, <small> tags. Disclaimers verbatim.]

--- KLEINANZEIGEN-BESCHREIBUNG (exakter Wortlaut, nur Deutsch) ---
[Only if Kleinanzeigen is selected and KA_APPLIES=yes]

[Complete plain text. First line is the KA title (KA_TITLE if derived, else
ITEM_TITLE). Then main description, condition, pickup/shipping line, disclaimer
(KA version) verbatim at end. No "@" character anywhere — Kleinanzeigen rejects
"@" in the description on publish; write "bei" or "/" instead (e.g. "4K@60Hz" →
"4K bei 60Hz"). eBay and Vinted accept "@".]

--- VINTED-BESCHREIBUNG (exakter Wortlaut, kein HTML, zweisprachig) ---
[Only if Vinted is selected and VINTED_APPLIES=yes]

[Complete plain text. German block: title on first line, description, condition,
eBay German disclaimer. Then ---, then English block: title on first line,
description, condition, eBay English disclaimer. No HTML tags anywhere.]

=====================================

Hier ist der komplette Entwurf. Bitte prüfe alles — Beschreibungen, Preise,
Versand, Titel. Wenn alles passt, schreibe ich die Action-Datei und starte die
Listings.

---

### Step C: Wait for approval — HARD STOP

Do not proceed until the user explicitly approves ("ok", "passt", "yes", "sieht
gut aus", or similar). Apply requested changes and re-present the full draft.
Repeat until approved.

**Until that explicit approval arrives, presenting the draft is the ONLY thing
you may do.** Do **NOT**, on any account, perform any of these before approval:
- create the `Listings/` run folder or any per-item folder,
- stage, copy, convert (HEIC→JPEG), or resize any photo,
- write `listing.md` / the action file,
- start the ebay-lister, kleinanzeigen-lister, or vinted-lister.

These are all side-effecting steps. If the user asks a question
or requests an edit, answer/revise and re-present; that is not approval. Wait for
an unambiguous go-ahead.

### Step D: Save action file and hand off

**Precondition: Step C approval has been received.** If it has not, stop and
return to Step C — do not create folders, stage photos, or write any file.

**A listing run is not "create some drafts". It is: run folder → action file →
validator green → listers → `feedback.md`.** The run is not complete, and must
not be reported as complete, until `feedback.md` exists on disk. Steps 1–4 below
all happen **before you open any website**. Do not start browser work and
archive afterwards: in the 2026-08-14 and 08-15 runs the archive was written
only after the user asked, days later, with all drafts already live — one run
diagnosed itself exactly right: *"Ich habe die Aufgabe als 'Entwürfe anlegen'
gelesen statt als 'Listing-Lauf durchführen'."*

**One run = one item = one folder.** When the user hands you several items,
each gets its own folder, its own action file, and its own `feedback.md`
describing that item's run. Never write one shared feedback file into several
folders: the 2026-08-08 batch copied one file into three folders, and its
blanket claim that the film was "versiegelt" was false for an item whose own
action file recorded a torn-open box.

Once approved:

1. **Create the per-item run folder and save the action file inside it:**
   - Check whether a CLAUDE.md exists in the current working directory (i.e.,
     whether there is an active project folder). If yes, the base is
     `[CWD]/Listings/`.
   - If no project folder is identifiable, ask: "Wo soll die Listing-Datei
     gespeichert werden?"
   - Create **one folder per listing run** that holds everything for this item:
     `[base]/Listings/[YYYY-MM-DD]-[item-slug]/` (lowercase, hyphens, no special
     characters, date from today). Create it if it does not exist.
   - Save the action file as `listing.md` **inside that folder** (the folder name
     already carries the date and slug, so the file name does not repeat them).
   - **Everything for this run lives in this one per-item folder, and that folder
     always lives under a `Listings/` parent.** That means: `listing.md`, the
     staged/processed photos (`01.jpg`, `02.jpg`, …), and the `feedback.md` the
     listers write at the end (see the lister skills) all go directly in
     `Listings/[YYYY-MM-DD]-[slug]/`. There is no separate `photos/` subfolder,
     and nothing for this run is written outside this folder. If a `Listings/`
     folder does not exist yet, create it — do not scatter listing files at the
     project root.

2. **Stage the photos into the item folder** (skip if no on-disk photos were
   obtained in A2 — then set `PHOTO_FILES: NONE`):
   - **If the photos were only chat attachments** (vision-only, no file on disk):
     tell the user the exact item-folder path and ask them to drop the original
     photos in there, then wait. Once they confirm, list the folder (`ls`) to pick
     up the originals. If they can't, set `PHOTO_FILES: NONE` and continue.
   - Stage each photo **directly in the item folder**, numbered in display order:
     `01.[ext]`, `02.[ext]`, … The first photo becomes the title image.
   - **Convert HEIC/HEIF to JPEG.** iPhone photos are HEIC by default and
     **Vinted's upload field rejects HEIC outright** (eBay and Kleinanzeigen
     accept it, but Vinted does not, which breaks the cross-listing). For any
     `.heic`/`.heif` source, stage a JPEG instead:
     `sips -s format jpeg [src] --out [item-folder]/NN.jpg`. Always stage `.jpg`/
     `.jpeg`/`.png`/`.webp`; never leave a `.heic` path in `PHOTO_FILES`.
   - **Size limits.** The browser upload tool rejects calls over 10 MB. Check
     sizes (`ls -l`); downscale any file over 8 MB with `sips -Z 2500 [file]`
     (smaller max dimension if still over 8 MB). **eBay rejects images whose
     WIDTH is under 500 px** ("Muss über 500 Pixel breit sein") — `sips -Z`
     caps the long edge, so for tall portrait photos verify the resulting
     width stays above 500 px (`sips -g pixelWidth [file]`) and pick a larger
     `-Z` value if needed. `2500` is safe for normal aspect ratios; do not
     downscale below ~1000 px on the long edge.
   - **Resize ONLY with `sips`. Never use Pillow/PIL, ImageMagick, or any other
     library to resize a listing photo.** `sips` honours the EXIF orientation
     tag; Pillow neither applies nor preserves it on save, so a resized photo is
     written in raw (rotated) pixel orientation and gets uploaded sideways/upside
     down. User photos arrive correctly oriented and must stay that way. If — and only if — `sips` is genuinely unavailable and
     you must fall back to Python, call `ImageOps.exif_transpose(img)` to bake the
     orientation into the pixels **before** saving.
   - **`sips` availability:** `sips` is macOS-only and is absent in the Cowork
     sandbox **and on the device-side Linux VM** (`device_bash`) alike — check
     `command -v sips` before calling it, every run. If unavailable: PIL/Pillow
     **read-only** checks (dimensions, format) are fine; for resize, use
     `ImageOps.exif_transpose(img)` first, then `img.save(…, quality=95)`, and
     verify orientation afterward. HEIC needs the `pillow-heif` plugin
     (`pip install pillow-heif`, then `from pillow_heif import register_heif_opener;
     register_heif_opener()`); ImageMagick 6 on the VM has no HEIC delegate.
   - **Verify orientation after every resize.** After downscaling, read the new
     dimensions (`sips -g pixelWidth -g pixelHeight [file]`) and confirm the
     portrait/landscape relationship matches the original (a portrait source must
     stay W < H). If it flipped, the orientation was mishandled — re-stage the
     photo with `sips`.
   - **Delete the originals to avoid duplicates.** Once the numbered `01..n` files
     exist and are verified (correct size/format), delete the original
     un-numbered source files **that live in the item folder** (e.g.
     `IMG_1234.heic`) so only the upload-ready numbered set remains. Delete an
     original only after its staged counterpart exists; never delete the numbered
     staged files; never delete unrelated files.
   - **Delete the consumed temp source folder (A0b scans only).** If the photos
     were sourced from a **temporary discovery folder** found by the A0b scan
     (a temp photo subfolder inside the listing base folder), delete that whole
     folder now — **but only after** the numbered `01..n` copies exist in the item
     folder and are verified (correct size/format/orientation). Its photos are
     safely staged into the item folder, and removing it keeps the workspace clean
     and prevents the next "just list something" run from re-listing the same item.
     **Delete by the exact absolute path you recorded in A0b** — do not re-derive
     the folder from the item slug (the temp folder's name and the slug usually
     differ). Scope the deletion tightly: remove **only** that one stored
     temp-folder path; **never** delete `Listings/`, any item folder, or a
     folder you did not source from. Do **not** delete a folder the user explicitly
     named as an external source (only auto-discovered temp folders inside the base
     folder are consumed) — if in doubt, leave it and tell the user it can be
     removed.
   - **EPERM fallback (Cowork / network mounts).** If the `rm` fails with
     "Operation not permitted" (EPERM — expected on cloud-synced or
     File-Provider mounts), do **not** retry or escalate. Instead: (1) write a
     **`.consumed-[YYYY-MM-DD]-[slug]`** marker file into the temp folder (writes
     succeed even when deletes don't on this mount), (2) tell the user the folder
     could not be removed automatically and they should delete it manually. The
     `.consumed*` marker ensures the A0b scan skips this folder on the next run,
     preventing the same item from being re-listed.
   - Record the staged paths in `PHOTO_FILES`, comma-separated, in order —
     **as paths the browser upload tool can read.** In the Cowork container
     that is the connected folder's mount under `/mnt/user-data/uploads/…`;
     `/tmp/…` copies and device-side paths are rejected with "only files this
     session is allowed to read" (three 2026-08-30 runs). When the staged
     photos live only on the device, transfer them (`device_stage_files`) and
     record the resulting uploads path. Do this **before** running the
     validator — it checks that every `PHOTO_FILES` entry exists, so validating
     first produces spurious "photo missing on disk" errors.
   - **The item folder must be reachable by the browser upload tool**, which only
     accepts files the session has shared — i.e. a folder the user connected for
     this conversation (the typical Cowork listing folder) or the session's
     uploads/outputs. Saving the run folder under a connected `Listings/` folder
     works (the normal case). If the base folder is NOT connected, the listers'
     `file_upload` will be rejected — warn the user that photos will need manual
     upload. Connecting a folder **mid-conversation has been observed not to
     propagate** to the upload tool's allowlist: if the folder
     wasn't connected when the conversation started, photo upload likely needs a
     fresh conversation rather than a late connect.

3. **Write the action file** using the format defined below.

   **Then re-read it against the draft the user approved, field by field.** The
   action file is the sole handoff — whatever it says is what gets listed, and
   the approved draft text in the conversation counts for nothing once they
   diverge. Check at minimum: titles, all prices, `SHIPPING_KA_METHODS`,
   `SHIPPING_KA_SIZE`, `VINTED_PACKAGE_SIZE`, `SHIPPING_EBAY_POLICY`,
   condition values. In the 2026-07-24 Philips Hue run the approved draft said
   "Hermes Päckchen + DHL Paket 2 kg" while the action file said "DHL Paket
   2 kg, Hermes S-Paket" — the lister faithfully deselected the Päckchen the
   user had approved. If a value changed after approval for a good reason, tell
   the user; never let the two disagree silently.

4. **Validate the action file — mandatory gate.** Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_action_file.py" <path to listing.md>`.
   (The validator finds the seller config on its own by walking up from the
   action file; pass a config path as a second argument only if it lives
   elsewhere.)
   If that path does not exist, the plugin root did not resolve for this
   environment (in the Cowork sandbox it is
   `/sessions/<id>/mnt/.remote-plugins/plugin_*/scripts/validate_action_file.py`);
   locate it once with
   `find / -name validate_action_file.py -path '*plugin*' 2>/dev/null | head -1`
   and use that path. If the script only exists in a different environment
   than the action file (plugin in the container, `listing.md` on the device),
   copy `listing.md` and the seller config to where the script is and validate
   there. Never skip the gate because the path didn't resolve.

   On exit 1, fix every reported error in the file and re-run until it exits 0
   — never hand a failing file to the listers.

   **Warnings do not block, but every warning must be resolved before handoff
   — either fix the file or state the reason to the user.** Do not simply list
   them and move on. A warning here is nearly always a real drafting mistake:
   a Klein item without Hermes Päckchen, a `VINTED_PACKAGE_SIZE` that
   contradicts `SHIPPING_KA_SIZE`, a Vinted price below the eBay price. All
   three shipped wrong in the 2026-07-24 Philips Hue run because the warnings
   were treated as informational. If a warning is genuinely the intended
   exception (a Klein item that really needs a box; a rigid item that needs a
   larger Vinted size), say so explicitly in the draft summary so the user can
   object.

5. **Tell the user** the path where the file was saved.

6. **Immediately continue** with the kleinanzeigen-lister, ebay-lister, and
   vinted-lister skills for the applicable platforms — that is the canonical
   order (KA first, then eBay, then Vinted, matching the /list-item command).
   Do not wait for the user
   to invoke anything — the approval in Step C is the trigger for everything
   that follows.

   **A browser-tooling outage pauses the run; it does not fail it.** If the
   browser tools are unavailable (MCP not connected, a permission classifier
   temporarily down, a model-unavailable error), the drafting work still
   stands: the action file is written and the photos are staged. Say the run is
   paused at platform X, and resume from that same platform when the tools come
   back — do not re-draft, re-stage, or report the run as failed. The lister skills upload the staged photos from
   `PHOTO_FILES`; if it is `NONE`, drafts are saved without photos and the
   user adds them manually when reviewing.

7. **`feedback.md` is your deliverable, not the listers'.** The listers write it
   when they finish normally (see their skills), but the obligation is the
   drafter's and it is **unconditional**: if the run ends for any other reason —
   the user stops it, a platform is skipped, tooling stays down, you run out of
   context, only the draft was wanted — write `feedback.md` yourself into the run
   folder before you stop, describing how far the run got and why it ended.
   Never end a run with the folder lacking one.

   This is the single most-violated rule in the plugin's history. Across
   2026-07-24 … 08-17, **twenty runs produced no `feedback.md` at all** until the
   user asked weeks later; the files then had to be reconstructed from compacted
   sessions and several are admittedly unreliable. Writing learnings to project
   memory instead does **not** discharge this — both get written, and the run
   folder is the one the developer reads.

## Action file format

Write this file exactly. Every field must be present. Use `NONE` only when a
field genuinely does not apply (e.g., shipping fields when SHIPPING_OFFERED is
no, KA_TITLE when ITEM_TITLE is already ≤ 65 characters, or VINTED_TITLE when
ITEM_TITLE is already ≤ 50 characters). Do not abbreviate the description blocks.
Omit description sections entirely for platforms with `*_APPLIES=no`.

```
<!-- LISTING ACTION FILE v1 -->
<!-- Generated: [ISO 8601 timestamp] -->
<!-- Status: APPROVED -->

# ACTION: List [ITEM_TITLE]

## FIELDS
PLUGIN_VERSION: [copy the version verbatim from the **Plugin version:** line at the top of this skill — that line is authoritative. Never guess, never write "unbekannt" while that line is present]
ITEM_TITLE: [verbatim canonical title as it will appear on eBay, ≤ 80 chars]
KA_TITLE: [shorter title ≤ 65 chars for Kleinanzeigen / NONE if ITEM_TITLE already fits]
VINTED_TITLE: [shorter title ≤ 50 chars for Vinted / NONE if ITEM_TITLE already fits]
EBAY_PRICE: [e.g. 44.99]
EBAY_QUANTITY: [how many identical units are for sale, e.g. 1 / 2 — default 1. eBay is the only platform with a quantity field]
KA_PRICE: [e.g. 45]
CONDITION_TEXT_DE: [verbatim German condition text]
CONDITION_TEXT_EN: [verbatim English translation of condition text]
ZUSTANDSBESCHREIBUNG_DE: [condition only — no accessories — for eBay Zustandsbeschreibung field]
EBAY_CONDITION: [eBay condition dropdown label — Neu / Neu: Sonstige (siehe Artikelbeschreibung) / Gebraucht / Defekt — per the unified condition table / NONE if EBAY_APPLIES is no]
CONDITION_DROPDOWN_KA: [Neu / Sehr Gut / Gut / In Ordnung / Defekt]
LISTING_TYPE: [Sofort-Kaufen / Auktion]
AUCTION_START_PRICE: [e.g. 100.00 / NONE]
SHIPPING_OFFERED: [yes / no]
SHIPPING_SCOPE: [DE-only / DE+EU / NONE]
SHIPPING_KA_SIZE: [Klein / Mittel / Groß / NONE]
SHIPPING_KA_METHODS: [e.g. "DHL Paket 2 kg, Hermes S-Paket" / NONE]
SHIPPING_EBAY_POLICY: [exact policy name from the seller config's ebay_shipping_policies, verbatim / NONE]
EBAY_RETURNS: [ebay_returns from the seller config, e.g. No Return Accepted / NONE if EBAY_APPLIES is no]
EBAY_CATALOG_PRODUCT: [catalog product name / NONE]
EBAY_CATALOG_EAN: [EAN / NONE]
EBAY_CATEGORY_HINT: [category path or search term for the ebay-lister to steer to — use when the prelist suggestion is known-wrong (Leerbox, cross-category items) / NONE]
PHOTO_COUNT: [number]
PHOTO_FILES: [comma-separated absolute paths to the staged photos inside the item folder (NN.jpg …), in display order / NONE]
LOCATION: [location from the seller config, or location_zip if the form needs a ZIP]
KA_DIREKT_KAUFEN: [yes / no — ka_direkt_kaufen from the seller config / NONE when no shipping]
EBAY_APPLIES: [yes / no]
KA_APPLIES: [yes / no]
VINTED_APPLIES: [yes / no]
VINTED_PRICE: [e.g. 44.99]
VINTED_CONDITION: [Neu, mit Etikett / Neu / Sehr gut / Gut / Zufriedenstellend / Nicht voll funktionsfähig / NONE]
VINTED_CATEGORY: [exact leaf category path on vinted.de, e.g. "Elektronik > Videospiele & Konsolen > Controller" / NONE]
VINTED_SHIPPING: [Vinted-Versand / Selbst verschicken / Abholung / NONE]
VINTED_BRAND: [brand name as it would appear in Vinted's brand dropdown / NONE]
VINTED_BRAND_FALLBACK: [Markenname nutzen (use VINTED_BRAND as a custom brand name — for real brands not in Vinted's database) / Keine Marke erkannt / Keine Marke / NONE]
VINTED_COLOR: [one or two colors from Vinted palette, comma-separated, e.g. "Schwarz" or "Schwarz, Silber" / NONE]
VINTED_PLATFORM: [gaming platform if category requires it, e.g. "PS5" / NONE]
VINTED_MATERIAL: [material/composition for apparel & shoes when known, e.g. "100% Schurwolle" — never guessed from EAN / NONE]
VINTED_SIZE: [apparel/shoe size as shown in Vinted's Größe selector, e.g. "48" or "M" or "42" / NONE for non-apparel]
VINTED_PACKAGE_SIZE: [Klein / Mittel / Groß — derived from SHIPPING_KA_SIZE / NONE]

===EBAY_DESCRIPTION_START===
[Complete verbatim HTML — German block + <hr> + English block (or just the
one configured block, no <hr>, under german-only / english-only).
Each block starts with <p><strong>[title]</strong></p>.
Include all tags. Both disclaimers in <small> tags.
Omit this section entirely if EBAY_APPLIES is no.]
===EBAY_DESCRIPTION_END===

===KA_DESCRIPTION_START===
[Complete verbatim plain text, German only.
First line is the item title (plain text).
No "@" character anywhere — Kleinanzeigen rejects "@" in the description on
publish. Replace it: "4K@60Hz" → "4K bei 60Hz" or "4K/60Hz". (eBay and Vinted
accept "@"; only this KA block must avoid it.)
Disclaimer at end, verbatim Kleinanzeigen version.
Omit this section entirely if KA_APPLIES is no.]
===KA_DESCRIPTION_END===

===VINTED_DESCRIPTION_START===
[Complete verbatim plain text. No HTML. Bilingual: German block (title on first
line, description, condition, eBay German disclaimer in plain text), then --- on
its own line, then English block (title on first line, description, condition,
eBay English disclaimer in plain text). Under german-only / english-only only
that block, no ---.
Omit this section entirely if VINTED_APPLIES is no.]
===VINTED_DESCRIPTION_END===
```
