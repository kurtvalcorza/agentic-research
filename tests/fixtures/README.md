# Test fixtures

JSON records exercising the checks. Naming convention:

- `<record>.valid.json` — a well-formed record that must pass
- `<record>.<defect>.json` — a record containing exactly **one** defect

One defect per fixture. A fixture with two defects cannot prove which one the check
caught, so a passing test against it proves less than it appears to.
