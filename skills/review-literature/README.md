# Review Literature

Full 7-phase literature review automation with hybrid human-AI collaboration. Automates mechanical phases, preserves human intellectual ownership for synthesis and interpretation.

## Philosophy

**Automate extraction, not insight.** Machines are good at pattern matching and data structuring. Humans are good at meaning-making and argumentation.

## The 7 Phases

**Automated Phases (0-3)**
- **Phase 0**: Generate screening criteria (interactive)
- **Phase 1**: Screen literature against criteria
- **Phase 2**: Extract structured data to matrix
- **Phase 3**: Structure findings into synthesis document

**Human-Led Phases (4-7)** with AI support
- **Phase 4**: Draft manuscript (human writes, AI enhances)
- **Phase 5**: Validate citations (automated check)
- **Phase 6**: Frame contributions (AI provocation, human decides)
- **Phase 7**: Validate consistency (automated quality check)

## Execution Model

Uses **RLM (Research Literature Management)** execution model:
- Multiple checkpoints for user approval
- State preservation between phases
- Rollback capability
- Quality gates prevent advancing with errors

## Checkpoints

After each phase, you approve/reject before continuing:
- ✅ Approve → Advance to next phase
- ⏸️ Pause → Save state, resume later
- ↩️ Rollback → Return to previous phase
- 🚫 Reject → Fix issues before advancing

## What Gets Automated

- PDF text extraction
- Screening against binary criteria
- Data extraction to structured matrix
- Synthesis document scaffolding
- Citation validation
- Consistency checking

## What Stays Human

- Research question formulation
- Argumentation and interpretation
- Claim synthesis
- Contribution framing
- Final judgment calls

## Inputs Required

- Research question or topic
- Access to paper PDFs or abstracts
- Domain expertise for edge cases
- Judgment on quality thresholds

## Outputs

- `screening-criteria.md` - Operational filters
- `extraction-matrix.csv` - Structured data
- `synthesis.md` - Organized findings
- `draft-manuscript.md` - First complete draft
- `validation-report.md` - Quality checks
- `contributions.md` - Framed significance

## When to Use

- Starting a systematic review
- Meta-analysis or scoping review
- Literature chapter for dissertation
- Grant proposal background
- Research synthesis for publication

## Related Skills

- `generate-screening-criteria` - Phase 0
- `screen-literature` - Phase 1
- `synthesize-research` - Phase 4
- `validate-citations` - Phase 5
- `frame-contributions` - Phase 6
- `validate-consistency` - Phase 7
- `recursive-lit-review` - For 50-500+ papers

## Typical Timeline

- **Small review (10-20 papers)**: 2-3 hours
- **Medium review (20-50 papers)**: 4-8 hours
- **Large review (50+ papers)**: Use `recursive-lit-review` instead
