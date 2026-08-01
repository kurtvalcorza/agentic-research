# Test fixtures

JSON records exercising the checks. Naming convention:

- `<record>.valid.json` — a well-formed record that must pass
- `<record>.<defect>.json` — a record containing exactly **one** defect

One defect per fixture. A fixture with two defects cannot prove which one the check
caught, so a passing test against it proves less than it appears to.

`counts.two-ends-only.json` is the exception worth naming: its "defect" is that
nothing is wrong with it. It names both ends of the flow and nothing between, so
every rule passes, no arithmetic is checked, and the flow check has nothing to
report — which is exactly the state `U_prisma` must not read as zero outstanding
work.
