---
name: release
description: Guide and automate release management for data-prep-kit. Covers dev1 regression builds, pending-release branches, release creation, and post-release dev setup. Trigger on "release", "cut a release", "prepare release", "release management", "publish release".
user_invocable: true
---

# Data Prep Kit Release Management Skill

You are guiding the user through the **data-prep-kit** release process. This is a monorepo with three independently versioned packages:

| Package | Version var | Suffix var |
|---|---|---|
| data-processing-lib | `DPK_NEXT_RELEASE` | `DPK_VERSION_SUFFIX` |
| data-connector-lib | `DPK_CONNECTOR_NEXT_RELEASE` | `DPK_CONNECTOR_SUFFIX` |
| transforms | `TRANSFORM_NEXT_RELEASE` | `TRANSFORM_VERSION_SUFFIX` |

All versions live in `.make.versions` (single source of truth). After editing versions, `make set-versions` propagates them to all `pyproject.toml` files.

> **NOTE — connector is independent:** `data-connector-lib` is versioned on its own track (e.g. `0.2.x`) and is **not** always part of a release, so the root `make set-versions` deliberately does **not** recurse into it. When the connector IS being released alongside the other packages (as it is in some releases), you must propagate its version separately: `make -C data-connector-lib set-versions`. After running it, verify `data-connector-lib/pyproject.toml` matches `DPK_CONNECTOR_NEXT_RELEASE` + `DPK_CONNECTOR_SUFFIX`. If the connector is not part of this release, leave its version untouched.

## When invoked, present a menu

Ask the user which release step to perform:

1. **Step 0: Dev1 Regression Build** — Create a `x.x.x.dev1` branch for regression testing
2. **Step 1: Pending Release** — Create a `pending-release/x.x.x` branch with clean versions
3. **Step 2: Create Release** — Guide creation of the release branch and tag on GitHub
4. **Step 3: Post-Release Dev Setup** — Bump versions and restore `.dev0` suffix for new development
5. **Full Release Walkthrough** — Walk through all steps end-to-end
6. **Release Status Check** — Analyze current repo state and determine where we are in the release process

---

## Implementation details for each step

### Step 0: Dev1 Regression Build

**Purpose:** Create a dev1 pre-release wheel for regression testing before the final release.

1. Confirm the user is on the `dev` branch and it is up to date:
   ```
   git checkout dev
   git pull
   ```
2. Read `.make.versions` to determine the current `*_NEXT_RELEASE` values. Confirm the target version with the user (e.g., `1.1.8`).
3. Create the dev1 branch:
   ```
   git checkout -b x.x.x.dev1
   ```
4. Edit `.make.versions` — set all relevant suffixes to `.dev1`:
   - `DPK_VERSION_SUFFIX=.dev1`
   - `DPK_CONNECTOR_SUFFIX=.dev1`
   - `TRANSFORM_VERSION_SUFFIX=.dev1`
5. Run `make set-versions` to propagate version changes to all pyproject.toml files. **If the connector is part of this release**, also run `make -C data-connector-lib set-versions` (the root recursion skips it by design).
6. Verify versions propagated correctly by reading the pyproject.toml files for each package — including `data-connector-lib/pyproject.toml` if the connector is being released.
7. Stage, commit, and push:
   ```
   git add .
   git commit -s -m "adding dev1 release for regression testing"
   git push --set-upstream origin x.x.x.dev1
   ```
8. Create a PR against the `dev` branch using `gh pr create`.
9. Inform the user of next steps:
   - Review and merge the PR
   - After merge, build and publish wheels for `data-processing-lib` and `transforms`. These targets live in the component Makefiles, not the repo root — run them from each component folder:
     ```
     make -C data-processing-lib build-pkg-dist publish-dist
     make -C transforms build-pkg-dist publish-dist
     ```
   - Test notebooks and confirm success before proceeding to Step 1

### Step 1: Pending Release

**Purpose:** Remove dev suffixes and prepare the final release version.

1. Confirm the user is on the `dev` branch and it is up to date:
   ```
   git checkout dev
   git pull
   ```
2. Read `.make.versions` to determine the current version numbers. Confirm the target release version with the user.
3. Create the pending-release branch:
   ```
   git checkout -b pending-release/x.x.x
   ```
4. Edit `.make.versions` — clear all suffixes for the components being released:
   - `DPK_VERSION_SUFFIX=`
   - `DPK_CONNECTOR_SUFFIX=`
   - `TRANSFORM_VERSION_SUFFIX=`
5. Run `make set-versions` to propagate. **If the connector is part of this release**, also run `make -C data-connector-lib set-versions` (the root recursion skips it by design).
6. Verify versions propagated correctly, including `data-connector-lib/pyproject.toml` if the connector is being released.
7. Check `release-notes.md` for an entry for this version. If missing, prompt the user to provide release notes. Help draft them by:
   - Running `git log` to find commits since the last release tag
   - Categorizing changes into Transforms, General, and other sections
   - Following the existing format in `release-notes.md` (numbered lists with descriptions)
8. Stage, commit, and push:
   ```
   git add .
   git commit -s -m "preparing for a new release"
   git push --set-upstream origin pending-release/x.x.x
   ```
9. Create a PR against the `dev` branch using `gh pr create`.
10. Inform the user of next steps:
    - Review and merge the PR
    - After merge, build and publish wheels for `data-processing-lib` and `transforms`. These targets live in the component Makefiles, not the repo root — run them from each component folder:
      ```
      make -C data-processing-lib build-pkg-dist publish-dist
      make -C transforms build-pkg-dist publish-dist
      ```
    - Proceed to Step 2 to create the actual release

### Step 2: Create Release

**Purpose:** Create the release branch and tag on GitHub.

This step involves browser-based actions on GitHub. Guide the user through:

1. Verify the pending-release PR has been merged and wheels have been published.
2. Instruct the user to create a new branch `releases/vx.x.x` from `dev` on GitHub:
   - Go to the repository on GitHub
   - Click the branch dropdown
   - Type `releases/vx.x.x` and create from `dev`
3. Instruct the user to create a new release on GitHub:
   - Go to Releases > "Draft a new release"
   - Create a new tag `vx.x.x` targeting the `releases/vx.x.x` branch
   - Title: `vx.x.x`
   - Copy release notes from `release-notes.md` into the release description
   - Publish the release
4. Alternatively, if `gh` CLI is available, offer to automate:
   ```
   gh api repos/{owner}/{repo}/git/refs -f ref="refs/heads/releases/vx.x.x" -f sha="$(git rev-parse dev)"
   gh release create vx.x.x --target releases/vx.x.x --title "vx.x.x" --notes-file release-notes-excerpt.md
   ```
5. Confirm the release was created successfully.

### Step 3: Post-Release Dev Setup

**Purpose:** Bump version numbers and restore dev suffix for ongoing development.

1. Confirm the user is on the `dev` branch and it is up to date:
   ```
   git checkout dev
   git pull
   ```
2. Read `.make.versions` to get current version numbers.
3. Ask the user which version component to bump (minor or patch) for each package, or suggest the default (patch bump).
4. Create the post-release branch using today's date:
   ```
   git checkout -b post-YYYY-MM-DD
   ```
5. Edit `.make.versions`:
   - Increment the appropriate version component for each `*_NEXT_RELEASE`
   - Set all suffixes to `.dev0`:
     - `DPK_VERSION_SUFFIX=.dev0`
     - `DPK_CONNECTOR_SUFFIX=.dev0`
     - `TRANSFORM_VERSION_SUFFIX=.dev0`
6. Run `make set-versions` to propagate. **If the connector was part of the release**, also run `make -C data-connector-lib set-versions` (the root recursion skips it by design).
7. Verify versions propagated correctly, including `data-connector-lib/pyproject.toml` if the connector was released.
8. Stage, commit, and push:
   ```
   git add .
   git commit -s -m "preparing for a new release"
   git push --set-upstream origin post-YYYY-MM-DD
   ```
9. Create a PR against the `dev` branch using `gh pr create`.

### Full Release Walkthrough

Walk through Steps 0-3 sequentially, pausing after each step for user confirmation before proceeding. Track progress and report status at each transition.

### Release Status Check

Analyze the current state of the repository to determine where in the release process we are:

1. Read `.make.versions` and report current versions and suffixes.
2. Check the current branch name for clues (`dev`, `x.x.x.dev1`, `pending-release/*`, `post-*`).
3. Check for recent release tags: `git tag --sort=-creatordate | head -5`
4. Check for open PRs related to releases: `gh pr list --search "pending-release OR dev1 OR post-"`
5. Check `release-notes.md` for the latest documented version.
6. Report:
   - Current version state (dev, dev1, release-ready, or post-release)
   - What the next step should be
   - Any issues found (e.g., mismatched suffixes, missing release notes)

---

## Safety guardrails

- **Always confirm with the user** before making any edits to `.make.versions` or `release-notes.md`.
- **Always show a diff preview** of version changes before committing.
- **Never run `publish-dist`** automatically — only instruct the user to do it (from the component folders) after PR merge.
- **Never force-push** or modify release branches/tags.
- **Verify branch state** (clean working tree, correct base branch) before creating new branches.
- When creating commits, always use the `-s` flag (signed-off-by) as required by the project.

## Output format

For each step, produce:
- A clear header indicating the current step
- Pre-flight checks (branch state, version state)
- Actions taken with their results
- Next steps the user needs to complete manually
- A status summary (e.g., "Step 1 complete — pending-release/1.1.8 branch created and PR opened")
