<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Data Version Control](#data-version-control)
  - [Initialization](#initialization)
  - [Add Remote Repository](#add-remote-repository)
  - [Add File to dvc](#add-file-to-dvc)
  - [Share Data](#share-data)
  - [Retrieve Data](#retrieve-data)
  - [Checkout](#checkout)
- [Pipeline Version Control](#pipeline-version-control)
  - [Transformation](#transformation)
  - [Pipeline](#pipeline)
  - [Metrics](#metrics)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

DVC is an open-source version control system for machine learning projects. It is built to make ML
models shareable and reproducible. It is designed to handle large files, data sets, machine learning
models, and metrics as well as code.

It features:
- version control data & model
- workflow for deployment & collaboration

At its core, dvc is a command line interface, like git, with extensive caching, operating system
specific hardlink management, custom file format, etc.

# Data Version Control

*Data: 10/16/2018, v0.19.12*

## Initialization

To initialize a DVC repository, run:

```console
$ dvc init
Adding '.dvc/state' to '.dvc/.gitignore'.
Adding '.dvc/lock' to '.dvc/.gitignore'.
Adding '.dvc/config.local' to '.dvc/.gitignore'.
Adding '.dvc/updater' to '.dvc/.gitignore'.
Adding '.dvc/cache' to '.dvc/.gitignore'.
Checking for updates...
You can now commit the changes to git.
```

After DVC initialization, a new directory `.dvc` will be created with `config`, `.gitignore` files
and `cache` directory. These files and directories are hidden from the user in general and the user
does not interact with these files directly.

`.dvc/cache` directory is one of the most important parts of any DVC repositories. The directory
contains all content of data files. The most important part about this directory is that `.dvc/.gitignore`
file is containing this directory which means that the cache directory is not under Git control -
this is your local directory and you cannot push it to any Git remote.

```console
$ tree . -a
.
├── .dvc
│   ├── cache
│   ├── config
│   └── .gitignore
└── .git
    ...

14 directories, 20 files

$ cat .dvc/.gitignore
state
lock
config.local
updater
cache
```

Ref: https://dvc.org/doc/commands-reference/init

## Add Remote Repository

The same way as Github serves as a master storage for Git-based projects, DVC data remotes provide
a central place to keep and share data and model files. With a remote data storage, you can pull
models and data files which were created by your team members without spending time and resources
to re-build models and re-process data files. It also saves space on your local environment - DVC
can fetch into the local cache only the data you need for a specific branch/commit.

Using DVC with a remote data storage is optional. By default, DVC is configured to use a local data
storage only (usually `.dvc/cache` directory inside your repository), which enables basic DVC
usage scenarios out of the box.

DVC supports a couple of backend, e.g. Amazon S3, HDFS, etc, each has a corresponding driver in cli.

```console
$ dvc remote add -d myremote /tmp/dvc-storage
Setting 'myremote' as a default remote

$ cat .dvc/config
['remote "myremote"']
url = /tmp/dvc-storage
[core]
remote = myremote
```


## Add File to dvc

When you add a file or a stage to your pipeline, DVC creates a special `.dvc` file that contains all
the needed information to track your data. The file itself is in a simple [YAML format](https://dvc.org/doc/user-guide/dvc-file-format)
and could be easily written or altered (after being created by dvc run or dvc add) by hand.

```console
$ wget https://dvc.org/s3/get-started/data.xml
...

$ ls -lh
total 37M
-rw-r--r-- 2 deyuan deyuan 37M Aug  9 08:47 data.xml
-rw-r--r-- 1 deyuan deyuan 115 Oct 16 15:16 data.xml.dvc

$ dvc add data.xml
Checking for updates...
Adding 'data.xml' to '.gitignore'.
Saving 'data.xml' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/a3/04afb96060aad90176268345e10355 -> data.xml
Saving information to 'data.xml.dvc'.

To track the changes with git run:

        git add .gitignore data.xml.dvc

$ ls
data.xml  data.xml.dvc
```

DVC updates `.gitignore` so that the original file `data.xml` is no not tracked by git; instead, a
new `data.xml.dvc` file is created to track the original file.

```console
$ cat .gitignore
data.xml

$ cat data.xml.dvc
md5: 301598c8348f8ac0c95abc6fc19da952
outs:
- cache: true
  md5: a304afb96060aad90176268345e10355
  path: data.xml

$ tree .dvc
.dvc
├── cache
│   └── a3
│       └── 04afb96060aad90176268345e10355
├── config
├── lock
├── state
└── updater

2 directories, 5 files

$ ls -lh .dvc/cache/a3/04afb96060aad90176268345e10355
-rw-r--r-- 2 deyuan deyuan 37M Aug  9 08:47 .dvc/cache/a3/04afb96060aad90176268345e10355
```

The data is cached under `.dvc/cache`, and DVC uses hard link to make it part of user-facing directory
tree (notice inode number is the same).

```console
$ ls -il
total 37036
102495704 -rw-r--r-- 2 deyuan deyuan 37916850 Aug  9 08:47 data.xml
102543262 -rw-r--r-- 1 deyuan deyuan      115 Oct 16 15:16 data.xml.dvc

$ ls -il .dvc/cache/a3/04afb96060aad90176268345e10355
102495704 -rw-r--r-- 2 deyuan deyuan 37916850 Aug  9 08:47 .dvc/cache/a3/04afb96060aad90176268345e10355
```

## Share Data

`dvc push` pushes all data file caches related to the current Git branch to the remote storage.

```console
$ dvc push
Preparing to push data to /tmp/dvc-storage
[##############################] 100% Collecting information
[##############################] 100% data.xml

$ tree /tmp/dvc-storage
/tmp/dvc-storage
└── a3
    └── 04afb96060aad90176268345e10355

1 directory, 1 file
```

## Retrieve Data

`dvc pull` pulls data files to the working space.

The set of data files to pull (usually it means downloading from the remote storage if file is not
in the local cache yet) is determined by **analyzing all `.dvc` files in the current branch**,
unless --all-branches is specified.

After data file is in cache DVC utilizes OS specific mechanisms like reflinks or hardlinks to put it
into the working space without copying.

```console
$ rm -f data.xml

$ dvc pull
Preparing to pull data from /tmp/dvc-storage
[##############################] 100% Collecting information
Checking out 'data.xml' with cache 'a304afb96060aad90176268345e10355'.
Created 'hardlink': .dvc/cache/a3/04afb96060aad90176268345e10355 -> data.xml
```

## Checkout

We start by adding one more data into our repository:

```console
$ wget https://imgur.com/HJCjylV.jpg
...

$ mv HJCjylV.jpg dog.jpg

$ ll
total 37M
-rw-r--r-- 2 deyuan deyuan  37M Aug  9 08:47 data.xml
-rw-r--r-- 1 deyuan deyuan  115 Oct 16 15:16 data.xml.dvc
-rw-r--r-- 1 deyuan deyuan 285K Oct 12 11:52 dog.jpg

$ dvc add dog.jpg
Adding 'dog.jpg' to '.gitignore'.
Saving 'dog.jpg' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/b2/480770f49077512d19c452474bb7e5 -> dog.jpg
Saving information to 'dog.jpg.dvc'.

To track the changes with git run:

        git add .gitignore dog.jpg.dvc

$ git add .gitignore dog.jpg.dvc

$ git commit -m "add dog jpg to DVC"
[master e8b6f0f] add dog jpg to DVC
 2 files changed, 7 insertions(+), 1 deletion(-)
 create mode 100644 dog.jpg.dvc

$ dvc push
Preparing to push data to /tmp/dvc-storage
[##############################] 100% Collecting information
[##############################] 100% dog.jpg

$ dvc pull
Preparing to pull data from /tmp/dvc-storage
[##############################] 100% Collecting information
Data 'dog.jpg' didn't change.
Data 'data.xml' didn't change.
```

Now we find our previous git commit and checkout to it:

```console
$ git log
commit e8b6f0fcfe907cb90e8dcc81b96e9d77f3a8f86f (HEAD -> master)
Author: Deyuan Deng <deyuan@caicloud.io>
Date:   Tue Oct 16 15:58:45 2018 +0800

    add dog jpg to DVC

commit 01da903e2004b79ff1e02911857f3c9a030294a0
Author: Deyuan Deng <deyuan@caicloud.io>
Date:   Tue Oct 16 15:25:13 2018 +0800

    add source data to DVC

commit dc7a4d10d0f6276679f14668f62c80463adc1fc0
Author: Deyuan Deng <deyuan@caicloud.io>
Date:   Tue Oct 16 15:09:50 2018 +0800

    initialize DVC local remote

commit a5bbb98213c8ada2a4c29796f6e69f72d26071e8
Author: Deyuan Deng <deyuan@caicloud.io>
Date:   Tue Oct 16 15:09:35 2018 +0800

    initialize DVC

$ gco 01da903e2004b79ff1e02911857f3c9a030294a0
...
HEAD is now at 01da903 add source data to DVC

$ ls
data.xml  data.xml.dvc  dog.jpg

$ dvc checkout
Data 'data.xml' didn't change.

$ ls
data.xml  data.xml.dvc
```

Note that `dog.jpg` is removed from user directory, but it still exists in cache directory. We can
remove unused cache using `dvc gc`:

```console
$ ls .dvc/cache
a3  b2

$ tree .dvc/cache
.dvc/cache
├── a3
│   └── 04afb96060aad90176268345e10355
└── b2
    └── 480770f49077512d19c452474bb7e5

2 directories, 2 files

$ dvc gc
Warning: This will remove all cache except the cache that is used in the current git branch.
Are you sure you want to proceed? (y/n)
y

$ tree .dvc/cache
.dvc/cache
├── a3
│   └── 04afb96060aad90176268345e10355
└── b2

2 directories, 1 file
```

# Pipeline Version Control

## Transformation

Here we download data and run a transformation script on the data:

```console
$ wget -q -O - https://dvc.org/s3/get-started/code.tgz | tar zx
$ virtualenv --no-site-packages .virtual
$ source .virtual/bin/activate
(.virtual) deyuan at mangosteen in /tmp/dvc on 01da903!

$ pip install -U -r requirements.txt
Collecting pandas (from -r requirements.txt (line 1))
...

# Add '.virtual' to .gitignore, then
$ git add .
$ git commit -m "add code"
```

Instead of launching script directly, in DVC, we need to use `dvc run`:
- `-d` means dependency
- `-o` means output; the output file will be automatically added to dvc version control

After running the script with `dvc run`, a new file `data.tsv.dvc` will be created by DVC, which is
the .dvc file for our output.

```console
dvc run \
  -d prepare.py -d data.xml \
  -o data.tsv -o data-test.tsv \
   python prepare.py data.xml
Running command:
        python prepare.py data.xml
Adding 'data.tsv' to '.gitignore'.
Saving 'data.tsv' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/58/245acfdc65b519c44e37f7cce12931 -> data.tsv
Adding 'data-test.tsv' to '.gitignore'.
Saving 'data-test.tsv' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/9d/603888ec04a6e75a560df8678317fb -> data-test.tsv
Saving information to 'data.tsv.dvc'.

To track the changes with git run:

        git add .gitignore data.tsv.dvc
```

Content of `data.tsv.dvc` (we can give it a different name via `-f` flag in `dvc run`):

```yaml
cmd: python prepare.py data.xml
deps:
- md5: 1436a3e43a8800d7a5f1862648bbf570
  path: prepare.py
- md5: a304afb96060aad90176268345e10355
  path: data.xml
md5: 852bbec8db2cea46fde5b7b18dcbee8e
outs:
- cache: true
  md5: 58245acfdc65b519c44e37f7cce12931
  path: data.tsv
- cache: true
  md5: 9d603888ec04a6e75a560df8678317fb
  path: data-test.tsv
```

Content of `.gitignore`. The `data.tsv` and `data-test.tsv` is the output file, around 5M and 20M
respectively.

```
.virtual

data.xml
dog.jpg
data.tsv
data-test.tsv
```

## Pipeline

Pipeline is actually a combination of multiple `dvc run`:

```console
$ dvc run -d featurization.py -d data.tsv \
              -o matrix.pkl \
              python featurization.py data.tsv matrix.pkl
Running command:
        python featurization.py data.tsv matrix.pkl
The input data frame data.tsv size is (20110, 3)
The output matrix matrix.pkl size is (20110, 5002) and data type is float64
Adding 'matrix.pkl' to '.gitignore'.
Saving 'matrix.pkl' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/fe/5d0a09d48525287af0669f884b51e3 -> matrix.pkl
Saving information to 'matrix.pkl.dvc'.

To track the changes with git run:

        git add .gitignore matrix.pkl.dvc

$ dvc run -d train.py -d matrix.pkl \
              -o model.pkl \
              python train.py matrix.pkl model.pkl
Running command:
        python train.py matrix.pkl model.pkl
/usr/lib/python3.7/site-packages/sklearn/ensemble/weight_boosting.py:29: DeprecationWarning: numpy.core.umath_tests is an internal Num
Py module and should not be imported. It will be removed in a future NumPy release.
  from numpy.core.umath_tests import inner1d
Input matrix size (20110, 5002)
X matrix size (20110, 5000)
Y matrix size (20110,)
Adding 'model.pkl' to '.gitignore'.
Saving 'model.pkl' to cache '.dvc/cache'.
Created 'hardlink': .dvc/cache/09/07e5395fd7465793796fb229c61680 -> model.pkl
Saving information to 'model.pkl.dvc'.

To track the changes with git run:

        git add .gitignore model.pkl.dvc

$ git add .gitignore matrix.pkl.dvc model.pkl.dvc
$ git commit -m "add featurization and train steps to the pipeline"
```

After running the two steps, as in transformation, we'll have two dvc files `matrix.pkl.dvc` and
`model.pkl.dvc`.

Content of `matrix.pkl.dvc`:

```yaml
cmd: python featurization.py data.tsv matrix.pkl
deps:
- md5: 73de8d15fee65c47db4acdf217efc858
  path: featurization.py
- md5: 58245acfdc65b519c44e37f7cce12931
  path: data.tsv
md5: c67650eca051faf6a0f17f80d8108112
outs:
- cache: true
  md5: fe5d0a09d48525287af0669f884b51e3
  path: matrix.pkl
```

Content of `model.pkl.dvc`:

```yaml
cmd: python train.py matrix.pkl model.pkl
deps:
- md5: d2079fff89ccf7d56f9149179dd9b411
  path: train.py
- md5: fe5d0a09d48525287af0669f884b51e3
  path: matrix.pkl
md5: 76c0a6182834f1283de59aebdd962567
outs:
- cache: true
  md5: 0907e5395fd7465793796fb229c61680
  path: model.pkl
```

With all these dvc files, we can track our model provenance:

```console
$ dvc pipeline show --ascii model.pkl.dvc
 .--------------.
 | data.xml.dvc |
 `--------------'
         *
         *
         *
 .--------------.
 | data.tsv.dvc |
 `--------------'
         *
         *
         *
.----------------.
| matrix.pkl.dvc |
`----------------'
         *
         *
         *
 .---------------.
 | model.pkl.dvc |
 `---------------'
```

Since all information are recorded, later, we can use `dvc repro model.pkl.dvc` to reproduce our
pipeline, ref: https://dvc.org/doc/get-started/reproduce.

## Metrics

There is nothing fancy about metrics in DVC.

To find the best performing experiment or track the progress, a special metric output type is
supported in DVC.

Metric file is usually a plain text file with any project-specific numbers - AUC, ROC, etc. With a
`-M` option of dvc run you can specify outputs that contain your project metrics:

```console
$ dvc run \
      -d evaluate.py -d model.pkl -d matrix-test.pkl \
      -M auc.metric \
      python evaluate.py model.pkl matrix-test.pkl auc.metric
```

The `evaluate.py` file is responsible to output metrics data into `auc.metric` file.

*References*
- https://dvc.org/doc/get-started/experiments
- https://dvc.org/doc/get-started/compare-experiments
