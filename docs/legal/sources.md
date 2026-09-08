# Official Legal Sources Register

Maintained legal corpus for LabelGuard rules. B alone edits this file / rule data. Before production or real enforcement, legal team must validate every configured rule against the latest Gazette/Department notification (PRD §47, §48).

## Primary sources (official)
- Department of Consumer Affairs — Legal Metrology page (2011 Rules + amendments): https://consumeraffairs.gov.in/pages/legal-metrology-act
- Department 'What's New' — Packaged Commodities Rules book + FAQs: https://consumeraffairs.nic.in/whats-new-0

## Consolidated reference (unofficial, for text parsing)
- Rajasthan govt consolidated PCR-2011 PDF: https://swcs.rajasthan.gov.in/Upload/ce69e6c9-9deb-46d9-a981-858d9df602c1Legal%20Metrology%20(Packaged%20commodity)%20Rules%202011.pdf

## Amendment timeline to track (PRD §48)
- 24.10.2025 amendment
- 02.12.2025 amendment
- 13.02.2026 amendment
- Second Amendment 2026
- Third Amendment 2026 (29.05.2026) — note e-commerce country-of-origin filter effective date uses the latest applicable amendment.

## Rules engine obligation
Never hard-code a stale 2011 checklist. Rules are versioned with `effective_from`/`effective_to`; inspections retain the ruleset version in force on their inspection date (R-VERSION-01/02).