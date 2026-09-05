# Listing workspace

This folder is the listing base for the `de-marketplace-listing` plugin
(eBay.de, Kleinanzeigen.de, Vinted.de). Its presence marks this directory as the
project root, so per-item runs belong under `./Listings/`.

## Always run listings through the plugin

Any request to sell, list, or draft an item here — including a bare "list this",
"verkauf das", or a folder of photos dropped in with no other instruction — is a
**plugin run**, not a manual browser task. Invoke the skill first, before asking
the user anything and before opening any website.

- **`listing-drafter`** — the entry point (gathers info, writes the action file)
- `ebay-lister`, `kleinanzeigen-lister`, `vinted-lister` — run automatically after
- `/list-item` — the slash command that runs the whole sequence

**Never draft by hand because a skill name is missing.** If the expected skills
are not loaded, say so in your first message and stop — a hand-drafted run
skips the validator and leaves no record.

## What a completed run leaves on disk

Every item gets its own folder, `Listings/[YYYY-MM-DD]-[slug]/`, containing:

| file | written by |
|---|---|
| `listing.md` | drafter (Step D) — must pass `validate_action_file.py` |
| `01.jpg`, `02.jpg`, … | drafter (staged, numbered, in display order) |
| `feedback.md` | the run — **required**, one per item, never shared between items |

A run that ends early still writes `feedback.md` saying how far it got. If a
folder here has no `feedback.md`, that run did not finish properly.

Photos dropped loose in this folder (or in a bare subfolder such as `Lamp/`)
are **input**: the drafter's folder scan picks them up, stages them into a dated
item folder, and consumes the temp folder afterwards.

## Seller config

`.claude/de-marketplace-listing.local.md` holds the platforms you sell on,
location, eBay shipping-policy names, price style and language settings. Read
it at the start of a run — do not re-ask the user for values it already
provides. Re-run `/listing-setup` to change it.
