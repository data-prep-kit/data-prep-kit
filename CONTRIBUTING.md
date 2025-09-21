## Contributing In General

Our project welcomes external contributions. If you have an itch, please feel free to scratch it.

### Signing prerequisites 

We have a requirement that all signed commits must have a github "verified" signature, before a corresponding Pull Request (PR) can be merged. 

Follow the instructions [here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) for creating and adding a new SSH key to your github profile settings. Please make sure to select a "sigining" key and not the default "authentication" key. Then you need to tell github about your new SSH key by using the commands: 

```
git config --global gpg.format ssh

git config --global user.signingkey /PATH/TO/.SSH/KEY.PUB
```
where you substitue /PATH/TO/.SSH/KEY.PUB with the path to your new public SSH key. 

To verify that you have done the above steps correctly, please use the command:

```
git config --global --edit 
```
and confirm that in your editor, you see the following important sections:

```
# This is user's git configuration file.
[user]
        email = your email address
        name = your first and last name
        signingkey = /PATH TO KEY/KEY.PUB
[commit]
        gpgsign = true
[gpg]
        format = ssh
```

You will now include the flag `-s | --sign-off` when you commit a change to your local git repository, for example

```
git commit -s -m "your commit message"
```


### Creating issues

To contribute code or documentation, please create an [issue](https://github.com/data-prep-kit/data-prep-kit/issues) to engage with the maintainers and the open source community on the proposed enhancements, describe what problem it solves, and the use cases it covers. Alternatively, you can scan the existing issues and engage with the authors/commentators. Once the issue is assigned, the assignee is encouraged to submit a [PR](https://github.com/data-prep-kit/data-prep-kit/pulls).  
Before embarking on a more ambitious contribution, please quickly get in touch with [us](MAINTAINERS.md).

#### Proposing new features

When proposing a new feature, please select the **Feature request** template in creating a new issue and fill all the sections of the template, including the choice of what component of DPK (e.g., documentation, transforms, pipelines, or other) it is related to and most importantly, a succinct description of the new feature, before submitting. 

#### Fixing bugs

If you discover a bug or would like to fix a bug, please raise an issue, before sending a
pull request so it can be tracked. Select the **Bug Report** template in creating a new issue and fill all the mandatory sections of the template, including **What happend ...** , **Reproduction script**, **OS** , and **Python version**. 

### PR review

If you decide to submit a PR that addresses a new feature and/or a bug, for which a corresponding issue has already been submitted, work on your forked version of the repo and after additions/modifications of code in your fork, submit a PR, mentioning what issue it addresses and other optional information that facilitates the review process. At this point, the maintainers of the repo will assign one or more reviwers to your PR. 


### Merge approval

The PR reviewers use LGTM (Looks Good To Me) in comments on the code
review to indicate acceptance, or ask for changes to the specific sections of the code. A PR requires an approval from at least one reviewer, before it is merged by the maintainer. 

For a list of the maintainers, see the [MAINTAINERS.md](MAINTAINERS.md) page.

### Legal 

Each source file must include a license header for the Apache
Software License 2.0. Using the SPDX format is the simplest approach.
e.g.,

```
/*
Copyright <holder> All Rights Reserved.

SPDX-License-Identifier: Apache-2.0
*/
```

We have tried to make it as easy as possible to make contributions. This
applies to how we handle the legal aspects of contribution. We use the
same approach - [Developer's Certificate of Origin 1.1 (DCO)](https://github.com/hyperledger/fabric/blob/master/docs/source/DCO1.1.txt) - that the Linux® Kernel [community](https://elinux.org/Developer_Certificate_Of_Origin)
uses to manage code contributions.

When submitting a PR that has been signed-off (please see above for the signing requirement), the developer accepts the DCO. 

## Transform Setup and Testing

Please note the many useful options of the make command, as shown by using `make help`, that will take care of manual steps that would have been needed for tasks such as building, publishing, setting up or testing transforms in most directories.

## Coding style guidelines

Coding style as enforced by `pre-commit`.
