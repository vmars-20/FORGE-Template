# Generic Submodule Documentation Refactoring Prompt

**Purpose:** Align any submodule with the parent monorepo's 3-tier documentation architecture.

**Use this prompt when:** You want to optimize a submodule's documentation for LLM token efficiency and self-contained operation.

---

## Prompt Template

```
You are working inside a git submodule that is part of a larger monorepo.

Current location: [FILL IN: e.g., /path/to/monorepo/libs/my-submodule]
Submodule purpose: [FILL IN: brief 1-sentence description]

## Context: Parent Monorepo Architecture

This monorepo follows a hierarchical 3-tier documentation system optimized for LLM context efficiency:

**Property 1: Self-Contained Authoritative Bubbles**
- Each submodule should be authoritative for its domain
- Zero dependencies on parent monorepo (works standalone)
- Can be used by other projects

**Property 3: Three-Tier Documentation System**
- **Tier 1**: llms.txt - Quick reference catalog (~500-1000 tokens)
  - Component/feature listing
  - Basic usage examples
  - Pointers to Tier 2

- **Tier 2**: CLAUDE.md - Authoritative self-contained guide (~3-5k tokens)
  - Design rationale
  - Core patterns and standards
  - Integration guidance
  - Should be self-sufficient for 90% of common tasks

- **Tier 3**: Specialized docs - Load only when needed (5-10k tokens each)
  - Deep technical details
  - Troubleshooting guides
  - Implementation specifics
  - Reference material

**Property 5: Token-Efficient Context Loading**
- Start with Tier 1 (~1k tokens)
- Escalate to Tier 2 only when needed (~4k tokens total)
- Reserve 190k+ tokens for actual work
- Minimize documentation overlap and redundancy

**Design Principle:**
"Default to silence. Escalate consciously. Preserve context religiously."

---

## Your Task

**Phase 1: Assessment**

1. Review the current documentation structure in this submodule:
   - What documentation files exist?
   - How many lines/tokens per file?
   - What's the current hierarchy (if any)?
   - Is there overlap/redundancy?
   - Does it follow the 3-tier pattern?

2. Assess current state:
   - Is `llms.txt` present? Is it concise (~500-1000 tokens)?
   - Is `CLAUDE.md` present? Is it self-contained and authoritative?
   - Are specialized docs properly separated?
   - Are there historical/deprecated docs that should be archived?
   - Are there project-specific references that hurt standalone use?

**Phase 2: Proposal**

Based on your assessment, propose a refactoring plan:

1. **Tier 1 (llms.txt)**:
   - What should be in the quick reference?
   - Does it need creation, enhancement, or consolidation?

2. **Tier 2 (CLAUDE.md)**:
   - What core knowledge belongs here?
   - What should be consolidated from other docs?
   - Should it be created or enhanced?

3. **Tier 3 (Specialized docs)**:
   - What specialized docs are needed?
   - Should any be created, merged, or archived?
   - What's the optimal organization?

4. **Cleanup**:
   - What should be archived (with timestamps)?
   - What should be deleted?
   - What references should be updated?

**Phase 3: Metrics**

Estimate the impact:
- Before: X lines across Y documents
- After: X lines across Y documents
- Reduction: Z%
- Token efficiency improvement: estimated W%

**Phase 4: Execution Plan**

Provide a step-by-step execution plan:
1. What edits to make (be specific)
2. What to create
3. What to archive
4. What to update (cross-references)
5. Git workflow (commit strategy)

---

## Key Constraints

- **Self-contained**: Remove dependencies on parent monorepo docs
- **Standalone naming**: Remove historical project references
- **No duplication**: Each piece of information should live in ONE place
- **Progressive disclosure**: Common tasks → Tier 2, deep details → Tier 3
- **Token conscious**: Every line should justify its token cost

---

## Success Criteria

✅ Tier 1 (llms.txt) exists and is concise (~500-1000 tokens)
✅ Tier 2 (CLAUDE.md) is authoritative and self-contained (~3-5k tokens)
✅ Tier 3 specialized docs are properly separated and indexed
✅ No documentation redundancy or overlap
✅ Submodule works standalone (no parent dependencies)
✅ Historical/deprecated content archived or removed
✅ Cross-references updated
✅ Overall token reduction achieved (target: 30-50%)

---

## Example: forge-vhdl Submodule Results

**Before refactoring:**
- 8 documents, 4,041 lines
- Unclear hierarchy
- Significant overlap
- VOLO/EZ-EMFI historical references

**After refactoring:**
- 5 documents, 2,337 lines (42% reduction)
- Clear 3-tier structure:
  - Tier 1: llms.txt (124 lines, ~500 tokens)
  - Tier 2: CLAUDE.md (742 lines, ~3.5k tokens, AUTHORITATIVE)
  - Tier 3: 3 specialized docs (load as needed)
- All historical references removed
- 5 docs archived with timestamps
- 50% token efficiency improvement for common tasks

---

## Getting Started

Please analyze the current documentation structure and provide:
1. **Assessment**: Current state analysis
2. **Proposal**: Specific refactoring recommendations
3. **Metrics**: Estimated impact
4. **Plan**: Step-by-step execution instructions

Then ask: "Should I proceed with this plan?"
```

---

## Notes for Multiple Submodules

This is a **template prompt** - customize the `[FILL IN]` sections for each submodule.

**Recommended workflow:**
1. cd into target submodule
2. Fill in the template for that specific context
3. Paste into Claude Code
4. Review the proposal before executing
5. Iterate if needed

**Save this template at:** `docs/migration/SUBMODULE_DOC_REFACTOR_TEMPLATE.md` (parent monorepo level)

---

**Version:** 1.0 (2025-11-04)
**Based on:** forge-vhdl successful refactoring (v2.0.0)
