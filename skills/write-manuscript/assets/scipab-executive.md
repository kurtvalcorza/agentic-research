---
marp: true
theme: executive
paginate: true
header: ''
footer: '**[Organization Name]** | [Date]'
style: |
  section {
    background-color: #ffffff;
    color: #2c3e50;
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 28px;
  }
  h1 {
    color: #1a5490;
    font-size: 2.8em;
    font-weight: 700;
    margin-bottom: 0.5em;
    line-height: 1.2;
  }
  h2 {
    color: #2c3e50;
    font-size: 2em;
    font-weight: 600;
    margin-bottom: 0.4em;
  }
  h3 {
    color: #34495e;
    font-size: 1.5em;
    font-weight: 500;
  }
  strong {
    color: #1a5490;
    font-weight: 700;
  }
  ul {
    list-style: none;
    padding-left: 0;
  }
  ul li {
    padding-left: 1.5em;
    margin-bottom: 0.6em;
    line-height: 1.4;
  }
  ul li:before {
    content: "▸";
    color: #1a5490;
    font-weight: bold;
    display: inline-block;
    width: 1.2em;
    margin-left: -1.2em;
  }
  .bignum {
    font-size: 3em;
    font-weight: 700;
    color: #1a5490;
    line-height: 1;
  }
  .metric {
    font-size: 2.2em;
    font-weight: 700;
    color: #27ae60;
  }
  .warning {
    font-size: 2.2em;
    font-weight: 700;
    color: #e74c3c;
  }
  section.complication {
    background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
    color: #ffffff;
  }
  section.complication h1, section.complication h2 {
    color: #ffffff;
  }
  section.complication ul li:before {
    color: #ffffff;
  }
  section.implication {
    background: #2c3e50;
    color: #ecf0f1;
    font-size: 1.5em;
    padding: 3em;
  }
  section.implication h1 {
    color: #e74c3c;
    font-size: 2.5em;
    text-align: center;
  }
  section.implication .warning {
    color: #e74c3c;
  }
  section.benefit {
    background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
    color: #ffffff;
  }
  section.benefit h1, section.benefit h2 {
    color: #ffffff;
    border-bottom-color: #ffffff;
  }
  section.benefit ul li:before {
    color: #ffffff;
  }
  section.cta {
    background: #1a5490;
    color: #ffffff;
    padding: 3em;
  }
  section.cta h1 {
    color: #ffffff;
    font-size: 3em;
    text-align: center;
  }
  section.cta ul li:before {
    color: #3498db;
  }
  table {
    font-size: 0.85em;
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
  }
  th {
    background: #1a5490;
    color: white;
    padding: 0.8em;
    text-align: left;
    font-weight: 600;
  }
  td {
    padding: 0.8em;
    border-bottom: 1px solid #ddd;
  }
  tr:hover {
    background: #f5f5f5;
  }
  .highlight-box {
    background: #ecf0f1;
    border-left: 6px solid #1a5490;
    padding: 1em 1.5em;
    margin: 1em 0;
  }
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->
<!-- _footer: "" -->

![bg right:40% 80%](https://via.placeholder.com/800x600/1a5490/ffffff?text=LOGO)

# [Project Name]
## [Compelling Subtitle]

**[Your Name], [Title]**
*[Organization/Department]*

[Presentation Date]

---

<!-- _class: situation -->

# Situation

## [One-sentence summary of current state]

**Current landscape:**

<div class="bignum">8</div>

**partner universities**

each maintaining **separate** research data silos

<div class="metric">$1.2M/year</div>

total storage and duplication cost

---

<!-- _class: situation -->

## Situation: How We Got Here

**Timeline:**

| Year | Development |
|------|-------------|
| 2020 | Each university builds its own data store |
| 2022 | Duplication accelerates (shared projects grow) |
| 2024 | Storage and re-collection cost reaches $1.2M/year |
| 2025 | **Status quo** (no shared infrastructure) |

**Why this happened:**
No shared open-science data strategy

---

<!-- _class: complication -->

# Complication

## [The Problem in 6 Words or Less]

**Four critical issues:**

Duplicated datasets across institutions
Wasted effort and storage cost
No shared data infrastructure
Reproducibility gaps widening

---

<!-- _class: complication -->

## Complication: The Cost

<div style="display: flex; justify-content: space-around; align-items: center;">

<div>
<div class="bignum">$1.2M</div>
<strong>Annual cost</strong><br/>
(storage + re-collection)
</div>

<div>
<div class="bignum">8</div>
<strong>Separate silos</strong><br/>
(no interoperability)
</div>

<div>
<div class="bignum">0</div>
<strong>Shared datasets</strong><br/>
(no reuse)
</div>

</div>

**Bottom line:** We're re-collecting and re-storing the same data, not sharing it.

---

<!-- _class: implication -->

# Implication

## If we don't act within 5 years:

<div class="warning">$6M</div>

**cumulative cost of duplicated data work**

<div class="warning">Zero</div>

**shared datasets available for reuse**

<div class="warning">Persistent</div>

**reproducibility gaps**

---

<!-- _class: implication -->

## Implication: The Trajectory

**Scenario planning (2025-2030):**

**Status Quo Path:**
- Duplication cost escalates to $6M cumulative
- Researchers keep re-collecting the same datasets
- No shared governance or standards emerge
- Reproducibility gaps become structural

**Result:** the consortium locked out of collaborative, reproducible research

---

<!-- _class: position -->

# Position

## [Your Solution in 8 Words Max]

**A federated open-data platform shared across the consortium**

---

<!-- _class: position -->

## Position: Three Core Claims

<div class="highlight-box">

### 1. Cost Reduction
<div class="metric">67% savings</div>
$0.4M vs. 1.2M annually

</div>

<div class="highlight-box">

### 2. Reuse & Collaboration
<div class="metric">8 universities</div>
sharing one federated catalog

</div>

<div class="highlight-box">

### 3. Reproducibility
<div class="metric">100%</div>
datasets versioned and citable

</div>

---

<!-- _class: position -->

## Position: How It Works

**Architecture (simplified):**

```
┌─────────────────────────────────────┐
│  University Research Applications   │
└──────────────┬──────────────────────┘
               │
     ┌─────────▼─────────┐
     │  Federated Data   │  ← One shared catalog
     │  Catalog          │
     └─────────┬─────────┘
               │
     ┌─────────▼─────────┐
     │  Member Repos     │  ← Datasets stay at each
     │  (each university)│     institution, indexed centrally
     └───────────────────┘
```

**Key difference:** Federated, standards-based, reusable

---

<!-- _class: position -->

## Position: Proof Points

**Evidence this works:**

| Proof Point | Source |
|-------------|--------|
| 67% cost reduction | Technical specs (Phase 1 pilot) |
| 8 universities onboarded | Onboarding program (Q4 2025) |
| Production-ready | 3 shared datasets federated successfully |
| Sector precedent | Established open-data federation model (adapted) |

**Risk mitigation:** Pilot-first approach (reversible, low-cost)

---

<!-- _class: cta -->

# Action

## Launch 6-Month Pilot With 3 Member Universities

**Starting Q2 2026 (April-Sept)**

---

<!-- _class: action -->

## Action: Pilot Scope

**What we're asking for:**

<div class="highlight-box">

**Budget:** $0.5M
- Infrastructure: $0.3M
- Onboarding: $0.15M
- Operations: $0.05M

</div>

**Timeline:** 6 months (Q2 2026)

**Scope:** 3 shared datasets
- Genomics reference set
- Climate sensor archive
- Survey microdata

**Success criteria:** 50% cost reduction, 3 universities onboarded

---

<!-- _class: action -->

## Action: What Happens Next

**Decision path:**

| Date | Milestone | Owner |
|------|-----------|-------|
| **March 2026** | Consortium steering committee approval | [Committee Chair] |
| **April 2026** | Budget release | Consortium finance office |
| **April-May** | Infrastructure setup | Platform engineering team |
| **June-Sept** | Pilot execution | Open-data platform team |
| **October** | Evaluation report | Project team |

**Decision needed by:** **March 15, 2026**

---

<!-- _class: benefit -->

# Benefit

## By 2028: A Shared Open-Science Repository

---

<!-- _class: benefit -->

## Benefit: The Future State

**Quantified outcomes:**

<div class="metric">$0.8M/year</div>

**savings** (reallocated to research)

<div class="metric">200 datasets</div>

**shared** and citable across the consortium

<div class="metric">8 universities</div>

**using the platform** (standardized)

---

<!-- _class: benefit -->

## Benefit: Strategic Positioning

**The consortium becomes:**

A reference model
for open-science data sharing

A collaborative research hub
(not isolated silos)

A reproducibility leader
(versioned, citable datasets)

**Identity shift:** From duplicating to sharing

---

<!-- _class: next-steps -->

# Next Steps

**Immediate actions:**

1. **March 1:** Present to consortium steering committee
   - Seek approval for $0.5M pilot budget

2. **March 15:** Decision deadline
   - Approve/reject pilot program

3. **April 1:** If approved, kickoff
   - Platform infrastructure setup begins

**Questions?** [Your email/contact]

---

<!-- _class: appendix -->
<!-- _paginate: false -->

# Appendix

*Backup slides for detailed questions*

---

## Appendix: Budget Breakdown

**$0.5M pilot allocation:**

| Category | Amount | Details |
|----------|--------|---------|
| Infrastructure | $0.3M | Cloud hosting, storage, catalog services |
| Onboarding | $0.15M | 3 universities × 6 months (integration, materials) |
| Operations | $0.05M | Project management, monitoring, support |
| **Total** | **$0.5M** | 6-month pilot |

**ROI calculation:** Breakeven in 14 months (vs. duplicated storage and re-collection)

---

## Appendix: Risk Analysis

**Key risks and mitigations:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Technical failure | Low | High | Pilot in controlled environment (3 datasets) |
| Institutional pushback | Medium | Low | No data migration required (federated, pilot only) |
| Adoption resistance | Medium | Medium | Onboarding + change management |
| Budget overrun | Low | Medium | Fixed scope (3 datasets only) |

**Exit strategy:** If pilot fails, no long-term commitment

---

## Appendix: Comparable Initiatives

**Similar initiatives:**

| Sector | Program | Outcome |
|--------|---------|---------|
| Genomics | Federated genomic data network | 50% cost reduction, 500+ datasets shared |
| Climate science | Open climate data archive | 70% reuse rate across member labs |
| Social science | Shared survey data repository | $10M savings in re-collection (2020-2024) |

**Lesson:** Shared open-data infrastructure is research-critical

---

## Appendix: Technical Architecture

**Detailed system design:**

[Insert architecture diagram here]

**Components:**
- Federated Catalog (search, authentication, access control)
- Member Repositories (versioned datasets at each institution)
- Ingest Pipeline (metadata harvesting, validation)
- Monitoring Dashboard (usage, reuse metrics)

**See:** Technical specs document for details

---

<!--
SPEAKER NOTES TEMPLATE (customize for each slide)

Title Slide:
- Opening: "Good morning. Today I'm proposing a 6-month pilot for a shared open-data platform."
- Context: "This is about strategic positioning—not just cost savings."
- Transition: "Let me show you where we are today."

Situation Slide:
- Key stat: "8 universities, separate silos, $1.2M/year."
- Emphasis: "This happened organically—no one designed this."
- Transition: "But organic doesn't mean optimal."

Complication Slide:
- Tone: Concerned but calm (not alarmist)
- Pause after "Zero shared datasets" (let it sink in)
- Transition: "So what happens if we do nothing?"

Implication Slide:
- Tone: Urgent, visceral
- Stat emphasis: "$6M over 5 years"
- Personal angle: "We keep re-collecting the same data instead of building on each other's work"
- Transition: "But there's a better path."

Position Slide:
- Tone: Confident, solution-oriented
- Emphasize: "Federated" (not just "cheaper")
- Transition: "Here's the evidence."

Action Slide:
- Tone: Directive, specific
- Decision point: "March 15 deadline"
- Transition: "And here's what we gain."

Benefit Slide:
- Tone: Inspiring, aspirational
- Identity shift: "From duplicating to sharing"
- Closing: "This is about collaborative, reproducible research."
-->
