# Risk Register

| Risk | Impact | Mitigation |
|---|---:|---|
| Generated documents appear construction-ready | High | Prominent disclaimers, title-block labels, forbidden-language tests |
| User assumes legal or permitting validity | High | Package README, PDF title-page warnings, required professional-review sections |
| Cost estimates are treated as live market quotes | High | YAML-only cost rates, source notes, no live scraping |
| Structural placeholders look engineered | High | Label as placeholders and require structural engineer review |
| MEP placeholders look engineered | High | Label as placeholders and require electrical/mechanical review |
| SVG drawings imply precision | Medium | Use schematic labels and approximate dimension notes |
| PDF dependency causes install issues | Medium | Decide between WeasyPrint and ReportLab before implementation |
| Excel formulas become fragile | Medium | Prefer transparent formulas and tested workbook structure |
| Assumptions drift from generated outputs | High | Centralize assumptions in YAML and test propagation |
| Package omits source YAML | Medium | Manifest and ZIP tests requiring YAML inclusion |
| Unsafe wording slips into templates | Medium | Repository-wide forbidden-phrase tests |

