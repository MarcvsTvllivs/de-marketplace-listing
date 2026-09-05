<!-- Seller configuration template for the de-marketplace-listing plugin.
     The /listing-setup command copies this file to
       [listing folder]/.claude/de-marketplace-listing.local.md
     and fills in your values. Every value below is a placeholder — replace it.
     The listing-drafter reads this file at the start of every run; the
     action-file validator reads it to check drafts against your settings. -->
---
# ── Which platforms you sell on ──────────────────────────────────────────────
platforms: ebay, kleinanzeigen, vinted   # any subset of: ebay, kleinanzeigen,
                                # vinted. Only these are offered per run;
                                # add one later by editing this line and
                                # (for ebay) filling the policies below

# ── Where you are ────────────────────────────────────────────────────────────
location: Musterstadt           # city for the platforms' location/filter field
location_zip: 12345 Musterstadt # used when a form requires a ZIP code
pickup_area: Musterstadt-Altstadt  # named in the Kleinanzeigen pickup sentence
                                # ("Abholung in [pickup_area] ...") — usually
                                # more specific than `location`

# ── How your listings read ───────────────────────────────────────────────────
languages: bilingual            # bilingual = German block + English block on
                                # eBay/Vinted | german-only = German only
disclaimers: no                 # yes = end every description with the
                                # warranty-exclusion disclaimers from
                                # templates/disclaimers.md (a template commonly
                                # used by German private sellers — NOT legal
                                # advice; see the README before enabling)

# ── Selling preferences ──────────────────────────────────────────────────────
pricing_style: psychological    # psychological = .99 prices on eBay and on
                                # drafter-derived Vinted prices | verbatim =
                                # keep your stated prices as-is
ka_direkt_kaufen: yes           # yes/no — enable Kleinanzeigen "Direkt kaufen"
                                # (buy-now with Käuferschutz) on shipped
                                # Festpreis listings
ebay_returns: No Return Accepted  # the returns option to select on eBay,
                                  # exactly as your form labels it

# ── Your eBay shipping policies (business policies), by size tier ────────────
# Only needed when `platforms` includes ebay. The drafter estimates each item's
# shipped size/weight and picks a policy from this ladder; the ebay-lister
# selects it BY NAME, so every name must match a policy in your eBay account
# VERBATIM (Mein eBay → Konto → Rahmenbedingungen). See the README section
# "eBay shipping policies" for how to set these up. Delete any tier you don't
# have — the drafter then uses the nearest configured tier (preferring the
# larger one) and tells you. `standard` is the default tier and must exist.
ebay_shipping_policies:
  letter_minimal: Großbrief DE & EU            # smallest, flat — fits a letter
  letter_large: Maxibrief DE & EU              # up to 35 × 25 × 5 cm, 1 kg
  standard: Paket bis 5 kg DE & EU             # medium box — the default
  standard_de_only: Paket bis 5 kg DE          # medium box, DE-only scope
  larger: Paket bis 10 kg DE & EU              # heavier / larger box
  largest: Paket bis 31,5 kg DE & EU           # heavy and/or large
---

# Notes

Anything below the frontmatter is ignored by the plugin — use it for your own
notes (e.g. what each eBay policy contains, or reminders about your account).
