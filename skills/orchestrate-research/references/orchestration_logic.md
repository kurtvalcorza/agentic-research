# Orchestration Logic: Detailed Specs

## Architecture Overview

### Three-Layer Intelligence Stack

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Context Detection                     │
│  - Corpus size analysis                         │
│  - Project path pattern matching                │
│  - Existing work detection                      │
│  - Resume capability scanning                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: Intelligent Routing                   │
│  - Workflow selection (LRA vs RLM)              │
│  - Output path resolution (3-level hierarchy)   │
│  - Validation skill injection                   │
│  - Mode selection (Quick vs Full)               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: Orchestration Execution               │
│  - Invokes selected workflow                    │
│  - Manages phase transitions                    │
│  - Handles validation gates                     │
│  - Recovers from interruptions                  │
└─────────────────────────────────────────────────┘
```

## Phase 0: Initialization & Context Detection

### Step 0.1: Corpus Analysis

**Goal:** Understand what we're working with

**Actions:**
1. **Count papers in corpus**
   ```bash
   pdf_count=$(find "$corpus_path" -name "*.pdf" | wc -l)
   md_count=$(find "$corpus_path" -name "*.md" | wc -l)
   total_papers=$((pdf_count + md_count))
   ```

2. **Detect existing work**
   ```bash
   # Check for LRA outputs
   if [ -f "phase1-screening-report.md" ]; then
     existing_work="standard-lra"
     last_phase=$(detect_last_completed_phase)
   fi

   # Check for RLM manifest
   if [ -f ".rlm-manifest.json" ]; then
     existing_work="recursive-lit-review"
     last_phase=$(jq -r '.current_phase' .rlm-manifest.json)
   fi
   ```

3. **Analyze corpus complexity** (for adaptive batching)
   ```python
   def analyze_corpus_complexity(corpus_path):
     papers = list_files(corpus_path)
     complexity_profile = {
       "simple": 0,      # <10 pages
       "standard": 0,    # 10-30 pages
       "complex": 0,     # 30-100 pages
       "book": 0         # >100 pages
     }

     for paper in papers:
       page_count = get_page_count(paper)
       if page_count < 10:
         complexity_profile["simple"] += 1
       elif page_count < 30:
         complexity_profile["standard"] += 1
       elif page_count < 100:
         complexity_profile["complex"] += 1
       else:
         complexity_profile["book"] += 1

     return complexity_profile
   ```

**Output Example:**
```python
corpus_analysis = {
  "total_papers": 150,
  "pdf_count": 145,
  "md_count": 5,
  "complexity_profile": {
    "simple": 50,
    "standard": 80,
    "complex": 15,
    "book": 5
  },
  "existing_work": None,  # or "standard-lra" or "recursive-lit-review"
  "last_completed_phase": None  # or "phase2", etc.
}
```

### Step 0.2: Project Context Detection

**Goal:** Determine where outputs should be saved

**Logic:**
- **Level 1 - Example Research Institute Projects** (Highest Priority)
  - Pattern: `01_Projects/Example Research Institute/{project}/research/corpus/`
  - Output: `01_Projects/Example Research Institute/{project}/research/outputs/`
  - Auto-detected for: Project Atlas, Project Quartz, Project Skye, Project Beacon, Project Nova

- **Level 2 - Generic Research**
  - Pattern: `01_Projects/Research/{project}/corpus/`
  - Output: `01_Projects/Research/outputs/literature-reviews/{project}/outputs/`

- **Level 3 - Standalone** (Fallback)
  - Pattern: Arbitrary path (Desktop, Downloads, etc.)
  - Prompt user with 3 options:
    - Option 1: `01_Projects/Research/outputs/literature-reviews/{auto-name}/` (recommended)
    - Option 2: `{corpus_path}/outputs/` (same location as corpus)
    - Option 3: Custom path (user specifies)

### Step 0.3: Workflow Selection Decision Tree

**Decision Logic:**

```python
def select_workflow(corpus_analysis, project_context):
  total_papers = corpus_analysis["total_papers"]
  existing_work = corpus_analysis["existing_work"]

  if existing_work == "standard-lra":
    return {"workflow": "standard-lra", "mode": "resume", "start_phase": corpus_analysis["last_completed_phase"] + 1}

  if existing_work == "recursive-lit-review":
    return {"workflow": "recursive-lit-review", "mode": "resume", "start_phase": corpus_analysis["last_completed_phase"]}

  if total_papers <= 15:
    return {"workflow": "standard-lra", "mode": "quick", "estimated_time": "15-25 minutes"}

  if total_papers <= 50:
    return {"workflow": "standard-lra", "mode": "full", "estimated_time": "30-90 minutes"}

  if total_papers <= 150:
    return {"workflow": "recursive-lit-review", "mode": "standard", "estimated_time": "60-120 minutes"}

  # ... see original SKILL.md for more complexity ranges
```
