# Sync Submodules

Update all git submodules (forge, libs/*) to latest commits.

**Agent:** General-purpose

---

## What It Does

Synchronizes all git submodules in the monorepo:
- `forge/` - Main instrument forge submodule
- `forge/libs/basic-app-datatypes/` - Type system library (nested)
- `forge/libs/moku-models/` - Platform specifications (nested)
- `forge/libs/riscure-models/` - Probe hardware specs (nested)

## When to Use

- After pulling monorepo changes
- Before starting probe development (ensure latest libs)
- When forge/ or libs/ appear out of sync
- After upstream changes to submodules

## Commands Executed

```bash
# Update all submodules recursively
git submodule update --init --recursive --remote

# Show updated submodule commits
git submodule status
```

## Expected Output

```
Submodule 'forge' (https://github.com/sealablab/moku-instrument-forge) registered for path 'forge'
Submodule 'forge/libs/basic-app-datatypes' (https://github.com/sealablab/basic-app-datatypes) registered for path 'forge/libs/basic-app-datatypes'
Submodule 'forge/libs/moku-models' (https://github.com/sealablab/moku-models) registered for path 'forge/libs/moku-models'
Submodule 'forge/libs/riscure-models' (https://github.com/sealablab/riscure-models) registered for path 'forge/libs/riscure-models'

Cloning into 'forge'...
...

Submodule path 'forge': checked out 'd212c2f...'
Submodule path 'forge/libs/basic-app-datatypes': checked out '15d9fab...'
Submodule path 'forge/libs/moku-models': checked out 'a4267b0...'
Submodule path 'forge/libs/riscure-models': checked out '600375b...'
```

## Notes

- This command updates to latest commits on tracked branches
- Changes may require monorepo commit to update submodule pointers
- Use before asking type/platform questions to ensure latest docs

## Troubleshooting

**Issue:** Submodule has local changes
```
error: Your local changes to the following files would be overwritten by checkout
```

**Fix:**
```bash
cd forge/libs/basic-app-datatypes
git stash
cd ../../..
/sync-submodules
```

**Issue:** Nested submodule not initialized
```
Submodule path 'forge/libs/basic-app-datatypes': not initialized
```

**Fix:**
```bash
git submodule update --init --recursive
```
