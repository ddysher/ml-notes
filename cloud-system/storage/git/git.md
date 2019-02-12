<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Concepts](#concepts)
  - [Visualization](#visualization)
  - [.git directory](#git-directory)
- [Experiments](#experiments)
  - [Object](#object)
  - [HEAD](#head)
  - [Index](#index)
  - [Packfile](#packfile)
  - [Data Transfer](#data-transfer)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Concepts

Following is a digest of core concepts in Git:
- repository: a collection of commits, working tree, branch, tag, etc
- index: changes are first registered in the index; it is useful to be seen as the "staging area"
- working tree: a directory structure with a repository associated with it
- commit: a snapshot of working tree at some point in time
- branch: name alias for commit, branch change each time a new commit is checked in to that branch
- tag: name alias for commit, unlike branch which can change, tag is fixed to a commit and has its own description
- master: mainline branch of development in most repositories, but by no means a special branch
- HEAD: reference to current working commit, which also can be a branch reference

Other internal concepts:
- blob: represent file content (no metadata)
- tree: mirrors filesystem structure, each tree points to other trees and blobs
- commit: internal representation of a user-facing commit, each commit contains a tree
- object: a generic concept, includes blob, tree, commit and tag. All Git objects are stored the same
  way, just with different types – instead of the string blob, the header will begin with commit or
  tree. Also, although the blob content can be nearly anything, the commit and tree content are very
  specifically formatted. Both `blob`, `tree` and `commit` are compressed and saved under `.git/objects`.

More about commit:

> Another joy of the commit-based system is that you can rephrase even the most complicated version
> control terminology using a single vocabulary. For example, if a commit has multiple parents, it’s
> a "merge commit" — since it merged multiple commits into one. Or, if a commit has multiple children,
> it represents the ancestor of a "branch", etc. But really there is no difference between these
> things to Git: to it, the world is simply a collection of commit objects, each of which holds a
> tree that references other trees and blobs, which store your data. Anything more complicated than
> this is simply a device of nomenclature.

*References*
- https://jwiegley.github.io/git-from-the-bottom-up/
- https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain

## Visualization

<p align="center"><img src="./assets/commits.png" height="360px" width="auto"></p>
<p align="center"><img src="./assets/data-model-3.png" height="360px" width="auto"></p>

## .git directory

```
$ ls -F1
config
description
HEAD
hooks/
index
info/
objects/
refs/
```

The core files/directories are: HEAD, refs, index, objects.

# Experiments

## Object

Git uses sha1 as key to store blob. Note the sha1 value is not just file content, Git also adds some
padding:

```console
$ mkdir sample; cd sample
$ echo 'Hello, world!' > greeting

$ git hash-object greeting
af5626b4a114abcb82d63db7c8082c3c4756e51b

# This is different from git hash.
$ sha1sum greeting
09fac8dbfd27bd9b4d23a00eb648aa751789536d  greeting

$ echo 'blob 14\0Hello, world!' | sha1sum
af5626b4a114abcb82d63db7c8082c3c4756e51b  -
```

Now we initialize the repository, `.git` is empty:

```console
$ git init
Initialized empty Git repository in /tmp/sample/.git/

$ tree .git
.git
├── branches
├── config
├── description
├── HEAD
├── hooks
│   ├── applypatch-msg.sample
│   ├── commit-msg.sample
│   ├── fsmonitor-watchman.sample
│   ├── post-update.sample
│   ├── pre-applypatch.sample
│   ├── pre-commit.sample
│   ├── prepare-commit-msg.sample
│   ├── pre-push.sample
│   ├── pre-rebase.sample
│   ├── pre-receive.sample
│   └── update.sample
├── info
│   └── exclude
├── objects
│   ├── info
│   └── pack
└── refs
    ├── heads
    └── tags

9 directories, 15 files
```

After `git add`, we'll see the file blob saved under `objects`. Git will compress the file so
directly looking at the file is not useful, we can check the data with `git cat-file`:

```
$ git add greeting

$ tree .git
.git
├── branches
├── config
├── description
├── HEAD
├── hooks
│   ├── applypatch-msg.sample
│   ├── commit-msg.sample
│   ├── fsmonitor-watchman.sample
│   ├── post-update.sample
│   ├── pre-applypatch.sample
│   ├── pre-commit.sample
│   ├── prepare-commit-msg.sample
│   ├── pre-push.sample
│   ├── pre-rebase.sample
│   ├── pre-receive.sample
│   └── update.sample
├── index
├── info
│   └── exclude
├── objects
│   ├── af
│   │   └── 5626b4a114abcb82d63db7c8082c3c4756e51b
│   ├── info
│   └── pack
└── refs
    ├── heads
    └── tags

10 directories, 17 files

$ cat .git/objects/af/5626b4a114abcb82d63db7c8082c3c4756e51b
<---binary data--->

$ git cat-file blob af56
Hello, world!
```

Now let's create our commit. There are a few things to note:
- a new commit is created under `objects/fb/c992571f1ab4a5a68625f65fb87a9148712c75`
  - we can view the content of the commit via `git cat-file commit fbc9925`
- a new tree is created under `objects/05/63f77d884e4f79ce95117e2d686d7d6e282887`
  - we can view the content of the tree via `git cat-file tree 0563f77` or `git ls-tree 0563f77`
  - or use `git cat-file -p commitid^{tree}` to print tree object of a commit
- the file content stays in `objects/af/5626b4a114abcb82d63db7c8082c3c4756e51b`
  - we can view the content of the file via `git cat-file file af5626b`, as mentioned above
- a new reference `refs/heads/master` is created with a single value `fbc992571f1ab4a5a68625f65fb87a9148712c75`
  - which means master branch points to our new commit

To summarize, all blobs are saved under `objects` directory with three different types: blob, tree
and commit (another one is tag). The repository contains a single commit, which references a tree
that holds a blob — the blob containing the contents I want to record.

It's also useful to use `git show [objectID]` to view the content.

```console
$ git commit -m "Added my greeting"
[master (root-commit) fbc9925] Added my greeting
 1 file changed, 1 insertion(+)
 create mode 100644 greeting

$ tree .git
.git
├── branches
├── COMMIT_EDITMSG
├── config
├── description
├── HEAD
├── hooks
│   ├── applypatch-msg.sample
│   ├── commit-msg.sample
│   ├── fsmonitor-watchman.sample
│   ├── post-update.sample
│   ├── pre-applypatch.sample
│   ├── pre-commit.sample
│   ├── prepare-commit-msg.sample
│   ├── pre-push.sample
│   ├── pre-rebase.sample
│   ├── pre-receive.sample
│   └── update.sample
├── index
├── info
│   └── exclude
├── logs
│   ├── HEAD
│   └── refs
│       └── heads
│           └── master
├── objects
│   ├── 05
│   │   └── 63f77d884e4f79ce95117e2d686d7d6e282887
│   ├── af
│   │   └── 5626b4a114abcb82d63db7c8082c3c4756e51b
│   ├── fb
│   │   └── c992571f1ab4a5a68625f65fb87a9148712c75
│   ├── info
│   └── pack
└── refs
    ├── heads
    │   └── master
    └── tags

15 directories, 23 files
```

## HEAD

At mentioned above, `HEAD` points to a working commit, which usually is tip of a branch, but can be
any commit in history (called `detached HEAD`). Here, it points to `master`:

```console
$ cat .git/HEAD
ref: refs/heads/master

$ git rev-parse HEAD
fbc992571f1ab4a5a68625f65fb87a9148712c75

$ git cat-file -t HEAD
commit

$ git cat-file commit HEAD
tree 0563f77d884e4f79ce95117e2d686d7d6e282887
author Deyuan Deng <deyuan@caicloud.io> 1539924721 +0800
committer Deyuan Deng <deyuan@caicloud.io> 1539924721 +0800

Added my greeting
```

## Index

The index is really just a staging area for next commit, and there’s a good reason why it exists:
it supports a model of development: the ability to build up your next commit in stages.

We'll start from scratch:

```console
$ mkdir sample; cd sample
$ echo 'Hello, world!' > greeting

$ git init
$ git add greeting
```

There is no commit but we can view our blob from index (--stage). Under the hood, `git ls-files --stage`
command prints out content of `.git/index` file.

```console
$ git log
fatal: your current branch 'master' does not have any commits yet

$ git ls-files --stage
100644 af5626b4a114abcb82d63db7c8082c3c4756e51b 0       greeting

$ ls .git/objects/af/5626b4a114abcb82d63db7c8082c3c4756e51b
.git/objects/af/5626b4a114abcb82d63db7c8082c3c4756e51b
```

The blob file is saved under `.git/objects` even if it's not committed, but if a change is
unregistered from the index with reset, it will become an orphaned blob that will get deleted at
some point at the future.

We can use `git commit` to commit the changes, but it's also possible to use the *plumbing* commands
to manually create commit, update references:
- git write-tree: record the contents of the index in a tree blob
- git commit-tree [treeID]: takes a tree hash id and creates a commit
- git update-ref refs/heads/master [commitID]: taks a commit id and set to tip of master branch
- git symbolic-ref HEAD refs/heads/master: linke HEAD to master

*Reference*
- https://mincong-h.github.io/2018/04/28/git-index/

## Packfile

Git will pack multiple objects (including blob, commit, tree, etc) into packfile to save space and
make Git more efficient. Packing (or compressing) happens by automatically calling into `git gc`, or
implicitly using `git push`, etc.

Below, we manually run `git gc` to pack our repository:

```console
$ echo 'Hello, world!' > greeting
$ git init
Initialized empty Git repository in /tmp/sample/.git/
$ git add .
$ git commit -m "Added my greeting"
[master (root-commit) 927ead0] Added my greeting
 1 file changed, 1 insertion(+)
 create mode 100644 greeting

$ echo 'Hello, world, again!' > greeting-again
$ git add .
$ git commit -m "Added my greeting again"
[master 797fc5c] Added my greeting again
 1 file changed, 1 insertion(+)
 create mode 100644 greeting-again

$ tree .git/objects
.git/objects
├── 05
│   └── 63f77d884e4f79ce95117e2d686d7d6e282887
├── 29
│   └── 96b2170926caaf45bebc3a159af8ef198fd2de
├── 6e
│   └── 996b1d518d3829d1144ba2e8d5c90bcadd23c6
├── 79
│   └── 7fc5cac1d96e156809d2dab0d811e364fd2794
├── 92
│   └── 7ead066a293c1e6f7c010ac13bd133ea97fad1
├── af
│   └── 5626b4a114abcb82d63db7c8082c3c4756e51b
├── info
└── pack

8 directories, 6 files

$ git gc
Enumerating objects: 6, done.
Counting objects: 100% (6/6), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (6/6), done.
Total 6 (delta 0), reused 0 (delta 0)

$ tree .git/objects
.git/objects
├── info
│   └── packs
└── pack
    ├── pack-d1ebd51962d221a9178b0c6bfb12b08931b6f84f.idx
    └── pack-d1ebd51962d221a9178b0c6bfb12b08931b6f84f.pack

2 directories, 3 files
```

For more details on packfile structure, ref: https://git-scm.com/book/en/v2/Git-Internals-Packfiles

## Data Transfer

TODO
