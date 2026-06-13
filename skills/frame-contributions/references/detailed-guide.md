## VALIDATED IMPLICATIONS (Post-Provocation)

### Summary Table

| Stakeholder | Core Implication | Evidence Grade | Action Timeframe |
|-------------|------------------|----------------|------------------|
| **Practitioners** | Pilot in supervised settings (0.3-0.5 SD learning gain) | HIGH | Immediate (0-6 months) |
| **Practitioners** | Budget $2-5 budget units per pilot site | MODERATE | Planning (6-12 months) |
| **Practitioners** | Do NOT deploy unsupervised (persistence unknown) | LOW | Defer (>24 months) |
| **Policymakers** | Classify as Supplemental/Supervised, require evaluation evidence | HIGH | Immediate (guidance action) |
| **Policymakers** | Mandate full-year outcome monitoring | LOW | Immediate (risk mitigation) |
| **Policymakers** | Do NOT mandate system-wide rollout yet | LOW | Defer (await better evidence) |
| **Researchers** | Fund full-year RCT (n=2,000) | LOW (gap) | Immediate (35 budget units) |
| **Researchers** | Fund educational equity study | ZERO (gap) | Immediate (10 budget units) |
| **Researchers** | Quantify adoption costs | MODERATE (gap) | Secondary (5 budget units) |

---

## PROVOCATION SESSION 3: Limitation Transparency

**Let's ensure you're not hiding weaknesses...**

### Provocation 4: Limitation Confession
**Q:** "What's the **most embarrassing limitation** of this review?"

**Your Initial Response:** [User input]
> "Limited to English-language papers"

**Provocation Challenge:**
❓ That's a standard limitation (everyone has it). What's the limitation you're **reluctant to admit**?
- What weakness might a harsh reviewer attack?
- What gap could undermine your core contribution?
- What did you hope readers wouldn't notice?

**Refined Response:** [User iteration]
> "Theme B (adoption barriers) is based on MODERATE evidence, mostly self-reported surveys. We don't have hard cost/time data—just educator opinions about barriers. This means our adoption budget estimates ($2-5 budget units) are educated guesses, not validated figures."

✅ **Honest** - Acknowledges evidence weakness in key claim

---

### Provocation 5: Generalizability Test
**Q:** "Where does this review **NOT apply**?"

**Your Initial Response:** [User input]
> "Findings are generalizable to school settings"

**Provocation Challenge:**
❓ That's overclaimed. Name **specific contexts** where your evidence breaks down:
- Low-resource schools (under-funded or rural)?
- Non-core subjects (arts, vocational, physical education)?
- Settings without reliable devices or connectivity?

**Refined Response:** [User iteration]
> "Findings apply ONLY to:
> - Supervised classroom settings (teacher-monitored, with reliable devices)
> - Math/literacy domains (80% of corpus)
> - Well-resourced schools (75% of studies in well-funded districts)
>
> Findings may NOT apply to:
> - Low-resource/under-connected schools (ZERO studies in corpus)
> - Arts, vocational, physical education domains (underrepresented, <10% corpus)
> - Unsupervised/self-directed use without a teacher (ZERO evidence)
>
> **Critical Caveat:** Generalizability to low-resource schools is UNKNOWN (0 such studies in corpus). Pilot data from low-resource settings is required before claims generalize to them."

✅ **Transparent** - Explicitly names non-applicability contexts

---

## VALIDATED LIMITATIONS (Post-Provocation)

1. **Adoption Evidence Weakness (MODERATE GRADE)**
   - Barrier data is self-reported (surveys), not measured costs/times
   - Budget estimates ($2-5 budget units) are projections, not validated figures
   - Impact: Adoption guidance is directionally correct but quantitatively uncertain

2. **Generalizability Constraints**
   - 80% math/literacy (not applicable to arts, vocational, etc.)
   - 75% well-resourced districts (low-resource applicability uncertain)
   - ZERO low-resource-school studies in corpus (equity validity unknown)
   - Impact: Findings require pilot validation in low-resource contexts before scaling

3. **Persistence Evidence Gap (LOW GRADE)**
   - Only 2 papers track outcomes across a full school year
   - High attrition bias (30-40% dropout)
   - Impact: Whether learning gains persist is UNCERTAIN, not established

4. **Educational Equity Blind Spot (ZERO EVIDENCE)**
   - No studies examine differential impacts by socioeconomic status, geography, or device access
   - Impact: Cannot claim equitable benefits; equity risks unknown

---

## FUTURE RESEARCH DIRECTIONS (Grounded in Gaps)

**From LOW/ZERO Evidence Themes:**

### Priority 1: Full-Year Persistence RCT (Addresses Limitation #3)
- **Gap:** Persistence of learning gains (LOW evidence, 2 cohorts only)
- **Study Design:** Multi-site RCT, n=2,000, full-school-year follow-up
- **Budget:** 35 budget units
- **Impact:** Upgrades Theme C from LOW to HIGH evidence
- **Justification:** Make-or-break question for adoption policy

### Priority 2: Educational Equity Study (Addresses Limitation #4)
- **Gap:** Equity impacts (ZERO evidence)
- **Study Design:** Quasi-experimental study in low-resource vs. well-resourced schools
- **Budget:** 10 budget units
- **Impact:** Fills critical equity blind spot
- **Justification:** Prevents widening achievement gaps

### Priority 3: Adoption Cost Quantification (Addresses Limitation #1)
- **Gap:** Quantified adoption costs (MODERATE evidence, self-reported)
- **Study Design:** Prospective cohort tracking actual costs/times in pilot sites
- **Budget:** 5 budget units
- **Impact:** Upgrades Theme B from MODERATE to HIGH evidence
- **Justification:** Enables accurate budgeting for scale-up

---

## OVERCLAIMING SAFEGUARDS (Auto-Checks)

### Check 1: Contribution-Evidence Alignment

For each stated contribution:
```python
IF contribution_claim AND evidence_grade:
  IF claim_strength > evidence_grade:
    FLAG: "POTENTIAL OVERCLAIM"
    SUGGEST: Downgrade claim language to match evidence

Example:
  Claim: "Establishes that learning gains persist all year" (strong language)
  Evidence: LOW GRADE (2 cohorts, high attrition)
  Verdict: OVERCLAIM ❌
  Fix: "Limited evidence suggests gains may persist across a school year, but HIGH-quality longitudinal studies needed"
```

### Check 2: Implication-Feasibility Alignment

For each implication:
```python
IF implication_requires_action AND action_has_resource_cost:
  IF cost_estimate AND cost_evidence_weak:
    FLAG: "UNCERTAIN FEASIBILITY"
    SUGGEST: Acknowledge uncertainty explicitly

Example:
  Implication: "Budget $2-5 budget units for pilot adoption"
  Evidence: MODERATE (self-reported barriers, no hard cost data)
  Verdict: UNCERTAIN FEASIBILITY ⚠️
  Fix: "Estimate $2-5 budget units based on reported barriers, but actual costs may vary—pilot costing study recommended"
```

### Check 3: Limitation-Omission Detection

```python
known_gaps = [theme for theme in synthesis if theme.evidence_grade in ["LOW", "ZERO"]]

IF known_gaps AND known_gaps NOT IN stated_limitations:
  FLAG: "LIMITATION OMISSION"
  SUGGEST: Add missing limitation

Example:
  Known Gap: Theme C (persistence) has LOW evidence
  Stated Limitations: Missing persistence caveat
  Verdict: OMISSION ❌
  Fix: Add "Persistence of learning gains remains uncertain (LOW evidence, only 2 studies across a full school year)"
```

---

## Success Criteria

Framing successful when:

1. ✅ Contributions grounded in synthesis evidence
2. ✅ All contributions pass provocation deletion/enablement/audience tests
3. ✅ Implications tailored to 3 audiences (practitioners/policymakers/researchers)
4. ✅ Implications specify actionable decisions (not vague "support" language)
5. ✅ Limitations transparently acknowledge evidence weaknesses
6. ✅ Future research grounded in identified LOW/ZERO evidence gaps
7. ✅ Zero overclaiming detected (all checks pass)

---

## Integration Points

### LRA Phase 6

```markdown
After Phase 5 (Citation Validation) completes:
  Invoke: frame-contributions

  Parameters:
    project_path: 01_Projects/AI-Tutoring-Review/research/
    provocation_mode: full
    audience_focus: balanced
    overclaim_sensitivity: high

  Process:
    1. Run 3 provocation sessions (Contribution, Implication, Limitation)
    2. Validate contributions against evidence grades
    3. Generate stakeholder-tailored implications
    4. Check for overclaiming (3 auto-checks)
    5. Output: phase6-contribution-framing_project.md

  IF overclaims detected:
    Pause, show user, request revision
  ELSE:
    Proceed to Phase 7 (Consistency Validation)
```

---

## Related Skills

- **[[../../tools-for-thought/SKILL|Tools for Thought]]** - Provocation methodology
- **[[../validate-evidence/SKILL|Validate Evidence]]** - Evidence grading for calibration
- **[[../validate-consistency/SKILL|Validate Consistency]]** - Uses contribution framing in Dimension 4

---

## Version History

**v2.0 (2026-01-17)** - Enhanced features
- Integrated Tools for Thought provocation mode
- Added 5 provocation questions (deletion, enablement, audience, limitation, generalizability)
- Added overclaiming auto-checks (3 safeguards)
- Added stakeholder-tailored implication templates
- Added evidence-graded future research prioritization

**v1.0** - Initial implementation
- Basic contribution framing
- Generic contribution statements

---

## Key Principles

1. **Provoke, Don't Suggest** - Challenge vague contributions to force clarity
2. **Evidence-Calibrated** - Contribution strength matches evidence grade
3. **Stakeholder-Specific** - Implications tailored to practitioner/policymaker/researcher needs
4. **Limitation Transparency** - Acknowledge weaknesses explicitly (builds trust)
5. **Priority-Driven** - Future research ranked by impact, not listed generically

**Strategic Clarity Through Provocation** 🎯
