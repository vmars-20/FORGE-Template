# GitHub Template Repository Setup

**How to enable this repository as a GitHub template**

---

## What is a GitHub Template?

A template repository allows users to create new repositories with the same directory structure, files, and git submodule configuration as your template - but with a fresh git history.

**Benefits:**
- "Use this template" button appears on your repository
- Users get clean slate (no template's git history)
- Submodules are configured automatically
- Easier than forking for starting new projects

---

## Step-by-Step Setup

### 1. Enable Template Repository Feature

**On GitHub:**

1. Go to your repository: `https://github.com/yourusername/moku-instrument-forge-mono-repo`
2. Click **Settings** (top right)
3. Scroll down to **"Template repository"** section
4. Check the box: ☑️ **"Template repository"**
5. Save

**Result:** A **"Use this template"** button will appear on your repository's main page.

---

### 2. Test the Template

**Create a test repository to verify:**

1. On your template repo, click **"Use this template"**
2. Name it: `test-template-clone`
3. Choose visibility (public/private)
4. Click **"Create repository"**
5. Clone the new repo:
   ```bash
   git clone --recurse-submodules https://github.com/yourusername/test-template-clone.git
   cd test-template-clone
   ```

**Verify:**
- [ ] All submodules are present (`git submodule status`)
- [ ] Documentation files are intact
- [ ] `.gitmodules` is correct
- [ ] Git history is fresh (not from template)

**If successful:**
- Delete the test repository
- Your template is ready!

---

### 3. Add Template Badge (Optional)

Add a badge to your README.md to advertise template status:

```markdown
[![Template](https://img.shields.io/badge/template-ready-green)](https://github.com/yourusername/moku-instrument-forge-mono-repo)
```

---

### 4. Create Template Documentation

Ensure these files exist and are up-to-date:

- [x] **CLAUDE.md** - Complete architecture guide
- [x] **TEMPLATE.md** - Step-by-step customization instructions
- [x] **README.md** - Includes "Using This Template" section
- [x] **.claude/manifest.json** - Programmatic structure definition
- [x] **.claude/commands/customize-monorepo.md** - AI-assisted customization

---

## What Users Will See

When someone clicks **"Use this template"**:

1. They see a **"Create a new repository"** form
2. They choose repository name and visibility
3. GitHub creates new repo with:
   - All your files and directory structure
   - Configured git submodules (`.gitmodules`)
   - **Fresh git history** (no commits from your template)

When they clone:
```bash
git clone --recurse-submodules <their-new-repo-url>
```

They get:
- All submodules initialized
- Ready-to-customize structure
- No connection to your template (not a fork)

---

## Template Best Practices

### Do's ✅

- **Do** keep the template clean and well-documented
- **Do** use clear naming in submodules
- **Do** provide TEMPLATE.md with step-by-step customization
- **Do** include example content that's easy to replace
- **Do** test the template regularly
- **Do** add a license (MIT recommended)

### Don'ts ❌

- **Don't** include secrets or credentials
- **Don't** include `.env` files with real values
- **Don't** include large binary files (bloats every use)
- **Don't** include generated files (build artifacts)
- **Don't** leave TODOs or unfinished sections

---

## Maintaining the Template

### When to Update

Update the template when:
- You discover better patterns
- Documentation can be improved
- New features are added to submodules
- Users report issues

### How to Update

```bash
# Make changes in your template repo
git add .
git commit -m "docs: Improve template documentation"
git push

# Optionally tag releases
git tag -a v2.1.0 -m "Template v2.1.0 - Improved docs"
git push origin v2.1.0
```

**Note:** Existing repositories created from your template **won't automatically update**. Users must manually pull changes if they want them.

---

## Tracking Template Usage

### GitHub Insights

GitHub doesn't provide built-in analytics for template usage, but you can:

1. **Watch "Used by" count** (shows up on your repo after people use it)
2. **Search GitHub** for repos created from your template
3. **Ask users to star** your template if it helped them

### Optional: Add Telemetry

You could add optional telemetry to your template:

**.claude/template-metadata.json:**
```json
{
  "template_source": "moku-instrument-forge-mono-repo",
  "template_version": "2.0.0",
  "created_from_template": true
}
```

Users can keep or remove this file - it's just metadata.

---

## Supporting Template Users

### Documentation

Ensure users have:
- **README.md** - Quick overview and template usage
- **TEMPLATE.md** - Detailed customization guide
- **CLAUDE.md** - Complete architecture reference
- **Submodule docs** - Each submodule well-documented

### Community

Consider creating:
- **Discussions tab** on GitHub for Q&A
- **Issue templates** for bug reports and feature requests
- **Contributing guide** for improvements to template

### AI Assistance

The `/customize-monorepo` command helps users adapt the template interactively.

---

## Alternative: GitHub Discussions Template

For community-focused templates, enable **Discussions**:

1. Go to **Settings** → **Features**
2. Check ☑️ **Discussions**
3. Create discussion categories:
   - **Show and Tell** - Users share their customizations
   - **Q&A** - Template usage questions
   - **Ideas** - Suggestions for template improvements

---

## Troubleshooting

### "Template repository checkbox is grayed out"

**Cause:** Repository might have issues, or you lack admin permissions

**Fix:**
- Ensure you have admin access
- Check repository isn't private (templates work with private, but need proper permissions)
- Try refreshing the page

### "Submodules aren't initialized when users clone"

**Cause:** Users forgot `--recurse-submodules` flag

**Fix:** Emphasize in TEMPLATE.md and README.md:
```bash
# IMPORTANT: Use --recurse-submodules flag
git clone --recurse-submodules <repo-url>
```

### "Users report template is outdated"

**Cause:** Template hasn't been updated in a while

**Fix:**
- Regularly update template with best practices
- Tag versions (v2.0.0, v2.1.0, etc.)
- Announce updates in Discussions or README

---

## Template vs. Fork

### When Users Should Use Template

- Starting a **new project** from your structure
- Want **clean git history**
- No intention to contribute back to template
- Customizing heavily for different domain

### When Users Should Fork

- Want to **track upstream changes**
- Planning to **contribute back** improvements
- Similar use case, minor customizations
- Want to stay in sync with template updates

**Both are valid!** Mention both options in README.

---

## Checklist: Is Your Template Ready?

Before enabling template repository:

- [ ] All documentation is complete (README, CLAUDE.md, TEMPLATE.md)
- [ ] No secrets or credentials in files
- [ ] `.gitignore` is comprehensive
- [ ] Submodules are properly configured
- [ ] License file exists (MIT recommended)
- [ ] Clear "Using This Template" section in README
- [ ] Test: Create a test repo from template and verify it works
- [ ] `/customize-monorepo` command works
- [ ] All links in documentation are correct

---

## After Enabling

1. **Announce it!** Let your community know the template is available
2. **Write a blog post** explaining the architecture
3. **Share on social media** or relevant forums
4. **Monitor feedback** and improve based on usage

---

## Example Template Announcement

```markdown
## 🎉 Template Repository Now Available!

This repository is now a **GitHub Template**. You can use it to create
your own instrument development monorepo with clean, composable architecture.

**To use:**
1. Click "Use this template" button
2. Follow TEMPLATE.md for customization steps
3. Start building!

See CLAUDE.md for complete architecture documentation.

Questions? Open a Discussion or Issue!
```

---

## Resources

- [GitHub: Creating a template repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository)
- [GitHub: Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

---

**Last Updated:** 2025-11-04
**Template Version:** 2.0.0
