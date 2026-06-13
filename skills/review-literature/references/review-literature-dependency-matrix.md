# Review Literature: Dependency Matrix

**Purpose**: Explicit dependency checking and validation for Review Literature workflow

**Pattern Source**: Adapted from an internal dependency matrix

---

## Phase Dependency Graph

```
Phase 0: Criteria Generation (OPTIONAL)
  ├─ Dependencies: None (optional entry point)
  ├─ Required Inputs: User research question (or defaults provided)
  └─ Produces: settings/screening-criteria.md, settings/research-question.md

Phase 1: Corpus Screening
  ├─ Dependencies: None (or Phase 0 if criteria needed)
  ├─ Required Inputs: corpus/candidates/*.pdf OR screening criteria
  └─ Produces: outputs/phase1-screening-report_project.md, corpus/approved/

Phase 2: Extraction & Synthesis
  ├─ Dependencies: Phase 1 MUST be complete
  ├─ Required Inputs: corpus/approved/*.pdf (screened papers)
  └─ Produces: outputs/phase2-synthesis-notes_project.md

Phase 3: Argument Structuring
  ├─ Dependencies: Phase 1 AND Phase 2 MUST be complete
  ├─ Required Inputs: outputs/phase2-synthesis-notes_project.md
  └─ Produces: outputs/phase3-argument-outline_project.md

Phase 4: Drafting (Human-Led with Enhance Writing)
  ├─ Dependencies: Phase 1, 2, AND 3 MUST be complete
  ├─ Required Inputs: phase2-synthesis-notes_project.md, phase3-argument-outline_project.md
  └─ Produces: outputs/phase4-handoff-document_project.md, user-written draft sections

Phase 5: Citation Validation
  ├─ Dependencies: Phase 4 MUST be complete (draft exists)
  ├─ Required Inputs: User draft sections, phase2-synthesis-notes_project.md (for citation tracking)
  └─ Produces: outputs/phase5-citation-validation_project.md

Phase 6: Contribution Framing
  ├─ Dependencies: Phase 3 AND Phase 4 MUST be complete
  ├─ Required Inputs: phase3-argument-outline_project.md, draft sections
  └─ Produces: outputs/phase6-contribution-framing_project.md

Phase 7: Consistency Validation
  ├─ Dependencies: Phase 3, 4, AND 6 MUST be complete (Phase 5 recommended)
  ├─ Required Inputs: All major outputs from Phases 3, 4, 6
  └─ Produces: outputs/phase7-consistency-report_project.md
```

---

## Quick Mode Dependency Graph (3 Phases)

```
Phase 1: Corpus Screening
  ├─ Dependencies: None
  ├─ Required Inputs: corpus/candidates/*.pdf
  └─ Produces: outputs/screening-report_project.md

Phase 2: Extraction & Synthesis
  ├─ Dependencies: Phase 1 MUST be complete
  ├─ Required Inputs: corpus/approved/*.pdf
  └─ Produces: outputs/synthesis-notes_project.md

Phase 3: Argument Structuring (with inline drafting guidance)
  ├─ Dependencies: Phase 1 AND 2 MUST be complete
  ├─ Required Inputs: outputs/synthesis-notes_project.md
  └─ Produces: outputs/argument-outline_project.md, drafting-guide.md
```

---

## Phase Dependency Definitions

### Phase 0: Criteria Generation (OPTIONAL)

```yaml
dependencies:
  phases: []  # No dependencies (optional entry point)
  files: []   # No file dependencies

required_inputs:
  - type: "user_input"
    description: "Research question (can be provided via Q&A or directly)"
    fallback: "If not provided, use interactive Q&A"

produces:
  required:
    - settings/screening-criteria.md
    - settings/research-question.md
  optional: []

skip_conditions:
  - "User provides screening criteria directly"
  - "Using default screening criteria"
  - "Expert user mode"
```

---

### Phase 1: Corpus Screening

```yaml
dependencies:
  phases: []  # Can start independently
  phases_optional: [0]  # Phase 0 optional if criteria provided
  files: []   # Discovers corpus dynamically

required_inputs:
  - type: "corpus_files"
    location: "corpus/candidates/"
    pattern: "*.pdf OR *.md"
    minimum: 1
    validation: "Files must be readable"

  - type: "screening_criteria"
    sources:
      - settings/screening-criteria.md (from Phase 0)
      - User-provided criteria
      - Default criteria
    fallback: "Use default academic screening criteria"

produces:
  required:
    - outputs/phase1-screening-report_project.md
  optional:
    - corpus/approved/ (screened papers copied here)
    - corpus/rejected/ (rejected papers with justifications)

validation:
  - check: "At least 1 PDF approved"
    error: "No papers passed screening. Review criteria or corpus."
  - check: "Screening report has structured format (Approved/Rejected sections)"
    error: "Screening report appears malformed"
```

---

### Phase 2: Extraction & Synthesis

```yaml
dependencies:
  phases: [1]  # MUST complete Phase 1
  files:
    - outputs/phase1-screening-report_project.md
    - corpus/approved/*.pdf (at least 1 file)

validation:
  - check: "corpus/approved/ contains at least 1 PDF"
    error: "No approved papers found. Re-run Phase 1 or check file locations."
  - check: "phase1-screening-report_project.md contains 'Approved Papers' section"
    error: "Screening report missing approved papers section"

produces:
  required:
    - outputs/phase2-synthesis-notes_project.md
  optional:
    - outputs/phase2-theme-map_project.md (visual theme network)

validation_post:
  - check: "synthesis-notes_project.md contains at least 3 themes"
    warning: "Synthesis identified fewer than 3 themes. Corpus may be too narrow."
  - check: "synthesis-notes_project.md size > 2000 bytes"
    error: "Synthesis notes appear incomplete or empty"
```

---

### Phase 3: Argument Structuring

```yaml
dependencies:
  phases: [1, 2]  # MUST complete Phases 1 AND 2
  files:
    - outputs/phase2-synthesis-notes_project.md

validation:
  - check: "synthesis-notes_project.md exists and is readable"
    error: "Synthesis notes missing. Re-run Phase 2."
  - check: "synthesis-notes_project.md has theme structure"
    error: "Synthesis notes malformed (missing themes)"

produces:
  required:
    - outputs/phase3-argument-outline_project.md
  optional:
    - outputs/phase3-evidence-map_project.md

validation_post:
  - check: "argument-outline_project.md has 'Known', 'Unknown', 'Contribution' sections"
    error: "Outline missing required sections (Known/Unknown/Contribution)"
  - check: "outline has evidence strength labels (Strong/Moderate/Weak)"
    warning: "Outline missing evidence labels. May need refinement."
```

---

### Phase 4: Drafting (Human-Led)

```yaml
dependencies:
  phases: [1, 2, 3]  # MUST complete Phases 1, 2, AND 3
  files:
    - outputs/phase2-synthesis-notes_project.md
    - outputs/phase3-argument-outline_project.md

validation:
  - check: "All prerequisite files exist"
    error: "Missing inputs for drafting phase"
  - check: "Enhance Writing skill available"
    warning: "Drafting phase uses Enhance Writing. Ensure skill is loaded."

produces:
  required:
    - outputs/phase4-handoff-document_project.md
  optional:
    - User-written draft sections (not tracked by orchestrator)

validation_post:
  - check: "handoff-document_project.md exists"
    warning: "Handoff document missing. Phase 4 may not have completed."
  - note: "Phase 4 produces user-written content. Orchestrator cannot validate draft quality."
```

---

### Phase 5: Citation Validation

```yaml
dependencies:
  phases: [4]  # MUST complete Phase 4 (draft exists)
  phases_recommended: [1, 2, 3]  # Should have all context
  files:
    - User draft sections (provided by user)
    - outputs/phase2-synthesis-notes_project.md (for citation cross-reference)

validation:
  - check: "User provides draft sections or file paths"
    error: "No draft content provided. Cannot Validate Consistency."
  - check: "synthesis-notes_project.md exists (for citation tracking)"
    warning: "Citation tracking file missing. Validation may be limited."

produces:
  required:
    - outputs/phase5-citation-validation_project.md
  optional:
    - outputs/phase5-suggested-fixes_project.md

validation_post:
  - check: "citation-validation_project.md contains validation score"
    error: "Validation report malformed (missing score)"
  - check: "No critical issues found (score >= 70)"
    warning: "Citation validation found critical issues. Review required."
```

---

### Phase 6: Contribution Framing

```yaml
dependencies:
  phases: [3, 4]  # MUST complete Phases 3 AND 4
  phases_recommended: [5]  # Phase 5 recommended but not required
  files:
    - outputs/phase3-argument-outline_project.md
    - User draft sections

validation:
  - check: "argument-outline_project.md exists and has 'Contribution' section"
    error: "Outline missing or lacks contribution framing"
  - check: "Draft sections available for context"
    warning: "No draft provided. Framing will be generic."

produces:
  required:
    - outputs/phase6-contribution-framing_project.md

validation_post:
  - check: "contribution-framing_project.md has multiple positioning options"
    warning: "Framing document appears incomplete (only one option)"
```

---

### Phase 7: Consistency Validation

```yaml
dependencies:
  phases: [3, 4, 6]  # MUST complete Phases 3, 4, AND 6
  phases_recommended: [5]  # Phase 5 recommended for complete validation
  files:
    - outputs/phase3-argument-outline_project.md
    - User draft sections
    - outputs/phase6-contribution-framing_project.md

validation:
  - check: "All required files exist"
    error: "Missing prerequisite files for consistency validation"
  - check: "Draft has introduction and conclusion sections"
    warning: "Draft appears incomplete. Consistency check will be limited."

produces:
  required:
    - outputs/phase7-consistency-report_project.md
  optional:
    - outputs/phase7-final-review-checklist_project.md

validation_post:
  - check: "consistency-report_project.md contains consistency score"
    error: "Validation report malformed"
  - check: "Consistency score >= 75"
    warning: "Consistency issues detected. Review recommendations."
```

---

## Quick Mode Validation Rules

### Quick Mode Phase 1: Screening (Same as Full Mode)
- See Phase 1 definition above

### Quick Mode Phase 2: Extraction (Same as Full Mode)
- See Phase 2 definition above

### Quick Mode Phase 3: Argument + Drafting Guidance

```yaml
dependencies:
  phases: [1, 2]  # Quick Mode Phases 1 and 2
  files:
    - outputs/synthesis-notes_project.md

validation:
  - check: "synthesis-notes_project.md exists"
    error: "Synthesis notes missing. Re-run Phase 2."

produces:
  required:
    - outputs/argument-outline_project.md
    - outputs/drafting-guide.md (simplified handoff)

validation_post:
  - check: "Both outline and drafting guide produced"
    warning: "Quick Mode output incomplete"

notes:
  - "Quick Mode Phase 3 combines Full Mode Phases 3 and 4"
  - "Drafting guide is simplified version of handoff document"
  - "User expected to draft independently after this phase"
```

---

## Error Messages and Recovery Actions

### Missing Prerequisite Phase

```markdown
❌ Cannot Invoke Phase 3: Argument Structuring

Reason: Phase 2 (Extraction & Synthesis) not completed

Current Workflow State:
✅ Phase 0: Criteria Generation (skipped - using defaults)
✅ Phase 1: Corpus Screening (completed)
❌ Phase 2: Extraction & Synthesis (not started)
⬜ Phase 3: Argument Structuring (cannot start)

Required Actions:
1. Complete Phase 2 first
2. Then retry Phase 3

Options:
[r] Run Phase 2 now (recommended)
[i] Check why Phase 2 wasn't run
[x] Cancel operation
```

---

### Missing Corpus Files

```markdown
❌ Cannot Invoke Phase 1: Corpus Screening

Reason: No corpus files found

Expected Location: corpus/candidates/
Found: 0 PDF files

Possible Causes:
- No PDFs placed in corpus/candidates/ directory
- PDFs in wrong location
- Incorrect file permissions

Recovery Options:
[l] List files in current directory (check if PDFs elsewhere)
[m] Manually specify corpus location
[c] Create corpus/candidates/ directory and add PDFs
[x] Cancel operation
```

---

### Missing Screening Criteria (Phase 1 without Phase 0)

```markdown
⚠️ Phase 1 Invoked Without Screening Criteria

Phase 0 was skipped, and no custom criteria provided.

Options:
[d] Use default academic screening criteria (recommended)
   - Peer-reviewed publications
   - Published within last 10 years
   - Directly addresses research question
   - Empirical or theoretical contribution

[c] Provide custom criteria now (interactive)
[0] Run Phase 0 interactively (full guidance)
[x] Cancel operation

Recommendation: Use default criteria if you're familiar with literature reviews.
```

---

### Empty or Incomplete Output File

```markdown
⚠️ Warning: Phase 2 Output Appears Incomplete

File: outputs/phase2-synthesis-notes_project.md
Size: 487 bytes (expected >2000 bytes)
Issue: File is unusually small

Possible Causes:
- Phase 2 agent interrupted mid-write
- Corpus too small (only 1-2 papers?)
- Processing error not logged

Recovery Options:
[i] Inspect file content (review what was written)
[r] Re-run Phase 2 (recommended)
[c] Continue anyway (Phase 3 may fail)
[x] Cancel operation

Recommendation: Inspect file first, then decide whether to re-run.
```

---

## Integration with Orchestrate Research

### Add Dependency Validation to Orchestrate Research

```markdown
## Phase Invocation Pattern (Enhanced with Validation)

### Step 0: Dependency Validation (MANDATORY)

Before spawning agent for any phase:

1. **Load dependency matrix**:
   - Read `review-literature-dependency-matrix.md`
   - Identify phase dependencies and required files

2. **Check execution state**:
   - Load workflow state (if exists)
   - Verify prerequisite phases completed
   - Check completion timestamps

3. **Verify file existence**:
   - Check all required input files exist
   - Verify minimum file sizes (non-empty)
   - Validate corpus directory for Phase 1

4. **Perform phase-specific validation**:
   - Phase 1: Corpus files exist
   - Phase 2: Approved corpus has >0 papers
   - Phase 3: Synthesis notes have theme structure
   - Phase 4: Enhance Writing skill available
   - Phases 5-7: User draft sections provided

5. **Decision logic**:
   ```
   IF all_dependencies_met AND all_files_valid:
     ✅ Proceed with phase execution

   ELSE IF phase_0_skipped AND no_criteria:
     ⚠️  Offer to use default criteria OR run Phase 0
     User choice: [use defaults | run Phase 0 | provide custom | cancel]

   ELSE IF missing_required_phase:
     ❌ Block phase execution
     Display: Error message + recovery options
     Require: User to run prerequisite phase

   ELSE IF missing_required_file OR file_invalid:
     ❌ Block phase execution
     Suggest: Re-run phase that produces file OR locate file manually
   ```

### Example Enhanced Invocation

```markdown
User: "Run Phase 3 of Review Literature"

Orchestrator performs validation:

Step 0.1: Check Phase Dependencies
- Phase 0: ⏭️ Skipped (using default criteria)
- Phase 1: ✅ Completed (2026-01-12 10:15:30)
- Phase 2: ✅ Completed (2026-01-12 10:28:45)

Step 0.2: Check Required Files
- phase1-screening-report_project.md: ✅ Exists (4,231 bytes)
- phase2-synthesis-notes_project.md: ✅ Exists (12,543 bytes)
- corpus/approved/: ✅ Contains 18 PDFs

Step 0.3: Validate File Integrity
- synthesis-notes_project.md: ✅ Valid (14 themes identified)
- Approved corpus: ✅ 18 papers ready for structuring

Step 0.4: Decision
✅ All dependencies satisfied

Proceeding to Phase 3: Argument Structuring...
```

---

## Validation Function (Pseudo-code)

```javascript
function validateReviewLiteraturePhasePrerequisites(phaseNumber, workflowMode) {
  const dependencies = REVIEW_LITERATURE_DEPENDENCIES[workflowMode][phaseNumber];
  const issues = [];

  // Special handling for Phase 0 (optional)
  if (phaseNumber === 0) {
    return { canProceed: true, isOptional: true };
  }

  // Check prerequisite phases
  for (const prereqPhase of dependencies.phases) {
    if (!isPhaseCompleted(prereqPhase)) {
      issues.push({
        type: "BLOCKING",
        message: `Phase ${prereqPhase} must be completed first`,
        recovery: `run_phase_${prereqPhase}`
      });
    }
  }

  // Check required files
  for (const file of dependencies.files) {
    if (!fileExists(file)) {
      issues.push({
        type: "BLOCKING",
        message: `Required file missing: ${file}`,
        recovery: "regenerate_prerequisite_or_locate_manually"
      });
    } else if (fileSize(file) < dependencies.minFileSize || 100) {
      issues.push({
        type: "WARNING",
        message: `File appears incomplete: ${file} (${fileSize(file)} bytes)`,
        recovery: "inspect_or_regenerate"
      });
    }
  }

  // Phase-specific validation
  if (phaseNumber === 1 && !corpusFilesExist()) {
    issues.push({
      type: "BLOCKING",
      message: "No corpus files found in corpus/candidates/",
      recovery: "add_pdfs_to_corpus_directory"
    });
  }

  if (phaseNumber === 2 && approvedCorpusCount() === 0) {
    issues.push({
      type: "BLOCKING",
      message: "Phase 1 approved 0 papers. Cannot extract from empty corpus.",
      recovery: "review_screening_criteria_or_expand_corpus"
    });
  }

  // Check recommended phases (warnings only)
  for (const recPhase of dependencies.phases_recommended || []) {
    if (!isPhaseCompleted(recPhase)) {
      issues.push({
        type: "WARNING",
        message: `Phase ${recPhase} recommended but not completed`,
        recovery: "optional"
      });
    }
  }

  return {
    canProceed: issues.filter(i => i.type === "BLOCKING").length === 0,
    blockingIssues: issues.filter(i => i.type === "BLOCKING"),
    warnings: issues.filter(i => i.type === "WARNING")
  };
}
```

---

## Benefits of Dependency Guardrails for Review Literature

### 1. Prevents Common User Errors
- Can't run Phase 3 without synthesis notes
- Can't start Phase 1 without corpus files
- Can't skip Phase 0 without providing criteria or accepting defaults

### 2. Clearer User Experience
- Explicit error messages explain WHY phase can't run
- Recovery options guide user to resolution
- Progress is always clear and validated

### 3. Supports Both Quick and Full Mode
- Quick Mode: 3-phase simplified dependency chain
- Full Mode: 8-phase comprehensive validation
- User can seamlessly switch between modes

### 4. Handles Optional Phase 0
- Phase 0 is truly optional (not a dependency)
- If skipped, offers defaults or custom criteria
- No confusion about "required" vs "optional"

### 5. Better Debugging
- Easy to diagnose workflow issues
- Clear audit trail of what succeeded/failed
- State validation utility can check integrity

---

**Created:** 2026-01-12
**Maintainer:** (your name)
**Status:** Active specification
**Priority:** High (consistency with Deep Research Synthesis)
**Related:**
- [[../../../subagents/phase-dependency-matrix|DRS Dependency Matrix]]
- [[../../../subagents/validate-workflow-state|Workflow State Validator]]
- [[../SKILL|Review Literature]]






