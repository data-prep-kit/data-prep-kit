# Release Management

## Overview 

Releases are created from the main repository branch for major releases only. A release can be created for each of the three components: data-connector-lib, data-processing-lib and transforms library or for all three simultaneously.

### Step 0: Create a PR for a `x.x.x.dev1` branch for regression testing
```
git checkout dev
git pull
git checkout -b x.x.x.dev1    ## Replace x.x.x with the proper release tag
```
From the main folder, edit the [`.make.versions`](.make.versions) and make the suffix dev1 for all the components

```
make set-versions
```

> **Note:** The root `make set-versions` does not recurse into `data-connector-lib` (the connector is versioned independently and is not always part of a release). If the connector IS being released, propagate its version separately with `make -C data-connector-lib set-versions` and confirm `data-connector-lib/pyproject.toml` updated.

```
git add .
git commit -s -m "adding dev1 release for regression testing"
git push --set-upstream origin x.x.x.dev1
```

Create a PR against the dev branch, review, approve and merge PR.

Once merged, build a wheel for `data-processing-lib` and `transforms` and upload to pypi. These targets live in the component Makefiles, so run them from each component folder:
```
make -C data-processing-lib build-pkg-dist publish-dist
make -C transforms build-pkg-dist publish-dist
```

After testing notebooks and confirming success - proceed to Step 1 for release

### Step 1: Create a PR for a `pending-release/x.x.x` branch
```
git checkout dev
git pull
git checkout -b pending-release/x.x.x     ## Replace x.x.x with the proper release tag
```
From the main folder, edit the [`.make.versions`](.make.versions) and remove the suffix (e.g., dev0, dev1, ... ) for all the components being released.

```
make set-versions
```

> **Note:** If `data-connector-lib` is among the components being released, also run `make -C data-connector-lib set-versions` — the root recursion skips it by design.

Edit the release notes [`release-notes.md`](release-notes.md) and add bullet list of major enhancements and bug fixes included in this release.

```
git add .
git commit -s -m "preparing for a new release"
git push --set-upstream origin pending-release/x.x.x
```

Create a PR against the dev branch, review, approve and merge PR.

Once merged, build a wheel for `data-processing-lib` and `transforms` and upload to pypi. These targets live in the component Makefiles, so run them from each component folder:
```
make -C data-processing-lib build-pkg-dist publish-dist
make -C transforms build-pkg-dist publish-dist
```


### Step 2: Create the release

1. Using the browser, create a new branch called `releases/vx.x.x`.

1. Using the browser, create a new release and associated release tag `vx.x.x` for `releases/vx.x.x`.


### Step 3: Setup dev for new work

```
git checkout dev
git pull
git checkout -b post-todays_date     

```
From the main folder, edit the `.make.versions`, increment minor or major and add the .dev0 suffix for all the released components.

```
make set-versions
```

> **Note:** If `data-connector-lib` was part of the release, also run `make -C data-connector-lib set-versions` — the root recursion skips it by design.

```
git add .
git commit -s -m "preparing for a new release"
git push --set-upstream origin post-todays_date
```

Create a PR, review, approve and merge PR.
