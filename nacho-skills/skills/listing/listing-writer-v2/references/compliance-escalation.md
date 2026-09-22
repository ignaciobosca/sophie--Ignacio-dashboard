# Compliance Escalation (Phase E)

Read at Phase E for regulated categories (toys, electronics with batteries, supplements, baby) or any product with a Seller Central Safety & Compliance tab. The skill FLAGS and ROUTES; the seller ATTESTS with supplier docs. Never assert a regulatory value the seller has not confirmed. These fields carry real legal liability if asserted wrong, treat them differently from marketing "claims to verify."

## The escalation checklist

| Field | Default trap | What to do |
|---|---|---|
| Country/Region of Origin | required | From supplier. Usually known. |
| Dangerous Goods Regulations | sellers default to "Not Applicable" | If the product has a lithium battery (most USB-C rechargeable toys/electronics), Not Applicable is likely WRONG. It usually needs the lithium-battery classification + a UN38.3 test report. Make the seller confirm battery chemistry (li-ion/li-po vs other) before accepting Not Applicable. A small mAh rating does not exempt it. |
| California Prop 65 Warning Type + Mandatory Cautionary Statement | "No Warning Applicable" | Many plastic/electronic/battery products DO carry a Prop 65 warning. Do not assert No Warning Applicable unless the supplier confirms in writing. If a warning applies, pick the matching warning type and statement. |
| Is This Product Subject To Buyer Age Restrictions | n/a | No for a normal kids toy (this is for alcohol/weapons/etc). |
| Has Replaceable Battery | mismatch risk | Match the spec sheet. Built-in rechargeable = No. Keep consistent with the structured-attributes tab. |
| Contains PFAS | guessing | Confirm with supplier. Usually No for plastic/LCD, but do not guess. |
| Ships Globally | mismatch risk | No for a US-only English listing. Keep consistent with the Offer tab marketplace toggles. |
| Is OEM Sourced Product | seller's call | Likely Yes for white-label/OEM. |
| Safety Attestation / CPC | bluffing | US children's products need a Children's Product Certificate (CPC) backed by CPSIA / ASTM F963 testing. Only attest Yes if the docs EXIST. Missing CPC is a launch blocker, not a field to fill optimistically. |
| Safety Warning (text) | n/a | Add "Adult supervision recommended. Not for children under 3 due to small parts" ONLY if the actual CPSC/ASTM determination says so. |

## Age vs small-parts conflict (Rule 9, applied here)

Small cards, a stylus, and insert slots commonly trigger a **3+ (36 months) minimum** under small-parts/choking rules. If the marketing claims "ages 1-3", "ages 1+", or a head keyword like "flash cards for toddlers 1-3", that can DIRECTLY CONTRADICT the safety rating. Reconcile before publishing:
- Either the testing supports the younger age (keep the claim), or
- The age floor rises to 3+ and the title/keywords/attributes must move with it.
Flag this loudly; it is both a suppression risk and a genuine safety issue.

## Fields to skip for US-only listings
- Regulatory Compliance Certification + Responsible Person's Email (EU GPSR)
- Compliance Media / Safety Data Sheet (chemical products)
- Non-Lithium Battery Energy Content (only if the battery is non-lithium; lithium goes under Dangerous Goods)
- Has Less Than 30 Percent State of Charge (only if DG applies)
- GHS Chemical H Code, BAA/TAA Regulation Compliance

## Output of Phase E
A short prioritized list of the 2-4 fields that carry actual liability and must be confirmed with supplier docs before Save and finish. For a USB-C rechargeable kids toy the usual three are: (1) battery chemistry -> Dangerous Goods, (2) Prop 65, (3) CPC/ASTM testing + the age-vs-small-parts reconciliation.
