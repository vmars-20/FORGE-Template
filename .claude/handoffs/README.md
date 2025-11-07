# Session Handoff Prompts

**Purpose:** Capture session context for continuation in new sessions or by other developers

**NOTE:** These handoffs are historical records from the original development of this template. They may contain user-specific paths (e.g., `/Users/vmars20/`, `/Users/johnycsh/`) that were relevant during development but should be ignored when using this as a template.

---

## What Are Handoff Prompts?

Session handoff prompts are detailed summaries that enable:
- ✅ **Continuation** - Pick up exactly where you left off in a new session
- ✅ **Collaboration** - Share context with teammates or AI agents
- ✅ **Documentation** - Historical record of what was done and why
- ✅ **Learning** - Examples of how to structure complex tasks

---

## Naming Convention

```
YYYY-MM-DD_HHMM_<brief-description>.md
```

**Examples:**
- `2025-11-06_1740_bpd-fsm-observer-test-fix.md`
- `2025-11-07_0930_voltage-package-migration.md`
- `2025-11-08_1500_cocotb-agent-improvements.md`

**Rationale:**
- Date/time prefix → Chronological ordering
- Brief description → Quick identification
- Markdown format → Easy to read and edit

---

## When to Create a Handoff

### Always Create When:
1. **Session ends mid-task** - Incomplete work that needs continuation
2. **Complex context** - Multiple interrelated changes (migrations, refactors)
3. **Agent handoff** - Delegating to specialized agent in new session
4. **Hitting tool limitations** - Need to restart with different approach

### Optional (But Useful):
5. **Major milestones** - Document completed multi-step workflows
6. **Blocked on external** - Waiting for feedback, resources, or decisions
7. **Teaching moments** - Show teammates how to approach similar problems

### Don't Create When:
- ❌ Simple one-command tasks
- ❌ Already documented in commit messages
- ❌ Routine maintenance work

---

## Handoff Template Structure

### Required Sections

1. **Header**
   - Date/time
   - Previous session summary
   - Current goal
   - Next session owner (human/agent)

2. **Context: What We Just Did**
   - Completed work (with ✅ markers)
   - Files modified
   - Architectural changes
   - Rationale for decisions

3. **Current Goal**
   - Clear objective for next session
   - Expected outcome
   - Success criteria

4. **Available Resources**
   - Relevant documentation
   - Agent definitions (if applicable)
   - External reference files
   - Related repositories

5. **Execution Plan**
   - Step-by-step approach
   - Decision points
   - Likely issues and solutions

6. **Quick Reference**
   - Commands to run
   - Paths to check
   - Key files to review

### Optional Sections

- **Decision Points** - Unresolved choices needing input
- **Known Issues** - Problems encountered but not yet fixed
- **Related Files** - Complete list of modified files
- **Previous Session Summary** - Link to prior handoffs
- **Notes for Specific Tools** - Agent-specific guidance

---

## Example: Good vs Bad Handoffs

### ❌ Bad Handoff (Too Vague)

```markdown
# Fix Tests

**Goal:** Get tests working

**Context:** Tests are broken

**Next Steps:** Fix them
```

**Problems:**
- No context about what was done
- No information about what's broken
- No guidance on how to fix
- No success criteria

### ✅ Good Handoff

```markdown
# Session Handoff: BPD FSM Observer Test Fix

**Date:** 2025-11-06 17:40
**Goal:** Get test_bpd_fsm_observer_progressive.py working

## Context: What We Just Did

1. Migrated VHDL packages from tools/forge-codegen/vhdl/ → libs/forge-vhdl/vhdl/packages/
   - Renamed: basic_app_*_pkg.vhd → forge_serialization_*_pkg.vhd
   - See: VHDL_SERIALIZATION_MIGRATION.md

2. Cleaned bpd-tiny-vhdl/tests/ directory
   - Removed: bpd_forge_tests/, mcc/, sim_build/
   - Kept: bpd_fsm_observer_tests/ (FSM observer tests only)

## Current Goal

Get FSM observer tests passing with <20 line output.

**Expected command:**
```bash
cd bpd-tiny-vhdl/tests && python run.py bpd_fsm_observer
```

**Likely issues:**
1. Package name mismatches (basic_app_* → forge_serialization_*)
2. Stub files in src/ need updating
3. Import path issues

## Resources

- Agent: .claude/agents/cocotb-integration-test/
- External reference: /Users/vmars20/TTOP/BPD-002v2/bpd-tiny-vhdl/tests/
- Docs: libs/forge-vhdl/CLAUDE.md

## Success Criteria

✅ GHDL compilation passes
✅ CocoTB tests run
✅ P1 output <20 lines
✅ All tests PASS
```

**Why this is better:**
- ✅ Clear context (2 major changes explained)
- ✅ Specific goal with expected outcome
- ✅ Actionable next steps (command to run)
- ✅ Anticipated issues listed
- ✅ Resources provided
- ✅ Measurable success criteria

---

## Using Handoffs

### Starting a New Session

1. **Read the latest handoff** (if continuing work)
   ```bash
   ls -t .claude/handoffs/ | head -1  # Get most recent
   cat .claude/handoffs/<latest>.md
   ```

2. **Load referenced resources**
   - Agent definitions
   - Documentation
   - External files

3. **Follow execution plan**
   - Run suggested commands
   - Check for listed issues
   - Verify success criteria

### Creating a Handoff

1. **At natural breakpoint** (end of task, stuck, need agent)

2. **Use template above** or copy existing handoff as starting point

3. **Be specific**
   - Exact commands run
   - Actual file paths
   - Concrete next steps

4. **Include recovery info**
   - How to undo changes if needed
   - Location of backups/references
   - Alternative approaches

5. **Git commit** (handoffs are documentation!)
   ```bash
   git add .claude/handoffs/
   git commit -m "docs: Add session handoff for <task>"
   ```

### Updating a Handoff

If session continues:
1. Keep original handoff
2. Create new handoff with updated status
3. Link back to previous: "Previous handoff: 2025-11-06_1740_..."

This creates a chain of work history.

---

## Handoff Best Practices

### DO:
- ✅ Write for "future you" or a teammate who knows nothing
- ✅ Include exact commands and paths
- ✅ List files modified (complete list in "Related Files")
- ✅ Explain WHY decisions were made
- ✅ Provide external references (repos, docs, files)
- ✅ State assumptions explicitly
- ✅ Include recovery/rollback instructions

### DON'T:
- ❌ Assume context ("the tests" - which tests?)
- ❌ Skip file paths ("updated the config" - which config?)
- ❌ Omit rationale ("changed naming" - why?)
- ❌ Leave TODOs vague ("fix errors" - which errors?)
- ❌ Forget external dependencies (reference files, repos)

---

## Handoff Workflow Examples

### Example 1: Agent Delegation

**Scenario:** Hit interactive tool limitation, need autonomous agent

```markdown
## Handoff Reason

Previous session hit Bash approval limitation when trying to run tests.
Agent needs full autonomy to run/fix/iterate.

## For Agent

You have full context above. Your task:
1. Run: cd bpd-tiny-vhdl/tests && python run.py bpd_fsm_observer
2. Fix any VHDL/import/path errors
3. Iterate until tests pass
4. Report final results

You can use Bash tool freely in your autonomous session.
```

### Example 2: Stuck on Decision

```markdown
## Decision Needed (Blocking)

**Question:** Keep stub VHDL files or delete them?

**Option A:** Delete stubs, use libs/forge-vhdl everywhere
- Pro: Single source of truth
- Con: More changes needed

**Option B:** Keep stubs for BPD tests
- Pro: Less churn, faster
- Con: Potential divergence

**Recommendation:** Try Option B first (pragmatic)

**Action:** Human/agent decides and updates this handoff
```

### Example 3: End-of-Day Checkpoint

```markdown
## Session Summary

**Completed:**
- ✅ Inlined 4 git submodules
- ✅ Migrated VHDL packages
- ✅ Updated documentation

**In Progress:**
- 🔄 Test cleanup (75% done)
- 🔄 FSM observer tests (not yet running)

**Next Session:**
- Get tests passing
- Delete stub files
- Update BPD to use forge-vhdl packages

**Estimated time:** 1-2 hours
```

---

## Version Control Integration

### Commit Handoffs

```bash
git add .claude/handoffs/<new-handoff>.md
git commit -m "docs: Add handoff for <task>"
```

**Why commit handoffs:**
- ✅ History of work progression
- ✅ Teammates can see context
- ✅ Examples for future similar tasks
- ✅ Documentation of decisions made

### Handoff + Code Changes

Option 1: **Separate commits** (recommended)
```bash
# Commit code changes
git add <files>
git commit -m "refactor: Migrate VHDL packages to forge-vhdl"

# Commit handoff
git add .claude/handoffs/<handoff>.md
git commit -m "docs: Add handoff for FSM observer test fix"
```

Option 2: **Combined commit** (if handoff is integral)
```bash
git add <files> .claude/handoffs/<handoff>.md
git commit -m "refactor: Migrate VHDL packages

See .claude/handoffs/2025-11-06_1740_... for continuation context"
```

---

## Archive Policy

**Keep handoffs indefinitely** - They're documentation, not cruft.

**Why not archive:**
- Small file size (text only)
- Valuable historical record
- Learning examples
- Shows work progression

**Gitignore exceptions:**
- Never ignore `.claude/handoffs/`
- These are documentation, not temp files

---

## Related Documentation

- **Agent definitions:** `.claude/agents/*/agent.md`
- **Shared docs:** `.claude/shared/`
- **Monorepo architecture:** `CLAUDE.md` (root)

---

## Questions?

**This system is new (2025-11-06)** - Iterate and improve!

If you find a better structure, update this README and existing handoffs.

---

**Created:** 2025-11-06
**Last Updated:** 2025-11-06
**Maintained By:** Development Team
