---
description: One-time seller configuration for the marketplace listing plugin (platforms, location, eBay shipping policies, preferences).
---

# /listing-setup — Configure the plugin for this seller

Create (or update) the seller configuration file that the listing-drafter and
the action-file validator read on every run:

```
[listing folder]/.claude/de-marketplace-listing.local.md
```

The **listing folder** is the folder the listing runs happen in — the working
directory that contains (or will contain) the `Listings/` subfolder. If the
current working directory doesn't look like it (no `Listings/` folder and the
user hasn't confirmed it), ask where their listing folder is before writing.
In the Claude desktop app (Cowork) that is the folder the user connected to the
session; in Claude Code it is the project directory.

## Steps

1. **Check for an existing config.** If
   `.claude/de-marketplace-listing.local.md` exists, read it, show the current
   values, and ask which to change — don't re-interview from scratch. Preserve
   any notes below the frontmatter.

2. **Interview.** Use `${CLAUDE_PLUGIN_ROOT}/templates/config-template.md` as
   the canonical field list and format. Ask in short groups (use
   multiselect/option questions where natural):

   - **Platforms** (first): which of eBay.de, Kleinanzeigen.de, Vinted.de the
     user sells on (`platforms`, multiselect, all three offered). Only the
     chosen ones are offered per run; they can add one later by re-running this
     command. Skip every later question that belongs to a platform they did
     not pick.
   - **Location:** city (`location`), ZIP form for forms that require it
     (`location_zip`), and — Kleinanzeigen only — the pickup area named in the
     pickup sentence (`pickup_area`, usually a district of the city).
   - **Listing style:** `languages` (bilingual German+English blocks on
     eBay/Vinted, german-only, or english-only — Kleinanzeigen stays German
     either way), and `disclaimers` (yes/no). For disclaimers,
     state plainly: they are a warranty-exclusion template commonly used by
     German private sellers, **not legal advice**; their protective effect is
     strongest for private sales of used goods and can be legally ineffective
     for new items. The user must actively choose yes.
   - **Selling preferences:** `pricing_style` (psychological .99 vs verbatim);
     Kleinanzeigen only: `ka_direkt_kaufen` (yes/no); eBay only:
     `ebay_returns` (the exact label of their returns choice on eBay, default
     "No Return Accepted").

3. **eBay shipping policies (only when `platforms` includes ebay).** The
   plugin selects eBay shipping policies **by name**, so they must already
   exist in the user's account under **Mein eBay → Konto → Rahmenbedingungen**
   (business policies). Ask the user to name their policies per size tier
   (`letter_minimal` / `letter_large` / `standard` / `standard_de_only` /
   `larger` / `largest` — see the template's comments for what each tier
   means). Rules:
   - Names must match the account **verbatim** — exact spacing and casing.
   - `standard` (the default tier) is required; the other tiers are optional
     and are simply omitted from the config when the user has no such policy.
   - If the user has no business policies yet, point them to the README
     section **"eBay shipping policies"** for a step-by-step guide to creating
     the ladder, and offer to leave `ebay_shipping_policies` unset for now —
     eBay listings will then be blocked until they re-run `/listing-setup`.
   - If the user has Chrome connected, offer to read the policy names from
     their eBay business-policies page instead of asking them to type them.

4. **Write the config.** Copy the template's structure, fill in the answers,
   create the `.claude/` directory if needed, and save. Show the user the
   final file contents and its path.

5. **Mark the listing folder.** If the listing folder has no `CLAUDE.md`, copy
   `${CLAUDE_PLUGIN_ROOT}/templates/listing-folder-CLAUDE.md` there as
   `CLAUDE.md` and create an empty `Listings/` subfolder. This is what makes a
   later session treat "list this" as a plugin run instead of a manual browser
   task. If a `CLAUDE.md` already exists, leave it alone and tell the user the
   template exists.

6. **Point out the remaining one-time steps** from the README: the Chrome
   extension must be installed and Chrome open; Vinted email/phone
   verification must be done once before the first Vinted run.

7. **Do not touch anything else.** No listing run, no browser navigation
   (except the optional policy read-out in step 3), no changes to existing
   listings.
