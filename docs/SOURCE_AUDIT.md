# AquaMind AI — Source Audit and Corrections

## Audit date

25 October 2026

## Why this audit exists

AquaMind treats source provenance as part of the safety case. Source metadata is therefore corrected when an official document contradicts an earlier draft entry. This file records those corrections instead of silently rewriting history.

## Material corrections made

1. **DuPont FilmTec Technical Manual** — the earlier draft registry labeled the document as “Version 20, August 2026.” The official DuPont PDF verified during this audit identifies the current document used by AquaMind as **Rev. 19, February 2026**. Canonical ID: `DUPONT_RO_MANUAL_R19_2026`.
2. **DuPont FT-Norm PRO manual** — the earlier draft registry labeled the manual as “Version 1, September 2026.” The official PDF identifies **Rev. 0, January 2022**. Current online tool availability is tracked separately as `DUPONT_FTNORM_TOOL_CURRENT`.
3. **DuPont Cleaning Procedures** — updated from the older Rev. 12 entry to the verified **Rev. 13, February 2026**.
4. **DuPont Chlorination/Dechlorination** — metadata normalized to the verified **Rev. 11, February 2026**.
5. **DuPont Operation Excellence / Limiting Conditions** — metadata normalized to **Rev. 1, June 2025**.
6. **Hydranautics TSB107** — corrected to the verified **TSB107.28, April 2025** rather than the earlier unverified 2026 revision claim.
7. **AWWA M46** — normalized to the official catalog wording **Nanofiltration and Reverse Osmosis, Third Edition**.
8. **NIST SP 800-82 Rev. 4** — retained only as an **Initial Public Draft** dated 21 September 2026; Rev. 3 remains the final OT-security reference.

## Added high-value official sources

- Hydranautics `TAB110` — chlorination in seawater RO supply/pretreatment.
- Hydranautics `TAB111` — chemical pretreatment for RO/NF.
- Hydranautics `TAB116` — polyamide membrane feedwater requirements and mechanical/chemical damage context.
- Current DuPont FT-Norm PRO online tool page, separated from the older technical manual so “current availability” is not confused with “manual revision.”

## Governance rule

A source-version correction is not treated as a model failure. It is treated as provenance maintenance. AquaMind must prefer a verified official source over an earlier project note, and the correction must be visible in Git history.

## Case-library deduplication

- `RO-INT-010` was merged into `RO-INT-001` because both represented the same generic high-flow/high-salt-passage integrity pattern.
- `RO-PRE-012` was merged into `RO-INT-007` because both represented the same startup/trapped-air/water-hammer guard.
- Two non-duplicate cleaning-safety cases were added: `RO-CLEAN-001` and `RO-CLEAN-002`.

The canonical library therefore remains at 90 cases without preserving duplicate semantics.
