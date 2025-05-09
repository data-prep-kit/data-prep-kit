# Release Management

## Overview 

Releases are created from the main repository branch for major releases only. A release can be created for each of the three components: data-connector-lib, data-processing-lib and transforms library or for all three simultaneously.

### Step 1: Create a PR for a `pending-release/x.x.x` branch
```
git checkout dev
git pull
git checkout -b pending-release/x.x.x     ## Replace x.x.x with the proper release tag
```
From the main folder, edit the `.make.versions` and remove the suffix (e.g., dev0, dev1, ... ) for all the components being released.

```
make set-versions
```

Edit the release notes `releases-notes.md`.

```
git add .
git commit -s -m "preparing for a new release"
git push --set-upstream origin pending-release/x.x.x
```

Create a PR against the dev branch, review, approve and merge PR.


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
```
git add .
git commit -s -m "preparing for a new release"
git push --set-upstream origin post-todays_date
```

Create a PR, review, approve and merge PR.
