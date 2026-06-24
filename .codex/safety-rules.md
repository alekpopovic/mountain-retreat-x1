# Codex Safety Rules

## Absolute Boundaries

Do not generate or imply:

- legal permits
- permit approvals
- signed engineering calculations
- sealed professional drawings
- legally binding construction approvals
- construction-ready documents
- code-compliance certifications

Do not scrape live prices.

Do not hide assumptions in code. All project assumptions must be stored in YAML and surfaced in generated outputs.

## Required Output Label

Every generated artifact should include clear language equivalent to:

```text
Preliminary planning document only. Not for construction, permitting, procurement, or legal reliance. Requires review by appropriately licensed professionals and local authorities before use.
```

## Required Professional Review Notes

Generated materials must call for review by:

- licensed architect
- licensed structural engineer
- licensed electrical engineer
- licensed mechanical engineer
- local permitting authority
- qualified cost estimator or contractor when cost estimates are used for budgeting

## Forbidden Phrase Examples

Generated outputs should be tested against phrases such as:

- approved for construction
- permit-ready
- building permit issued
- sealed engineering calculation
- licensed approval
- code-compliant certification
- authorized construction documents

