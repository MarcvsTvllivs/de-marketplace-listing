#!/usr/bin/env python3
"""Deterministic validator for listing action files (LISTING ACTION FILE v1).

Checks every machine-checkable invariant from listing-drafter/SKILL.md:
field presence, enums, price formats, title lengths, verbatim disclaimers,
description-block structure, photo staging (PHOTO_FILES paths exist, sizes,
formats, order), and cross-field logic.

Seller-specific checks (platforms, eBay policy names, location, pickup area,
pricing style, disclaimers on/off, languages) come from the seller config
(.claude/de-marketplace-listing.local.md), found by walking up from the action
file — or passed explicitly as the second argument. Without a config those
checks degrade to warnings.

Usage:
    python3 validate_action_file.py <action-file.md> [seller-config.md]

Exit codes: 0 = pass (warnings allowed), 1 = one or more errors, 2 = unreadable.
"""

import os
import re
import sys

MB = 1024 * 1024

REQUIRED_FIELDS = [
    "PLUGIN_VERSION",
    "ITEM_TITLE", "KA_TITLE", "VINTED_TITLE", "EBAY_PRICE", "KA_PRICE",
    "CONDITION_TEXT_DE", "CONDITION_TEXT_EN", "ZUSTANDSBESCHREIBUNG_DE",
    "EBAY_CONDITION", "CONDITION_DROPDOWN_KA", "LISTING_TYPE",
    "AUCTION_START_PRICE",
    "SHIPPING_OFFERED", "SHIPPING_SCOPE", "SHIPPING_KA_SIZE",
    "SHIPPING_KA_METHODS", "SHIPPING_EBAY_POLICY", "EBAY_RETURNS",
    "EBAY_CATALOG_PRODUCT",
    "EBAY_CATALOG_EAN", "EBAY_CATEGORY_HINT",
    "PHOTO_COUNT", "PHOTO_FILES", "LOCATION", "KA_DIREKT_KAUFEN",
    "EBAY_APPLIES", "KA_APPLIES", "VINTED_APPLIES", "VINTED_PRICE",
    "VINTED_CONDITION", "VINTED_CATEGORY", "VINTED_SHIPPING", "VINTED_BRAND",
    "VINTED_BRAND_FALLBACK", "VINTED_COLOR", "VINTED_PLATFORM",
    "VINTED_MATERIAL", "VINTED_SIZE", "VINTED_PACKAGE_SIZE",
]

ENUMS = {
    "CONDITION_DROPDOWN_KA": {"Neu", "Sehr Gut", "Gut", "In Ordnung", "Defekt"},
    "LISTING_TYPE": {"Sofort-Kaufen", "Auktion"},
    "SHIPPING_OFFERED": {"yes", "no"},
    "EBAY_APPLIES": {"yes", "no"},
    "KA_APPLIES": {"yes", "no"},
    "VINTED_APPLIES": {"yes", "no"},
    "SHIPPING_SCOPE": {"DE-only", "DE+EU", "NONE"},
    "SHIPPING_KA_SIZE": {"Klein", "Mittel", "Groß", "NONE"},
    "VINTED_CONDITION": {"Neu, mit Etikett", "Neu", "Sehr gut", "Gut",
                         "Zufriedenstellend", "Nicht voll funktionsfähig", "NONE"},
    "VINTED_SHIPPING": {"Vinted-Versand", "Selbst verschicken", "Abholung", "NONE"},
    "VINTED_PACKAGE_SIZE": {"Klein", "Mittel", "Groß", "NONE"},
    "VINTED_BRAND_FALLBACK": {"Markenname nutzen", "Keine Marke erkannt",
                              "Keine Marke", "NONE"},
    "KA_DIREKT_KAUFEN": {"yes", "no", "NONE"},
}

CONFIG_BASENAME = os.path.join(".claude", "de-marketplace-listing.local.md")

# Seller config, loaded in main(). None when no config file was found — the
# seller-specific checks then degrade to warnings.
CFG = None


def load_config(action_path, explicit=None):
    """Parse the seller config's YAML frontmatter (flat keys plus one level of
    nesting for ebay_shipping_policies). Found by walking up from the action
    file unless a path is passed explicitly. Returns a dict or None."""
    path = explicit
    if path is None:
        d = os.path.dirname(os.path.abspath(action_path))
        while True:
            cand = os.path.join(d, CONFIG_BASENAME)
            if os.path.isfile(cand):
                path = cand
                break
            parent = os.path.dirname(d)
            if parent == d:
                return None
            d = parent
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    m = re.search(r"^---\n(.*?)\n---", raw, re.S | re.M)
    if not m:
        return None
    cfg, current = {}, None
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        line = re.sub(r"\s+#.*$", "", line.rstrip())
        key, sep, val = line.partition(":")
        if not sep:
            continue
        indented = line[:1] in (" ", "\t")
        key, val = key.strip(), val.strip()
        if indented and current is not None:
            cfg[current][key] = val
        elif val == "":
            cfg[key] = {}
            current = key
        else:
            cfg[key] = val
            current = None
    cfg["_path"] = path
    return cfg


def lang():
    """'bilingual' (default) / 'german-only' / 'english-only'."""
    return (CFG or {}).get("languages") or "bilingual"


def wants_de():
    return lang() != "english-only"


def wants_en():
    return lang() != "german-only"


def bilingual():
    return wants_de() and wants_en()


def disclaimers_mode():
    """'on' / 'off' / 'unknown' (no config found)."""
    if CFG is None:
        return "unknown"
    return "on" if CFG.get("disclaimers", "no") == "yes" else "off"

# eBay condition dropdown labels are category-dependent, so this is a soft
# allow-list: an unknown value warns rather than errors, but it must be present
# and non-NONE whenever eBay applies.
EBAY_CONDITION_KNOWN = {
    "Neu",
    "Neu: Sonstige (siehe Artikelbeschreibung)",
    "Generalüberholt",
    "Gebraucht",
    "Defekt",
    "Neuwertig",
    "Sehr gut",
    "Gut",
    "Akzeptabel",
}

VINTED_PALETTE = {"Schwarz", "Grau", "Weiß", "Creme", "Beige", "Aprikose",
                  "Orange", "Rot", "Pink", "Lila", "Blau", "Grün", "Braun",
                  "Silber", "Gold", "Bunt", "Klar"}

KA_TO_VINTED_SIZE = {"Klein": "Klein", "Mittel": "Mittel", "Groß": "Groß"}

DISCLAIMER_DE_P1 = ("Die Ware wird unter Ausschluss jeglicher Gewährleistung "
                    "verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche "
                    "aus grob fahrlässiger bzw. vorsätzlicher Verletzung von "
                    "Pflichten des Verkäufers sowie für jede Verletzung von Leben, "
                    "Körper und Gesundheit.")
DISCLAIMER_DE_P2_EBAY = "Zwischenverkauf vorbehalten."
DISCLAIMER_DE_P2_KA = ("Zwischenverkauf bleibt stets vorbehalten. Vertragsannahme "
                       "erfolgt bei Versand durch Absendung, bei Abholung durch "
                       "Übergabe.")
DISCLAIMER_EN_P1 = ("This item is sold without any warranty. This exclusion does "
                    "not apply to claims for damages arising from grossly negligent "
                    "or intentional breach of duty by the seller, nor to any injury "
                    "to life, body, or health.")
DISCLAIMER_EN_P2 = "Subject to prior sale."

ALLOWED_PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def normalize(text):
    """Strip HTML tags and collapse whitespace for verbatim-text comparison."""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    fields = {}
    # Parse fields only from the header (before the first description block) —
    # field-shaped lines inside descriptions (e.g. "EAN: ...") must not
    # override FIELDS values.
    header = re.split(r"^===[A-Z_]+_START===", raw, maxsplit=1, flags=re.M)[0]
    for m in re.finditer(r"^([A-Z][A-Z0-9_]+):[ \t]*(.*)$", header, re.M):
        fields[m.group(1)] = m.group(2).strip()
    blocks = {}
    for name in ("EBAY_DESCRIPTION", "KA_DESCRIPTION", "VINTED_DESCRIPTION"):
        m = re.search(rf"==={name}_START===\n(.*?)\n==={name}_END===", raw, re.S)
        if m:
            blocks[name] = m.group(1)
    return raw, fields, blocks


def check_fields(fields):
    for key in REQUIRED_FIELDS:
        if key not in fields:
            err(f"missing field: {key}")
        elif fields[key] == "":
            err(f"empty field: {key}")
    for key, allowed in ENUMS.items():
        val = fields.get(key)
        if val is not None and val not in allowed:
            err(f"{key}: '{val}' not in {sorted(allowed)}")


def check_plugin_version(fields):
    val = fields.get("PLUGIN_VERSION")
    if val and not re.match(r"^\d+\.\d+\.\d+(\+[0-9A-Za-z.-]+)?$", val):
        warn(f"PLUGIN_VERSION '{val}' is not a semver (X.Y.Z, optional +build "
             f"metadata) — should match the version in .claude-plugin/plugin.json")


def check_titles(fields):
    title = fields.get("ITEM_TITLE", "")
    if len(title) > 80:
        err(f"ITEM_TITLE is {len(title)} chars (max 80)")
    kt = fields.get("KA_TITLE", "NONE")
    if fields.get("KA_APPLIES") == "yes":
        effective_ka = kt if kt != "NONE" else title
        if len(effective_ka) > 65:
            err(f"effective Kleinanzeigen title is {len(effective_ka)} chars "
                f"(max 65); KA_TITLE required when ITEM_TITLE exceeds 65")
    vt = fields.get("VINTED_TITLE", "NONE")
    if fields.get("VINTED_APPLIES") == "yes":
        effective = vt if vt != "NONE" else title
        if len(effective) > 50:
            err(f"effective Vinted title is {len(effective)} chars (max 50); "
                f"VINTED_TITLE required when ITEM_TITLE exceeds 50")
        caps = [w for w in re.findall(r"\b[A-ZÄÖÜ]{4,}\b", effective)]
        if caps:
            warn(f"Vinted title contains all-caps words {caps} — Vinted may "
                 f"reject (acronyms like HDMI are fine; brand names are not)")
        # Vinted's filter counts the overall capital share, not just single
        # words — dense model codes (UC-DAC-SFP+, UACC-DAC-SFP10-1M) fail even
        # without any 4+-cap word (2026-07-12 runs).
        letters = [c for c in effective if c.isalpha()]
        if letters:
            share = sum(c.isupper() for c in letters) / len(letters)
            if share > 0.4:
                warn(f"Vinted title is {share:.0%} capitals — Vinted rejects "
                     f"titles with too many capital letters overall (dense "
                     f"model codes); derive a low-caps VINTED_TITLE with "
                     f"descriptive words instead of the model code")


def check_ebay_condition(fields):
    val = fields.get("EBAY_CONDITION")
    if val is None:
        return  # presence handled by check_fields
    if fields.get("EBAY_APPLIES") == "yes":
        if val in ("NONE", ""):
            err("EBAY_APPLIES=yes but EBAY_CONDITION is NONE/empty")
        elif val not in EBAY_CONDITION_KNOWN:
            warn(f"EBAY_CONDITION '{val}' is not a common eBay label "
                 f"{sorted(EBAY_CONDITION_KNOWN)} — fine if it matches the "
                 f"category's dropdown, otherwise the lister will ask")


def check_prices(fields):
    psycho = CFG is not None and CFG.get("pricing_style", "psychological") == "psychological"
    no_cfg = CFG is None
    if fields.get("EBAY_APPLIES") == "yes":
        ep = fields.get("EBAY_PRICE", "")
        if not re.fullmatch(r"\d+(\.\d{1,2})?", ep):
            err(f"EBAY_PRICE '{ep}' is not a valid price")
        elif not re.fullmatch(r"\d+\.99", ep):
            if psycho:
                err(f"EBAY_PRICE '{ep}' must end in .99 (pricing_style: psychological)")
            elif no_cfg:
                warn(f"EBAY_PRICE '{ep}' does not end in .99 — no seller config "
                     f"found to confirm the pricing style")
    if fields.get("KA_APPLIES") == "yes":
        if not re.fullmatch(r"\d+", fields.get("KA_PRICE", "")):
            err(f"KA_PRICE '{fields.get('KA_PRICE')}' must be a whole euro amount")
    if fields.get("VINTED_APPLIES") == "yes":
        vp = fields.get("VINTED_PRICE", "")
        # User-stated prices are kept verbatim (any price with <=2 decimals);
        # only drafter-derived prices must use the pricing style — the validator
        # can't see user intent, so non-.99 is a warning, not an error.
        if not re.fullmatch(r"\d+(\.\d{1,2})?", vp):
            err(f"VINTED_PRICE '{vp}' is not a valid price")
        elif (psycho or no_cfg) and not re.fullmatch(r"\d+\.99", vp):
            warn(f"VINTED_PRICE '{vp}' is not .99-formatted — fine if "
                 f"user-stated, wrong if drafter-derived")
        if fields.get("EBAY_APPLIES") == "yes":
            try:
                if float(vp) < float(fields.get("EBAY_PRICE", "0")):
                    warn(f"VINTED_PRICE {vp} is lower than EBAY_PRICE "
                         f"{fields.get('EBAY_PRICE')} — fine only if the user "
                         f"asked for it; derived prices must match eBay")
            except ValueError:
                pass
    if fields.get("LISTING_TYPE") == "Auktion":
        if not re.fullmatch(r"\d+(\.\d{2})?", fields.get("AUCTION_START_PRICE", "")):
            err("LISTING_TYPE is Auktion but AUCTION_START_PRICE is not a price")


def check_shipping(fields):
    offered = fields.get("SHIPPING_OFFERED")
    if offered == "no":
        if fields.get("EBAY_APPLIES") == "yes":
            err("SHIPPING_OFFERED=no requires EBAY_APPLIES=no")
        if fields.get("VINTED_SHIPPING") not in ("Abholung", "NONE", None):
            err("SHIPPING_OFFERED=no requires VINTED_SHIPPING=Abholung (or NONE)")
    elif offered == "yes":
        if fields.get("SHIPPING_KA_SIZE") == "NONE" and fields.get("KA_APPLIES") == "yes":
            err("SHIPPING_OFFERED=yes but SHIPPING_KA_SIZE is NONE")
        policy = fields.get("SHIPPING_EBAY_POLICY")
        policies = (CFG or {}).get("ebay_shipping_policies") or {}
        if fields.get("EBAY_APPLIES") == "yes":
            if policy in ("NONE", "", None):
                err("EBAY_APPLIES=yes but SHIPPING_EBAY_POLICY is NONE")
            elif policies and policy not in policies.values():
                err(f"SHIPPING_EBAY_POLICY '{policy}' is not a configured eBay "
                    f"policy {sorted(policies.values())}")
            elif not policies:
                warn(f"SHIPPING_EBAY_POLICY '{policy}' cannot be verified — no "
                     f"seller config with ebay_shipping_policies found")
        # Hermes Päckchen is gated on the item being genuinely letter-sized
        # (longest + shortest side <= 37 cm, flat), NOT on SHIPPING_KA_SIZE.
        # v2.6.4 keyed it on Klein and that was wrong in both directions: it
        # forced Päckchen onto rigid Klein items (Shelly, films, Noctua — every
        # one correctly overridden by the run) while the user's actual rule is
        # that Päckchen is simply too small for anything non-flat.
        # The validator cannot measure a parcel, so it checks the one thing it
        # can: that the two platforms agree. Päckchen on KA and a letter tier
        # on eBay are the same physical claim and must travel together.
        letter_tier = {policies.get("letter_minimal"), policies.get("letter_large")} - {None}
        ka_methods = fields.get("SHIPPING_KA_METHODS", "NONE")
        # Unchanged v2.5.7 rule, still user-driven and still one-directional:
        # if eBay says the item is envelope-flat, KA must at least offer the
        # envelope method. The reverse is NOT checked — Hermes Päckchen and
        # eBay's letter tier are different carriers with different size limits,
        # and v2.6.3 deliberately decoupled the two.
        if (fields.get("EBAY_APPLIES") == "yes" and policy in letter_tier
                and fields.get("KA_APPLIES") == "yes" and ka_methods != "NONE"
                and "Hermes Päckchen" not in ka_methods):
            err(f"SHIPPING_EBAY_POLICY '{policy}' is letter-tier but "
                f"SHIPPING_KA_METHODS '{ka_methods}' lacks 'Hermes Päckchen' "
                f"(envelope items use Hermes Päckchen + DHL Paket 2 kg)")
        # Methods are a floor, never an exclusive pair: the buyer picks and pays,
        # so switching off a larger option only costs sales (user rule,
        # 2026-08-17: "If a buyer wants that, let them pay for it. I am not the
        # one paying for it."). Päckchen alone means larger methods were
        # deselected. The v2.6.4 check this replaces asserted the opposite —
        # that every Klein item must carry Päckchen — and fired wrongly on the
        # Shelly, film and Noctua runs, all of which correctly overrode it.
        if (fields.get("KA_APPLIES") == "yes" and ka_methods != "NONE"
                and "Hermes Päckchen" in ka_methods
                and "DHL Paket 2 kg" not in ka_methods):
            warn(f"SHIPPING_KA_METHODS '{ka_methods}' offers 'Hermes Päckchen' "
                 f"but not 'DHL Paket 2 kg' — methods are a floor, not a pair; "
                 f"never switch off a larger method the buyer could choose")
    qty = fields.get("EBAY_QUANTITY")
    if qty is not None and qty != "NONE":
        if not qty.strip().isdigit() or int(qty.strip()) < 1:
            err(f"EBAY_QUANTITY '{qty}' must be a whole number >= 1")
    elif fields.get("EBAY_APPLIES") == "yes":
        warn("EBAY_QUANTITY is absent — defaulting to 1. State it explicitly "
             "when selling more than one identical unit; a count that lives "
             "only in the conversation gets lost at the handoff")
    if fields.get("EBAY_APPLIES") == "yes" and fields.get("EBAY_RETURNS") in ("NONE", ""):
        err("EBAY_APPLIES=yes but EBAY_RETURNS is NONE/empty")
    if (fields.get("KA_APPLIES") == "yes" and offered == "yes"
            and fields.get("KA_DIREKT_KAUFEN") not in ("yes", "no", None)):
        err("KA_APPLIES=yes with shipping but KA_DIREKT_KAUFEN is not yes/no")
    ka_size = fields.get("SHIPPING_KA_SIZE", "NONE")
    v_size = fields.get("VINTED_PACKAGE_SIZE", "NONE")
    if (fields.get("VINTED_APPLIES") == "yes" and ka_size in KA_TO_VINTED_SIZE
            and v_size != "NONE" and KA_TO_VINTED_SIZE[ka_size] != v_size):
        warn(f"VINTED_PACKAGE_SIZE '{v_size}' does not match mapping from "
             f"SHIPPING_KA_SIZE '{ka_size}' (expected {KA_TO_VINTED_SIZE[ka_size]})")


def check_vinted_fields(fields):
    if fields.get("VINTED_APPLIES") != "yes":
        return
    cat = fields.get("VINTED_CATEGORY", "NONE")
    if cat == "NONE":
        err("VINTED_APPLIES=yes but VINTED_CATEGORY is NONE")
    elif ">" not in cat:
        err(f"VINTED_CATEGORY '{cat}' is not a leaf path (no '>')")
    elif cat.strip() in ("Elektronik", "Elektronik > Sonstiges"):
        err(f"VINTED_CATEGORY '{cat}' is a known-invalid (parent-only or "
            f"nonexistent) node")
    colors = fields.get("VINTED_COLOR", "NONE")
    if colors != "NONE":
        parts = [c.strip() for c in colors.split(",")]
        if len(parts) > 2:
            err(f"VINTED_COLOR has {len(parts)} colors (max 2)")
        for c in parts:
            if c not in VINTED_PALETTE:
                err(f"VINTED_COLOR '{c}' not in Vinted palette")
    # Apparel/shoes (signalled by a required Größe) should carry a material when
    # the composition is known. Warn, don't error — material can be genuinely
    # unknown, but it must never be silently skipped (never guessed from EAN).
    if (fields.get("VINTED_SIZE", "NONE") != "NONE"
            and fields.get("VINTED_MATERIAL", "NONE") == "NONE"):
        warn("VINTED_SIZE is set (apparel) but VINTED_MATERIAL is NONE — fill the "
             "material from the care label / research when known (never from EAN)")
    cat = fields.get("VINTED_CATEGORY", "NONE")
    cond = fields.get("VINTED_CONDITION", "NONE")
    if "Powerbanks" in cat and cond not in ("Neu, mit Etikett", "Neu", "NONE"):
        warn(f"VINTED_CATEGORY contains 'Powerbanks' but VINTED_CONDITION is "
             f"'{cond}' — Powerbanks is a new-only category on Vinted; used items "
             f"should set VINTED_APPLIES=no")


def check_photos(fields):
    count_raw = fields.get("PHOTO_COUNT", "")
    if not re.fullmatch(r"\d+", count_raw):
        err(f"PHOTO_COUNT '{count_raw}' is not an integer")
        return
    count = int(count_raw)
    files_raw = fields.get("PHOTO_FILES", "NONE")
    if files_raw == "NONE":
        if count > 0:
            warn(f"PHOTO_COUNT is {count} but PHOTO_FILES is NONE — photos "
                 f"will need manual upload")
        return
    # Paths are absolute; split on commas that precede a path start.
    paths = [p.strip() for p in re.split(r",\s*(?=/)", files_raw)]
    if len(paths) != count:
        err(f"PHOTO_FILES has {len(paths)} paths but PHOTO_COUNT is {count}")
    basenames = []
    for p in paths:
        if not os.path.isfile(p):
            # A path whose very root is absent means we are validating from a
            # different filesystem than the one that staged the photos (the
            # Cowork Linux sandbox cannot see macOS /Users paths). That is an
            # environment mismatch, not a broken action file.
            root = os.path.join(os.sep, p.strip(os.sep).split(os.sep)[0]) if p.startswith(os.sep) else ""
            if root and not os.path.isdir(root):
                warn(f"photo path not resolvable from this environment "
                     f"(no '{root}' here — check it on the host): {p}")
            else:
                err(f"photo missing on disk: {p}")
            continue
        size = os.path.getsize(p)
        if size > 10 * MB:
            err(f"photo over 10 MB (upload tool rejects it): {p} ({size // MB} MB)")
        elif size > 8 * MB:
            warn(f"photo over 8 MB (staging should have downscaled): {p}")
        ext = os.path.splitext(p)[1].lower()
        if ext not in ALLOWED_PHOTO_EXT:
            err(f"photo format '{ext}' not upload-safe (convert to JPEG): {p}")
        basenames.append(os.path.basename(p))
    if basenames != sorted(basenames):
        warn(f"staged photo basenames are not in sorted order {basenames} — "
             f"display order may not match user intent")


def check_block_presence(fields, blocks):
    for prefix, block in (("EBAY", "EBAY_DESCRIPTION"),
                          ("KA", "KA_DESCRIPTION"),
                          ("VINTED", "VINTED_DESCRIPTION")):
        applies = fields.get(f"{prefix}_APPLIES")
        if applies == "yes" and block not in blocks:
            err(f"{prefix}_APPLIES=yes but {block} block is missing")
        if applies == "no" and block in blocks:
            err(f"{prefix}_APPLIES=no but {block} block is present")
    check_condition_mirrored(fields, blocks)


def check_condition_mirrored(fields, blocks):
    """CONDITION_TEXT_DE must actually appear in each German description block.

    Guards against cross-item contamination: in the 2026-08-17 run the Noctua
    action file's KA and Vinted blocks carried the *Echo Show's* condition
    sentence verbatim, contradicting its own CONDITION_TEXT_DE, and nothing
    caught it because the field was only presence-checked.
    """
    # KA is always German; eBay/Vinted carry the German sentence unless the
    # seller runs english-only, and the English sentence unless german-only.
    expectations = [("CONDITION_TEXT_DE", ["KA"] + (["EBAY", "VINTED"] if wants_de() else [])),
                    ("CONDITION_TEXT_EN", ["EBAY", "VINTED"] if wants_en() else [])]
    for field, prefixes in expectations:
        cond = (fields.get(field) or "").strip()
        if not cond or cond == "NONE":
            continue
        for prefix in prefixes:
            block = f"{prefix}_DESCRIPTION"
            body = blocks.get(block)
            if fields.get(f"{prefix}_APPLIES") != "yes" or body is None:
                continue
            if cond not in body:
                warn(f"{block} does not contain {field} verbatim "
                     f"('{cond[:60]}…') — the condition text must be mirrored "
                     f"across platforms; a differing sentence here usually means "
                     f"text from another item leaked in")


def check_ebay_block(fields, blocks):
    body = blocks.get("EBAY_DESCRIPTION")
    if body is None:
        return
    if not body.lstrip().startswith("<p><strong>"):
        err("eBay description must start with <p><strong>[title]</strong></p>")
    if bilingual() and "<hr>" not in body and "<hr/>" not in body and "<hr />" not in body:
        err("eBay description missing <hr> between German and English blocks")
    flat = normalize(body)
    mode = disclaimers_mode()
    if mode == "off":
        return
    if mode == "unknown" and normalize(DISCLAIMER_DE_P1) not in flat \
            and normalize(DISCLAIMER_EN_P1) not in flat:
        warn("eBay description has no disclaimer — no seller config found to "
             "confirm that's intended")
        return
    pairs = []
    if wants_de():
        pairs += [("German disclaimer ¶1", DISCLAIMER_DE_P1),
                  ("German disclaimer ¶2", DISCLAIMER_DE_P2_EBAY)]
    if wants_en():
        pairs += [("English disclaimer ¶1", DISCLAIMER_EN_P1),
                  ("English disclaimer ¶2", DISCLAIMER_EN_P2)]
    if body.count("<small>") < 2:
        err("eBay description must wrap the disclaimers in <small> tags")
    for name, text in pairs:
        if normalize(text) not in flat:
            err(f"eBay description: {name} not verbatim")


def check_ka_block(fields, blocks):
    body = blocks.get("KA_DESCRIPTION")
    if body is None:
        return
    expected_ka_title = fields.get("KA_TITLE", "NONE")
    if expected_ka_title == "NONE":
        expected_ka_title = fields.get("ITEM_TITLE", "")
    first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    if first_line != expected_ka_title:
        err(f"KA description first line '{first_line}' != expected KA title "
            f"'{expected_ka_title}'")
    if re.search(r"<[a-zA-Z]+[^>]*>", body):
        err("KA description contains HTML tags (must be plain text)")
    flat = normalize(body)
    mode = disclaimers_mode()
    if mode == "on" or (mode == "unknown" and normalize(DISCLAIMER_DE_P1) in flat):
        if normalize(DISCLAIMER_DE_P1) not in flat:
            err("KA description: disclaimer ¶1 not verbatim")
        if normalize(DISCLAIMER_DE_P2_KA) not in flat:
            err("KA description: KA-specific Zwischenverkauf sentence not verbatim")
        if normalize(DISCLAIMER_DE_P2_EBAY) in flat and normalize(DISCLAIMER_DE_P2_KA) not in flat:
            err("KA description uses the eBay disclaimer variant instead of the KA one")
    elif mode == "unknown":
        warn("KA description has no disclaimer — no seller config found to "
             "confirm that's intended")
    for english in ("Subject to prior sale", "This item is sold", "For sale:"):
        if english in body:
            err(f"KA description contains English text: '{english}'")
    pickup = (CFG or {}).get("pickup_area")
    if pickup and pickup not in body:
        warn(f"KA description pickup line should name the configured "
             f"pickup_area '{pickup}'")
    if "@" in body:
        warn("KA description contains '@' — Kleinanzeigen rejects '@' on publish; "
             "replace with 'bei' or '/' (e.g. '4K@60Hz' → '4K bei 60Hz')")


DISCLAIMER_DE_SHORT = "Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft."
DISCLAIMER_EN_SHORT = "This item is sold without any warranty."


def check_vinted_block(fields, blocks):
    body = blocks.get("VINTED_DESCRIPTION")
    if body is None:
        return
    if len(body) > 2000:
        err(f"Vinted description is {len(body)} chars (hard limit 2000)")
    if re.search(r"<[a-zA-Z]+[^>]*>", body):
        err("Vinted description contains HTML tags (must be plain text)")
    if bilingual() and not re.search(r"^---$", body, re.M):
        err("Vinted description missing '---' separator between DE and EN blocks")
    expected_title = fields.get("VINTED_TITLE", "NONE")
    if expected_title == "NONE":
        expected_title = fields.get("ITEM_TITLE", "")
    first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    if first_line != expected_title:
        err(f"Vinted description first line '{first_line}' != expected title "
            f"'{expected_title}'")
    flat = normalize(body)
    mode = disclaimers_mode()
    if mode == "off":
        return
    has_full_de = normalize(DISCLAIMER_DE_P1) in flat
    has_full_en = normalize(DISCLAIMER_EN_P1) in flat
    has_short_de = normalize(DISCLAIMER_DE_SHORT) in flat
    has_short_en = normalize(DISCLAIMER_EN_SHORT) in flat
    if mode == "unknown" and not (has_full_de or has_short_de or has_full_en or has_short_en):
        warn("Vinted description has no disclaimer — no seller config found to "
             "confirm that's intended")
        return
    if wants_de():
        if has_full_de:
            if normalize(DISCLAIMER_DE_P2_EBAY) not in flat:
                err("Vinted description: German disclaimer ¶2 not verbatim")
        elif not has_short_de:
            err("Vinted description: German disclaimer not found (neither full nor short variant)")
    if wants_en():
        if has_full_en:
            if normalize(DISCLAIMER_EN_P2) not in flat:
                err("Vinted description: English disclaimer ¶2 not verbatim")
        elif not has_short_en:
            err("Vinted description: English disclaimer not found (neither full nor short variant)")
    if bilingual():
        if has_full_de and not has_full_en:
            err("Vinted description: mixed disclaimer variants (DE full, EN short/missing)")
        if not has_full_de and has_full_en:
            err("Vinted description: mixed disclaimer variants (DE short, EN full)")


def check_js_safety(blocks):
    # Listers inject description text into browser-side JS; backticks and ${
    # break (or execute inside) the injected script.
    for name, body in blocks.items():
        if "`" in body:
            err(f"{name} contains a backtick (`) — breaks the listers' JS injection")
        if "${" in body:
            err(f"{name} contains '${{' — breaks the listers' JS injection")


PLATFORM_FIELDS = {"ebay": "EBAY_APPLIES", "kleinanzeigen": "KA_APPLIES",
                   "vinted": "VINTED_APPLIES"}


def check_platforms(fields):
    """A platform the seller did not configure must never be listed."""
    if CFG is None or not CFG.get("platforms"):
        return
    configured = {p.strip() for p in str(CFG["platforms"]).split(",")}
    unknown = configured - set(PLATFORM_FIELDS)
    if unknown:
        warn(f"seller config platforms {sorted(unknown)} are not known "
             f"({sorted(PLATFORM_FIELDS)})")
    for platform, field in PLATFORM_FIELDS.items():
        if platform not in configured and fields.get(field) == "yes":
            err(f"{field}=yes but '{platform}' is not in the seller config's "
                f"platforms ({CFG['platforms']}) — run /listing-setup to add it")


def check_location(fields):
    if CFG is None:
        return
    allowed = {CFG.get("location"), CFG.get("location_zip")} - {None}
    if allowed and fields.get("LOCATION") not in allowed:
        warn(f"LOCATION '{fields.get('LOCATION')}' is not the configured "
             f"{sorted(allowed)}")


def main():
    global CFG
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    try:
        raw, fields, blocks = parse(path)
    except OSError as e:
        print(f"cannot read {path}: {e}")
        sys.exit(2)
    try:
        CFG = load_config(path, sys.argv[2] if len(sys.argv) == 3 else None)
    except OSError as e:
        print(f"cannot read seller config: {e}")
        sys.exit(2)
    if CFG is None:
        warn(f"no seller config ({CONFIG_BASENAME}) found — seller-specific "
             f"checks degraded to warnings; run /listing-setup")
    else:
        print(f"seller config: {CFG['_path']}")
    if "LISTING ACTION FILE v1" not in raw:
        warn("file lacks 'LISTING ACTION FILE v1' marker")

    check_fields(fields)
    check_plugin_version(fields)
    check_titles(fields)
    check_ebay_condition(fields)
    check_prices(fields)
    check_shipping(fields)
    check_vinted_fields(fields)
    check_photos(fields)
    check_block_presence(fields, blocks)
    check_ebay_block(fields, blocks)
    check_ka_block(fields, blocks)
    check_vinted_block(fields, blocks)
    check_js_safety(blocks)
    check_location(fields)
    check_platforms(fields)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{path}: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
