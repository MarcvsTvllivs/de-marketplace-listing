---
description: List an item for sale on eBay.de, Kleinanzeigen.de, and Vinted.de.
---

# /list-item — List an item on eBay.de, Kleinanzeigen.de and Vinted.de

Use the **listing-drafter** skill to begin. It handles:
- Gathering item information (Step A)
- Writing the complete listing descriptions (Step B)
- User approval (Step C)
- Saving the action file and handing off

**"Just list something" (default source).** If the user gives a vague request with
no specific item or photos ("just list something", "verkauf das"), the drafter does
**not** ask what to list or where the photos are — it scans the listing folder for
the temporary photo subfolders the user drops there, identifies the item from those
photos, and works from them. See the drafter's Step A0b.

After the user approves the draft, the **kleinanzeigen-lister**, **ebay-lister**,
and **vinted-lister** skills run automatically — no further commands needed.

The order is always:
1. listing-drafter → draft approved → per-item run folder created
   (`Listings/[date]-[item]/`) with the action file (`listing.md`) and staged
   photos inside it
2. kleinanzeigen-lister → KA draft saved
3. ebay-lister → eBay draft saved (only if shipping offered)
4. vinted-lister → Vinted draft saved ("Entwurf speichern")
5. The last applicable lister writes `feedback.md` into the run folder
   (`Listings/[date]-[item]/`) — candid developer notes on the run
6. The drafts are presented for the user to review and publish themselves — the
   plugin never publishes and never offers to (photos are already uploaded when
   file paths were available)

Everything for a run — `listing.md`, the processed photos, and `feedback.md` —
lives in that single per-item folder under `Listings/`.
