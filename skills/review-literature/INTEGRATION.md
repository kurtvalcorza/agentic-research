---
tags: [integration, philosophy, hybrid-workflow, research]
created: 2026-01-11
---

# Integration Philosophy: Hybrid Literature Review Workflow

## The Challenge

How do you reconcile two conflicting paradigms?

**Automation-First (legacy "Research-Writer" approach)**
- 7 specialist agents automate everything from screening to drafting
- Goal: Speed and thoroughness
- Philosophy: AI as task completer
- Output: Citation-validated drafts ready for submission

**Enhance Writing (Cognition-First)**
- AI as provocateur, not writer
- Goal: Deep understanding and original thinking
- Philosophy: AI as cognitive enhancement tool
- Anti-pattern: "Don't let AI write your literature review (you won't understand it)"

## The Solution: Hybrid Handoff

**Automate the mechanical. Preserve the intellectual.**

This skill splits the literature review workflow at the natural boundary between discovery and synthesis:

```
AUTOMATE (Phases 1-3)          |  HANDOFF  |  HUMAN-LED (Phases 4-7)
                               |           |
Corpus Screening       ─────── | ───────── | ──────  Writing
Extraction & Themes    ─────── |     │     | ──────  Synthesis
Argument Structuring   ─────── |     ↓     | ──────  Validation
                               |           |
                         You take ownership
                         of intellectual work
```

### What Gets Automated (Phases 1-3)

**Phase 1: Screening 50 papers against criteria**
- Tedious: Reading 50 abstracts to find 20 relevant ones
- Mechanical: Applying defined inclusion/exclusion rules
- Automatable: Clear decision criteria
- **Why automate:** Saves hours of manual filtering

**Phase 2: Extracting themes across 20 papers**
- Tedious: Tagging claims, evidence, methodologies across papers
- Mechanical: Pattern recognition (consensus, contradictions, gaps)
- Automatable: Structured extraction with AI
- **Why automate:** Provides organized starting point for YOUR synthesis

**Phase 3: Building argument structure**
- Tedious: Mapping "Known → Unknown → Contribution" framework
- Mechanical: Logical scaffolding from extracted themes
- Automatable: Creates outline for YOU to challenge and refine
- **Why automate:** Gives you something to push against, not start from scratch

### What Stays Human-Led (Phases 4-7)

**Phase 4: Writing the literature review**
- Intellectual: Requires understanding nuance, defending claims
- Creative: YOUR voice, YOUR framing, YOUR argument
- Non-automatable: AI can provoke thinking, not replace it
- **Why human-led:** "You should finish having *thought more deeply*, not less"

**Phase 5: Validating citations**
- Mechanical validation layer (can automate)
- But YOU decide how to fix issues flagged

**Phase 6: Framing your contribution**
- AI offers framing options (supportive, challenging, extending)
- YOU choose positioning based on your goals

**Phase 7: Consistency check**
- Automated QA check
- YOU make final decisions on flagged issues

## The Handoff Point: Phase 3 → Phase 4

### What Phase 3 Delivers

```markdown
# Argument Outline (AI-Generated)

## Known (Consensus in the field)
- Theme 1: AI tutoring improves test scores
  - Paper A: Smith (2023) - RCT shows 12% improvement
  - Paper B: Jones (2022) - Meta-analysis confirms effect
  - Paper C: Lee (2024) - Replication study

- Theme 2: Effects vary by implementation quality
  - Wang et al. (2023) - Quality matters more than technology
  - Chen (2024) - Teacher training mediates effectiveness

## Unknown (Gap identified)
- Little research on long-term retention (most studies < 6 months)
- Unclear which AI features drive learning vs. engagement
- Limited evidence on equity impacts across SES groups

## Contribution (Your work)
This review synthesizes evidence to identify success factors
and highlight research gaps for Project Atlas project design.
```

### What You Receive (Handoff Document)

```markdown
# Phase 4 Handoff: From Structure to Synthesis

You now have:
1. ✅ Approved corpus (23 papers vetted in Phase 1)
2. ✅ Synthesis notes (themes, claims, contradictions extracted)
3. ✅ Argument outline (logical structure: Known → Gap → Contribution)

## Before You Write: Critical Provocations

Answer these BEFORE drafting:

1. **Understanding Check**
   "Can I explain why each of the 23 papers matters for MY argument?"
   - If no: Read papers yourself, don't rely on AI summaries

2. **Gap Validation**
   "Is the AI-identified gap actually a gap, or am I missing context?"
   - Challenge AI's analysis
   - Verify the gap with your domain expertise

3. **Contribution Test**
   "Does my proposed contribution logically follow from the evidence?"
   - Test the Known → Gap → Contribution chain
   - Don't accept AI's framing uncritically

## Anti-Patterns to Avoid

❌ **Don't copy-paste AI synthesis into your literature review**
   - You won't understand what you wrote
   - You can't defend claims you didn't think through

❌ **Don't cite papers without reading them**
   - Minimum: Abstract + Conclusion + Cited Section
   - AI synthesis notes are LENSES for reading, not replacements

❌ **Don't accept AI's framing as YOUR framing**
   - The outline is a scaffold, not a script
   - Challenge it. Refine it. Make it yours.

## What to Do Instead

✅ **Use AI synthesis to organize YOUR thinking**
   - Let extracted themes guide WHERE you read, not WHAT you think
   - Example: AI says "Theme 1: Test scores improve" → Read those papers critically

✅ **Read papers through AI-identified lenses**
   - Methodological lens: What are limitations?
   - Consensus lens: Where do papers agree/diverge?
   - Gap lens: What questions remain unanswered?

✅ **Write YOUR argument, informed by AI structure**
   - Use outline as starting point
   - Revise as your understanding deepens
   - Own the intellectual work

## Next Steps: Engage Enhance Writing

Switch to [[../enhance-writing/references/academic-writing|Academic Writing Protocol]]:

**Phase 1: Literature Engagement**
- Your corpus is pre-screened, but YOU must READ papers
- Use AI synthesis notes as lenses, not summaries
- Take synthesis-ready notes: Claim, Evidence, Limitation, Connection

**Phase 2: Argument Construction**
- Test the AI-generated outline against your reading
- Map: Known → Unknown → Contribution
- Challenge consensus claims: Do 3+ papers really support this?

**Phase 3: Handle Contradictions**
- AI surfaced contradictions in Phase 2 synthesis notes
- Don't smooth them over—explain them
- Methodological? Temporal? Scope-based?

**Phase 4: Write Discussion**
- Interpretation: What do findings mean?
- Connection: How do they relate to existing work?
- Implication: What should change?
- Limitation: What can't I claim?

**Phase 5: Self-Review**
- Can I explain every paper without notes?
- Does my argument flow logically from question to answer?
- Have I addressed obvious criticisms proactively?
```

## Workflow Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID WORKFLOW                           │
│  Automate Mechanical Tasks  |  Preserve Intellectual Work   │
└─────────────────────────────────────────────────────────────┘

User Inputs
├── Research question (one sentence)
├── Screening criteria (inclusion/exclusion)
└── 50 candidate PDFs in corpus/candidates/

        ↓

┌───────────────────────┐
│ PHASE 1: SCREENING    │  🤖 AUTOMATED
│ Agent: Screener       │  Reads abstracts, applies criteria
└───────────────────────┘  Assigns relevance scores
        ↓
   [CHECKPOINT 1: User approves 23 papers]
        ↓
   Move approved PDFs to corpus/approved/

        ↓

┌───────────────────────┐
│ PHASE 2: EXTRACTION   │  🤖 AUTOMATED
│ Agent: Extractor      │  Extracts themes, claims, gaps
└───────────────────────┘  Identifies contradictions
        ↓
   Outputs: synthesis-notes_project.md
   - Theme 1: Test scores improve (5 papers)
   - Theme 2: Quality varies (8 papers)
   - Gap: Long-term retention unclear
   - Contradiction: SES effects mixed

        ↓

┌───────────────────────┐
│ PHASE 3: STRUCTURING  │  🤖 AUTOMATED
│ Agent: Structurer     │  Builds Known → Gap → Contribution
└───────────────────────┘  Creates logical outline
        ↓
   Outputs: argument-outline_project.md
   - Known: [AI synthesis of consensus]
   - Unknown: [AI-identified gaps]
   - Contribution: [AI-proposed framing]

        ↓
   [CHECKPOINT 2: User approves outline]
        ↓

╔═════════════════════════════════════════════════════╗
║                HANDOFF POINT                         ║
║                                                      ║
║  "Before you write, answer these provocations..."   ║
║                                                      ║
║  User receives:                                     ║
║  • Approved corpus (23 papers)                      ║
║  • Synthesis notes (themes as reading lenses)       ║
║  • Argument outline (scaffold, not script)          ║
║                                                      ║
║  User MUST:                                         ║
║  • Read papers (not just AI summaries)              ║
║  • Challenge AI's outline                           ║
║  • Own the intellectual work                        ║
║                                                      ║
║  Next: Enhance Writing Academic Writing Protocol  ║
╚═════════════════════════════════════════════════════╝

        ↓

┌───────────────────────┐
│ PHASE 4: DRAFTING     │  👤 HUMAN-LED
│ Mode: Provocation     │  (Enhance Writing)
└───────────────────────┘
        ↓
   User writes with provocations:
   - "Can you defend this claim with evidence?"
   - "What are you assuming here?"
   - "How does this connect to Theme X?"
   - "A skeptical reviewer would ask..."

        ↓

┌───────────────────────┐
│ PHASE 5: VALIDATION   │  🤖 AUTOMATED
│ Agent: Validator      │  (With human fixes)
└───────────────────────┘
        ↓
   Outputs: citation-validation_project.md
   - All citations checked against sources
   - Flags: 3 claims need stronger support
   - User fixes flagged issues

        ↓

┌───────────────────────┐
│ PHASE 6: FRAMING      │  🤝 HYBRID
│ Agent: Framer         │  AI offers options, user chooses
└───────────────────────┘
        ↓
   [CHECKPOINT 3: User selects framing]
   Options presented:
   - Supportive: Extends existing work
   - Challenging: Questions assumptions
   - Extending: Applies to new context

   User chooses: Extending (Project Atlas context)

        ↓

┌───────────────────────┐
│ PHASE 7: CONSISTENCY  │  🤖 AUTOMATED
│ Agent: Consistency    │  (User approves final)
└───────────────────────┘
        ↓
   Outputs: consistency-report_project.md
   - Intro ↔ Conclusion alignment: 85%
   - Claims ↔ Evidence alignment: 92%
   - Argument flow: Logical

   [CHECKPOINT 4: Final review]
        ↓

   ✅ Complete Literature Review
   - You understand the corpus deeply
   - You own the intellectual work
   - AI saved you 10+ hours of mechanical tasks
```

## Success Criteria

### You Did It Right If:

1. ✅ **You can explain every paper without notes**
   - Test: Close the AI outputs, explain the corpus from memory
   - If you can't, you relied too heavily on automation

2. ✅ **You challenged the AI's outline before accepting it**
   - Did you revise the "Known" section based on your reading?
   - Did you disagree with any AI-identified gaps?
   - Did you refine the contribution framing?

3. ✅ **You saved time on tedious tasks, not intellectual work**
   - Screening 50 papers: AI saved hours ✓
   - Reading 23 papers: You did this yourself ✓
   - Writing synthesis: You thought deeply, AI provoked ✓

4. ✅ **You finish having thought MORE deeply, not less**
   - Core Enhance Writing principle
   - AI was a cognitive enhancement tool, not a replacement

### You Did It Wrong If:

1. ❌ **You can't explain papers without AI summaries**
   - Sign you copy-pasted without understanding
   - Remedy: Go back, read papers yourself

2. ❌ **You accepted AI's outline uncritically**
   - Sign you treated scaffold as script
   - Remedy: Challenge every AI claim before writing

3. ❌ **Your draft reads like concatenated AI output**
   - Lacks YOUR voice, YOUR framing
   - Remedy: Rewrite in your own words, informed by structure

4. ❌ **You're citing papers you haven't read**
   - Academic integrity violation
   - Remedy: Read at minimum abstract + conclusion + cited section

## When to Use This Hybrid Workflow

### Use This Skill When:
- Starting from scratch with large corpus (20-100+ papers)
- Need systematic screening of many candidates
- Want structured extraction to organize initial reading
- Have limited time for mechanical tasks, want to focus on synthesis

### Use Pure Enhance Writing When:
- Already read papers, just need synthesis provocations
- Small corpus (< 10 papers) where screening isn't needed
- Deep dive into specific papers you've already identified
- Revising existing literature review for clarity

### Use Both (Recommended):
1. **This skill** for Phases 1-3: Discovery, screening, extraction
2. **Enhance Writing** for Phases 4-7: Synthesis, writing, refinement

## Philosophical Alignment

### Microsoft Research: Enhance Writing Framework

> "What would you rather have? A tool that thinks for you, or a tool that makes you think?"
> — Advait Sarkar, Microsoft Research

This hybrid workflow applies Enhance Writing principles:

| AI as Assistant (Wrong) | AI as Tool for Thought (Right) |
|-------------------------|--------------------------------|
| Automates everything | Automates tedious, preserves intellectual |
| Writes your literature review | Structures YOUR thinking about literature |
| Gives you answers | Helps you ask better questions |
| Optimizes for speed | Optimizes for understanding |
| You finish faster | You finish having thought more deeply |

**The handoff point (Phase 3→4) is the critical design decision** that preserves cognitive work while eliminating mechanical drudgery.

### Integration with an Existing Review Workflow

This skill extends your existing Enhance Writing skill:

```
Capture (Inbox)
  ↓
Process
  ↓
Create (Projects) ────┐
  ↓                   │
AI Work (.agent)  │
  │                   │
  ├─ [THIS SKILL] ───┤─── Automated discovery (Phases 1-3)
  │   Literature      │
  │   Review          │
  │   Automation      │
  │                   │
  └─ Tools for    ───┘─── Human synthesis (Phases 4-7)
     Thought
  ↓
Extract Learnings
  ↓
Reference (Knowledge Base)
```

## Related Documentation

- [[SKILL|Main Skill Definition]]
- [[README|Quick Start Guide]]
- [[references/workflow-phases|Detailed Phase Descriptions]]
- [[references/handoff-guide|Phase 3→4 Handoff Step-by-Step]]
- [[references/checkpoint-protocol|Human Checkpoint Guidelines]]
- [[../enhance-writing/SKILL|Enhance Writing Skill]]
- [[../enhance-writing/references/academic-writing|Academic Writing Protocol]]

## Version History

### v1.0 - 2026-01-11
- Initial integration philosophy
- Hybrid handoff design (Phase 3→4)
- Success criteria and anti-patterns
- Alignment with Enhance Writing framework


