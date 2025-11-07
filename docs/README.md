# Monorepo Documentation Index

**Quick reference for finding documentation and workflows across the monorepo.**

---

## 📂 Documentation Structure

### Project Documentation (`docs/`)

**Documentation index and GitHub template setup instructions.**

---

## 🔧 Workflows & Templates (`.claude/workflows/`)

**Reusable procedures for common maintenance tasks:**

### Documentation Refactoring

**`submodule-doc-refactor-quick.md`** ⚡ (Recommended)
- Copy-paste prompt for refactoring any submodule's docs
- Optimizes for 3-tier architecture (llms.txt → CLAUDE.md → specialized)
- ~100 lines, quick assessment → proposal → execution

**`submodule-doc-refactor-detailed.md`** 📚 (Comprehensive)
- Detailed template with structured phases
- Use for complex submodules
- ~200 lines, full guidance

**When to use:**
- Working inside a submodule that needs doc cleanup
- Want to align with monorepo 3-tier architecture
- Need to reduce token overhead for LLM work

**Example usage:**
```bash
cd libs/some-submodule
cat ../../.claude/workflows/submodule-doc-refactor-quick.md
# Copy-paste into Claude Code, let AI assess and propose
```

---

## 🏗️ Architecture Guidelines (`.claude/shared/`)

**Core principles and architectural patterns:**

- **`ARCHITECTURE_OVERVIEW.md`** - Hierarchical 3-tier documentation system
- **`CONTEXT_MANAGEMENT.md`** - Token efficiency strategies
- **`PROBE_WORKFLOW.md`** - Probe development workflow
- **`SESSION_HANDOFF.md`** - Context preservation between sessions

---

## 📍 Quick Links

**Need to refactor a submodule's docs?**
→ `.claude/workflows/submodule-doc-refactor-quick.md`

**Understanding the monorepo architecture?**
→ `.claude/shared/ARCHITECTURE_OVERVIEW.md`

**Setting up Claude Code workflows?**
→ `.claude/commands/` (slash commands) and `.claude/agents/` (specialized agents)

---

## 🎯 Documentation Philosophy

**Three-Tier System:**
1. **Tier 1** (llms.txt): Quick reference catalog (~500-1000 tokens)
2. **Tier 2** (CLAUDE.md): Authoritative self-contained guide (~3-5k tokens)
3. **Tier 3** (Specialized docs): Load only when needed (5-10k+ tokens)

**Design Principle:**
> "Default to silence. Escalate consciously. Preserve context religiously."

**Success Metrics:**
- 30-50% documentation reduction (typical)
- Self-contained submodules (no parent dependencies)
- Token-efficient context loading
- Zero redundancy

---

## 📝 Adding New Workflows

When you create a new reusable procedure:

1. Write it as a clear, copy-paste prompt
2. Save in `.claude/workflows/`
3. Use kebab-case naming: `my-workflow-name.md`
4. Update this index with a brief description
5. Commit with descriptive message

**Workflow naming convention:**
- `*-quick.md` - Concise version (recommended for most uses)
- `*-detailed.md` - Comprehensive version (complex cases)

---

**Last updated:** 2025-11-04
**Maintained by:** Moku Instrument Forge Team
