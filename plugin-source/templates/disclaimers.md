<!-- Canonical legal disclaimers for the listing-drafter. -->
<!-- PASTE these blocks verbatim into the action file's description sections —
     do NOT retype them from memory (transcription drift causes validator
     failures and is wasted output). The validator enforces these exact texts. -->
<!-- This file is the single source of truth; the listing-drafter SKILL.md
     reproduces the same text inline for readability, and the validator hard-codes
     it for enforcement. If any disclaimer ever changes, update all three. -->

## eBay — German (inside the eBay German block, each paragraph wrapped in <small>)

```
<p><small>Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche aus grob fahrlässiger bzw. vorsätzlicher Verletzung von Pflichten des Verkäufers sowie für jede Verletzung von Leben, Körper und Gesundheit.</small></p>
<p><small>Zwischenverkauf vorbehalten.</small></p>
```

## eBay — English (inside the eBay English block, each paragraph wrapped in <small>)

```
<p><small>This item is sold without any warranty. This exclusion does not apply to claims for damages arising from grossly negligent or intentional breach of duty by the seller, nor to any injury to life, body, or health.</small></p>
<p><small>Subject to prior sale.</small></p>
```

## Kleinanzeigen — German only (plain text, longer "Zwischenverkauf" sentence)

```
Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche aus grob fahrlässiger bzw. vorsätzlicher Verletzung von Pflichten des Verkäufers sowie für jede Verletzung von Leben, Körper und Gesundheit.

Zwischenverkauf bleibt stets vorbehalten. Vertragsannahme erfolgt bei Versand durch Absendung, bei Abholung durch Übergabe.
```

## Vinted — plain text (NO HTML). Reuses the eBay disclaimers, tags stripped.

### Vinted German block:

```
Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft. Der Ausschluss gilt nicht für Schadenersatzansprüche aus grob fahrlässiger bzw. vorsätzlicher Verletzung von Pflichten des Verkäufers sowie für jede Verletzung von Leben, Körper und Gesundheit.

Zwischenverkauf vorbehalten.
```

### Vinted English block:

```
This item is sold without any warranty. This exclusion does not apply to claims for damages arising from grossly negligent or intentional breach of duty by the seller, nor to any injury to life, body, or health.

Subject to prior sale.
```

## Vinted SHORT variant (only when the full bilingual description would exceed 2000 chars)

Use these shortened disclaimers (first + last sentence of the full text) in
**both** language blocks when the complete Vinted description exceeds 2000
characters. Never mix variants — both blocks use the same one.

### Vinted short — German:

```
Die Ware wird unter Ausschluss jeglicher Gewährleistung verkauft.

Zwischenverkauf vorbehalten.
```

### Vinted short — English:

```
This item is sold without any warranty.

Subject to prior sale.
```
