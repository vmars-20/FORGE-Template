# Quick Submodule Documentation Refactoring Prompt

**Copy-paste this into Claude Code when working inside ANY submodule:**

---

```
I'm working inside a git submodule. Help me refactor the documentation to follow our monorepo's 3-tier architecture.

## Background: 3-Tier Documentation System

Our monorepo uses a hierarchical documentation system:

**Tier 1: llms.txt** (~500-1000 tokens)
- Quick reference catalog
- Component listing + basic usage
- Pointers to Tier 2

**Tier 2: CLAUDE.md** (~3-5k tokens)
- AUTHORITATIVE, self-contained
- Design rationale + core patterns
- Should handle 90% of common tasks

**Tier 3: Specialized docs** (load as needed)
- Deep technical details
- Troubleshooting guides
- Reference material

**Design principle:** "Default to silence. Escalate consciously. Preserve context religiously."

## Your Task

1. **Assess** current documentation:
   - What exists? How many lines/tokens?
   - Does it follow 3-tier pattern?
   - Any overlap, redundancy, or historical cruft?

2. **Propose** refactoring plan:
   - What should be in Tier 1 (llms.txt)?
   - What should be in Tier 2 (CLAUDE.md)?
   - What specialized docs (Tier 3)?
   - What should be archived/removed?
   - Estimated token reduction?

3. **Ask for approval** before executing

## Constraints

✅ Self-contained (no parent monorepo dependencies)
✅ No duplication (one source of truth per concept)
✅ Standalone naming (remove historical project references)
✅ Token-conscious (justify every line)

## Success Metrics

Target: 30-50% documentation reduction
- Tier 1 exists and is concise
- Tier 2 is authoritative and self-sufficient
- Tier 3 properly separated
- Zero redundancy

## Example Results

**forge-vhdl submodule:**
- Before: 8 docs, 4,041 lines
- After: 5 docs, 2,337 lines (42% reduction)
- Token efficiency: 50% improvement for common tasks

---

Please analyze THIS submodule's docs and propose a refactoring plan.
```

---

**Usage:**
1. `cd` into any submodule
2. Copy the prompt above
3. Paste into Claude Code
4. Review proposal
5. Approve or iterate
6. Execute

**Save template at (parent monorepo):**
`docs/migration/SUBMODULE_DOC_REFACTOR_TEMPLATE.md`
