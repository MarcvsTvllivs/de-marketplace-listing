# DE Marketplace Listing Plugin

Automates the creation of second-hand listings on **eBay.de**, **Kleinanzeigen.de**,
and **Vinted.de** from a single drafting session.

---

## How it works

1. **listing-drafter** — you describe the item; Claude researches the product,
   drafts all descriptions, confirms prices and shipping, and saves a single
   action file (`.md`) to your project's `Listings/` folder.
2. **ebay-lister / kleinanzeigen-lister / vinted-lister** — each skill reads
   the action file, fills in the corresponding platform's form, uploads your
   photos, and saves a draft. No platform receives content the other
   platforms don't have; no content decisions are made at this stage.
3. The drafts are presented for you to review and publish yourself. The plugin
   never publishes and never offers to — it stops at ready-to-review drafts.

**Model recommendation: use an Opus-class model for the lister steps.** The
browser automation holds a lot of form state at once and has to recognise
silent failures (a field that looks filled but never auto-saved). Opus 4.8 has
run this workflow start-to-finish without intervention; Sonnet-class runs have
repeatedly needed 50+ turns for one platform and exhausted their context
mid-draft. Your choice — but that is where the difference shows.

**"Just list something."** If you don't name a specific item, just drop the item's
photos into a subfolder of your listing folder and say "list something" — the
drafter scans for those temporary photo folders, identifies the item from the
photos, and works from them (no "what do you want to list?" / "where are the
photos?" questions). After the run it stages the photos into the per-item
`Listings/` folder and removes the temporary folder.

Each run lives in its own folder under `Listings/` —
`Listings/[YYYY-MM-DD]-[item]/` — holding the action file (`listing.md`), the
processed photos, and a short `feedback.md` the skills write at the end of the
run (candid developer notes on what worked and what was awkward, so the plugin
can keep improving). Point the plugin's maintainer at those `feedback.md` files
to drive the next round of fixes.

---

## Configuration — run `/listing-setup` first

Everything seller-specific lives in one config file that the drafter and the
action-file validator read on every run:

```
[your listing folder]/.claude/de-marketplace-listing.local.md
```

Run the **`/listing-setup`** command once **from your listing folder** (the
folder your item photos and the `Listings/` archive live in) — it interviews
you, writes this file, and drops a `CLAUDE.md` into the folder so later
sessions treat "list this" as a plugin run. Re-run it anytime to change values
(or edit the file directly; the format reference is
`templates/config-template.md`). The fields:

| Field | What it controls |
|---|---|
| `platforms` | Which of `ebay`, `kleinanzeigen`, `vinted` you sell on — only these are offered per run; add one later by re-running `/listing-setup` |
| `location` / `location_zip` | The location field on eBay/Kleinanzeigen (ZIP form when required) |
| `pickup_area` | The area named in the Kleinanzeigen pickup sentence ("Abholung in …") |
| `languages` | `bilingual` (German + English blocks on eBay/Vinted), `german-only`, or `english-only` (Kleinanzeigen is always German) |
| `disclaimers` | `yes`/`no` — append the legal disclaimers (see below) |
| `pricing_style` | `psychological` (.99 prices) or `verbatim` |
| `ka_direkt_kaufen` | Enable Kleinanzeigen "Direkt kaufen" on shipped Festpreis listings |
| `ebay_returns` | The returns option to select on eBay, verbatim |
| `ebay_shipping_policies` | Your eBay business-policy names, by size tier (see guide below) |

Without a config file, the drafter asks for the values it needs per run and
offers to save them; eBay listing is blocked until shipping policies are
configured.

## Prerequisites

### Chrome extension
All three lister skills control the browser via the Claude-in-Chrome MCP
extension. Install it and keep Chrome open with the extension active before
starting a listing session.

### Platform accounts
You need active seller accounts on each platform you want to list on. The
skills do not create accounts.

### eBay shipping policies — setup guide (required for eBay)

The eBay lister selects a shipping policy **by name**, so the policies must
already exist in your eBay account as **business policies** (Rahmenbedingungen).
The drafter estimates each item's shipped size and weight and picks the policy
of the matching tier from your config, defaulting to the `standard` tier and
only going smaller or larger when it's confident.

**One-time setup in eBay:**

1. Go to **Mein eBay → Konto → Rahmenbedingungen** (business policies). If you
   have never used business policies, opt in there first.
2. Create one **Versandrahmenbedingung** (shipping policy) per size tier you
   actually ship. A useful ladder, from small to large:

   | Config tier | Typical contents |
   |---|---|
   | `letter_minimal` | Smallest, flat — fits a normal letter (Großbrief) |
   | `letter_large` | Maxibrief / Päckchen — cables, small peripherals, most accessories |
   | `standard` | Medium box (e.g. DHL Paket up to 5 kg), DE + EU — **required; the default** |
   | `standard_de_only` | Same as `standard` but DE-only scope (optional) |
   | `larger` | Heavier / larger box (e.g. DHL Paket 10 kg) |
   | `largest` | Heavy and/or bulky (e.g. DHL Paket 31,5 kg) |

   Name them whatever you like — you'll map your names to these tiers in the
   config. Only `standard` is required; skip tiers you never ship. In each
   policy, set the carrier services, prices, and shipping scope (DE / DE+EU)
   you actually offer.
3. Enter the exact policy names in `/listing-setup` (or the config file's
   `ebay_shipping_policies` block). Names must match **verbatim** — exact
   spacing and casing.

If a chosen policy name doesn't match one in your account at listing time, the
skill lists the available ones and asks you to pick — it never guesses.

---

## First-time Vinted setup (do this once)

Vinted triggers email and phone number verification the first time you interact
with the listing form on a new account:

- **Email verification** is triggered by clicking a category for the first time.
- **Phone verification** is triggered by the first submission attempt.

Both redirect you away from the listing form — **wiping everything you've
filled in** with no autosave. Once both verifications are complete they never
recur.

**Before running the vinted-lister for the first time on an account:**
go to your Vinted profile → Account settings → verify your email address and
phone number. The skill will then run without interruption.

---

## Photos

The skills upload your photos automatically (since v2.4). Each listing run gets
its **own folder** — `Listings/[YYYY-MM-DD]-[item]/` — holding both the action
file (`listing.md`) and the upload-ready photos (`01.jpg`, `02.jpg`, …). The
drafter stages the photos directly in that folder (no separate `photos/`
subfolder), converts HEIC to JPEG (iPhone photos — Vinted rejects HEIC),
downscales anything over 8 MB, then deletes the originals from the folder so
there are no duplicates.

For automatic upload to work, the photo files must be reachable by the browser
upload tool, which only accepts files the session has shared — i.e. **the
`Listings/` folder must be one you've connected to the session** (your usual
listing folder in the desktop app).

**Photos pasted into chat** can't be written to disk faithfully (Claude receives
them as images, not files), so if your only photos are chat attachments the
drafter will tell you the exact item-folder path and ask you to drop the
originals in there — then it stages them automatically. If no on-disk photos can
be obtained, the drafts are saved without photos and you add them manually. The
skills will tell you which photos need manual upload.

**Workflow:**
1. The skills save drafts with your photos uploaded.
2. You open each draft and review content and photos.
3. You publish each draft yourself. The plugin does not publish — it presents the
   ready-to-review drafts and stops.

---

## Legal disclaimers (opt-in)

With `disclaimers: yes` in your config, every generated description ends with
a warranty-exclusion disclaimer in German (and English for eBay and Vinted).
It is a **template commonly used by private sellers in Germany — not legal
advice**. Its protective effect is strongest for private sales of used goods;
for new/unused items a blanket warranty exclusion can be legally ineffective
(§§ 309, 444 BGB set limits). Review whether it fits your situation before
enabling it in `/listing-setup`. With `disclaimers: no`, descriptions carry no
legal boilerplate at all.

---

## Platform-specific notes

### eBay
- Listings are always saved as drafts ("Als Entwurf speichern") — never
  published directly.
- The description is injected as HTML into eBay's rich-text editor. eBay uses
  a Marko.js-based auto-save mechanism — the skill waits for the auto-save XHR
  to fire before continuing, so the draft may take 5–10 seconds longer than
  you might expect.
- eBay's catalog-match step may suggest item properties. The skill accepts only
  properties confirmed in the action file — it does not click "alle übernehmen".
  An EAN often does not auto-resolve to a catalog product on eBay.de, so manual
  category selection is the normal path.
- The condition (Neu / Gebraucht / …) is taken from the action file per item —
  a genuinely new item is listed as "Neu", not defaulted to "Gebraucht".

### Kleinanzeigen
- Listings are saved as drafts ("Entwurf speichern").
- Shipping methods: Kleinanzeigen pre-selects category-recommended methods. The
  skill opens the "Empfehlung für dein Produkt" modal via the chevron on the
  Versandmethoden row, adjusts the pre-checked method checkboxes to match the
  action file, and confirms with "Bestätigen". If the recommendations don't
  include the right methods, it falls back to the "Andere Versandmethoden"
  size picker. Selections are verified via screenshot before saving.

### Vinted
- Listings are saved as hidden drafts using the **"Entwurf speichern"** button
  (not "Hochladen", which publishes immediately). Drafts appear under the
  "Entwürfe" tab on your profile.
- After selecting a category, Vinted loads additional detail fields
  asynchronously (Marke, Zustand, Farbe, and sometimes Plattform). The skill
  waits for these to load and fills them.
- Selecting a premium brand (Apple, Nike, Adidas, etc.) triggers an
  "Echtheitsnachweis" (authenticity) modal — the skill dismisses it
  automatically.
- The shipping size (Klein / Mittel / Groß) is set from the action file and may
  differ from Vinted's pre-selected recommendation.

## Development

Source, evals and release tooling live in the GitHub repository:
https://github.com/MarcvsTvllivs/de-marketplace-listing — see its README for
installing from GitHub and for the maintainer release flow. Every run writes a
`feedback.md`; those files are the input for the next version.
