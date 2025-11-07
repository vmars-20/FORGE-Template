# Reusable Workflows

**Copy-paste prompts for common maintenance tasks.**

---

## Available Workflows

### Submodule Documentation Refactoring

**`submodule-doc-refactor-quick.md`** ⚡
- Quick copy-paste prompt (~100 lines)
- Use when: Working inside ANY submodule, want to optimize docs
- AI will: Assess → Propose → Ask for approval → Execute

**`submodule-doc-refactor-detailed.md`** 📚
- Comprehensive template (~200 lines)
- Use when: Complex submodule, need structured approach
- AI will: Detailed phase breakdown with metrics

**Example usage:**
```bash
cd libs/my-submodule
cat ../../.claude/workflows/submodule-doc-refactor-quick.md
# Copy-paste into Claude Code
# AI analyzes and proposes optimization
```

**Results:** 30-50% doc reduction, 3-tier structure alignment

---

## How to Use Workflows

1. **Navigate** to appropriate context (e.g., cd into submodule)
2. **Read** the workflow file
3. **Copy-paste** the prompt into Claude Code
4. **Review** AI's proposal
5. **Approve** or iterate
6. **Execute** the plan

---

## Adding New Workflows

**When to create a workflow:**
- You're doing something repeatedly across multiple areas
- It follows a structured process
- It's copy-paste friendly
- Other people (or future you) will benefit

**How to create:**
1. Write as clear, self-contained prompt
2. Include context, task, constraints, success criteria
3. Use kebab-case naming: `my-new-workflow.md`
4. Add to this README
5. Reference in `docs/README.md`

**Naming convention:**
- `*-quick.md` - Concise version (recommended)
- `*-detailed.md` - Comprehensive version (optional)

---

## Philosophy

**Workflows are:**
- ✅ Repeatable procedures
- ✅ Copy-paste prompts
- ✅ Context-aware
- ✅ Self-contained

**Workflows are NOT:**
- ❌ One-off scripts
- ❌ Code templates
- ❌ Architectural principles (those go in `.claude/shared/`)

---

**See also:**
- `docs/README.md` - Full documentation index
- `.claude/shared/` - Architectural principles
- `.claude/commands/` - Slash commands
