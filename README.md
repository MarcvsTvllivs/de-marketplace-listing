# de-marketplace-listing

A Claude plugin that lists second-hand items on **eBay.de**, **Kleinanzeigen.de**
and **Vinted.de** from one conversation: you describe the item (or drop its
photos in a folder), Claude researches it, drafts the descriptions, confirms
price and shipping with you, then fills in each platform's form in your own
Chrome and saves **drafts** — never publishes. You review and publish yourself.

Works in **Claude Code** (CLI) and in the **Claude desktop app (Cowork)**. You
pick which of the three platforms you use during setup; the rest is never
offered. Optional legal boilerplate (a warranty-exclusion template common
among German private sellers) is included and off by default.

The user manual — how a run works, prerequisites, eBay business-policy setup,
Vinted first-time verification, photo handling, the disclaimers — is
[plugin-source/README.md](plugin-source/README.md). It ships inside the
plugin.

---

## Installation

These instructions are written so that an agent (Claude Code or Claude in the
desktop app) given only this repository's address can carry them out. Human
readers can follow them just the same.

### Prerequisites (both routes)

- Google Chrome with the **Claude in Chrome** extension installed and Chrome
  open — the lister skills drive the real browser through it.
- Seller accounts on the platforms you want to use, logged in in that Chrome.
- A **listing folder** on disk: any folder where item photos will be dropped
  and where the per-item archive (`Listings/…`) will be written.

### Route A — Claude Code (CLI)

```bash
claude plugin marketplace add MarcvsTvllivs/de-marketplace-listing
```

```bash
claude plugin install de-marketplace-listing@de-marketplace-listing
```

Then, **inside the listing folder**, run `/listing-setup` and answer the
questions (platforms, location, style, eBay shipping policies if eBay is on).
It writes `.claude/de-marketplace-listing.local.md` and a `CLAUDE.md` into the
folder. From then on, `/list-item` — or just "verkauf das" with photos in the
folder — runs the whole sequence.

To update later:

```bash
claude plugin update de-marketplace-listing@de-marketplace-listing
```

### Route B — Claude desktop app (Cowork)

The desktop app installs plugins from a `.plugin` archive. Uploading it is a
click in the app that the human does; an agent can fetch or build the archive
and hand it over.

1. Get the archive. Either download `de-marketplace-listing-<version>.plugin`
   from the latest entry under **Releases** on this repository, or build it
   from a clone:

   ```bash
   git clone https://github.com/MarcvsTvllivs/de-marketplace-listing.git && cd de-marketplace-listing/plugin-source && zip -0 -r -X ../de-marketplace-listing.plugin . -x '.gitignore' -x '.DS_Store'
   ```

2. In the desktop app: **Settings → Plugins → Add → Upload plugin**, choose the
   `.plugin` file, confirm. If an older version is already installed, choose
   **Replace**. Restart the app afterwards — the app keeps the uploaded copy as
   the one it loads.
3. Start a Cowork session **with your listing folder connected** (the plugin
   uploads photos only from folders the session can read) and run
   `/listing-setup`. Answer the questions; it writes the seller config and a
   `CLAUDE.md` into the folder.
4. Do the one-time platform steps from the manual: Vinted email + phone
   verification (before the first Vinted run), and eBay business policies (if
   eBay is on).

### Verifying the install

Ask Claude to "list something" with a photo folder in the listing folder. The
first thing it should do is invoke the `listing-drafter` skill and show a
`Plugin version: <version>` line matching the version you installed. If it
starts drafting by hand instead, the plugin is not loaded.

---

## What's inside

```
plugin-source/            the plugin (this is what gets installed)
  commands/               /list-item, /listing-setup
  skills/                 listing-drafter, ebay-lister, kleinanzeigen-lister, vinted-lister
  scripts/                validate_action_file.py — deterministic gate before any browser work
  templates/              seller-config template, legal disclaimers, listing-folder CLAUDE.md
  README.md               the user manual
evals/                    drafter evals + golden fixtures (not shipped)
scripts/release.sh        maintainer release script (bumps versions, validates, builds the archive)
```

Nothing seller-specific lives in the plugin. Location, platforms, eBay policy
names, language and pricing preferences are all in the config file that
`/listing-setup` writes into *your* listing folder.

## Feedback loop

Every run ends by writing a candid `feedback.md` into the item's folder
(`Listings/<date>-<item>/`). Those notes are the raw material for the next
version — send them along, or open an issue quoting them.

## Maintainer notes

`scripts/release.sh <version>` bumps the version in plugin.json, the golden
fixture and every SKILL.md, runs the validator gate, deploys to the local
desktop-app plugin directories (maintainer's machine only), and builds the
`.plugin` archive. Commit, push, attach the archive to a GitHub release, and —
for the maintainer's own desktop app — re-upload the archive under
Settings → Plugins.
