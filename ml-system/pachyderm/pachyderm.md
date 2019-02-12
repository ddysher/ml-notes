<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
- [Concepts](#concepts)
  - [Repository](#repository)
  - [Branch](#branch)
  - [Commit](#commit)
  - [Hash Tree](#hash-tree)
  - [Others](#others)
- [PFS Experiment (with implementation)](#pfs-experiment-with-implementation)
  - [Installation](#installation)
  - [Create Repository](#create-repository)
  - [Put file](#put-file)
  - [Put more file](#put-more-file)
  - [Put directory](#put-directory)
  - [Storage Structure](#storage-structure)
  - [FUSE Mount](#fuse-mount)
  - [Delete File](#delete-file)
  - [Get file](#get-file)
- [PPS Experiments (with implementation)](#pps-experiments-with-implementation)
  - [Pipeline Runtime](#pipeline-runtime)
  - [Input/Output data](#inputoutput-data)
  - [Data Provenance](#data-provenance)
  - [Re-processing data](#re-processing-data)
  - [Distributed](#distributed)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Pachyderm is a tool for production data pipelines. If you need to chain together data scraping,
ingestion, cleaning, munging, wrangling, processing, modeling, and analysis in a sane way, then
Pachyderm is for you. If you have an existing set of scripts which do this in an ad-hoc fashion
and you're looking for a way to "productionize" them, Pachyderm can make this easy for you.

At its core, Pachyderm contains two parts: data versioning and data pipelining.

# Components

After running Pachyderm locally (full mode), there are three components:
- pachd: contains multiple in-process components to handle internal/external requests
- dash: frontend dashboard
- etcd: save metadata information like repo, branch, commit, as well as locking, etc.

`pachd` currently supports two modes: full and sidecar. The former includes everything you need in
a full pachd node. The later runs only pfs, the auth service, and a stripped-down version of pps.

Following is the gRPC services running in `pachd` in full model. Note the services communicate with
each other using gRPC, even if they are running in the same process.
- pfs: Pachyderm File System, the service managing versioned data
- pps: Pachyderm Pipelines, the service managing pipelines
- cache: CacheServer serves groupcache requests over grpc
- auth: Pachyderm auth system
- eprs: Service for Pachyderm enterprise edition, e.g. activate
- deploy: For deploying Pachyderm
- admin: Serving admin commands

For more information, refer to pachd's [main.go](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/cmd/pachd/main.go).

# Concepts

## Repository

From official site:
> A repo is the highest level data primitive in Pachyderm. Like many things in Pachyderm, it shares
> it's name with primitives in Git and is designed to behave analogously. Generally, repos should be
> dedicated to a single source of data such as log messages from a particular service, a users
> table, or training data for an ML model. Repos are dirt cheap so don't be shy about making tons
> of them.

Repository's data structure:

```
// RepoInfo is the main data structure representing a Repo in etcd
message RepoInfo {
  reserved 4;
  Repo repo = 1;
  google.protobuf.Timestamp created = 2;
  uint64 size_bytes = 3;
  string description = 5;
  repeated Branch branches = 7;

  // Set by ListRepo and InspectRepo if Pachyderm's auth system is active, but
  // not stored in etcd. To set a user's auth scope for a repo, use the
  // Pachyderm Auth API (in src/client/auth/auth.proto)
  RepoAuthInfo auth_info = 6;
}
```

## Branch

Branch is similar to git. Branch's data structure:

```
message BranchInfo {
  Branch branch = 4;
  Commit head = 2;
  repeated Branch provenance = 3;
  repeated Branch subvenance = 5;
  repeated Branch direct_provenance = 6;

  // Deprecated field left for backward compatibility.
  string name = 1;
}
```

## Commit

Commit is similar to git. Commit's data structure:

```
// CommitInfo is the main data structure representing a commit in etcd
message CommitInfo {
  Commit commit = 1;
  // description is a user-provided script describing this commit
  string description = 8;
  Commit parent_commit = 2;
  repeated Commit child_commits = 11;
  google.protobuf.Timestamp started = 3;
  google.protobuf.Timestamp finished = 4;
  uint64 size_bytes = 5;

  // Commits on which this commit is provenant. provenance[i] is a commit in
  // branch_provenance[i] (a branch name, and one of the branches on which this
  // commit's branch is provenant)
  repeated Commit provenance = 6;
  repeated Branch branch_provenance = 10;

  // ReadyProvenance is the number of provenant commits which have been
  // finished, if ReadyProvenance == len(Provenance) then the commit is ready
  // to be processed by pps.
  int64 ready_provenance = 12;

  repeated CommitRange subvenance = 9;
  // this is the block that stores the serialized form of a tree that
  // represents the entire file system hierarchy of the repo at this commit
  // If this is nil, then the commit is either open (in which case 'finished'
  // will also be nil) or is the output commit of a failed job (in which case
  // 'finished' will have a value -- the end time of the job)
  Object tree = 7;
}
```

## Hash Tree

A hash tree is used to represent the entire file system hierarchy of a repository at a specific
commit. Each hash tree is serialized in protocol buffer and saved in backend storage.

## Others

**Collection**

From [src/server/pkg/collection/types.go](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pkg/collection/types.go):
> Collection implements helper functions that makes common operations
> on top of etcd more pleasant to work with.  It's called collection
> because most of our data is modelled as collections, such as repos,
> commits, branches, etc.

# PFS Experiment (with implementation)

*Date: 10/12/2018, v1.7.3*

## Installation

To install local pachyderm, just run `pachctl deploy local`. Following is a list of all resources:

```console
$ kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
dash-57df5f5879-hhqdk    2/2       Running   0          17h
etcd-6dd89cf985-758nn    1/1       Running   0          17h
pachd-7f97765f5f-jh7hl   1/1       Running   0          17h

$ kubectl get service
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                   AGE
dash         NodePort    10.0.0.61    <none>        8080:30080/TCP,8081:30081/TCP                             17h
etcd         NodePort    10.0.0.181   <none>        2379:32379/TCP                                            17h
kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP                                                   17h
pachd        NodePort    10.0.0.124   <none>        650:30650/TCP,651:30651/TCP,652:30652/TCP,999:30999/TCP   17h

$ kubectl get secret
NAME                       TYPE                                  DATA      AGE
default-token-976pk        kubernetes.io/service-account-token   3         17h
pachyderm-storage-secret   Opaque                                0         17h
pachyderm-token-9fcgf      kubernetes.io/service-account-token   3         17h
```

Pachyderm depends on backend storage to persist data. By default, it uses local storage, but S3
compatible object storage is preferable. Here:
- `etcd` data path locates at host `/var/pachyderm/etcd`, mounted under `/var/data/etcd` in `etcd` container.
- `pachd` data path locates at host `/var/pachyderm/pachd`, mounted under `/pach` in `pachd` container.

All services use `NodePort`, and the exact ports are fixed and written in yaml manifests. To inspect
the manifests, refer to output from command `pachctl deploy local --dry-run`.

The secret `pachyderm-storage-secret` stores credentials used to access backend storage. It is not
used in local deployment since we simply use host path.

## Create Repository

To create a dataset repository in Pachyderm, run:

```console
$ pachctl create-repo images
```

The repository information will be persisted in etcd, and we can find it via `etcdctl get "" --from-key`,
which returns all keys in etcd. Note the key prefix `pachyderm/1.7.0` is defined in [src/server/pkg/collection](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pkg/collection/collection.go#L25).

```console
$ kubectl exec -it etcd-6dd89cf985-758nn sh
/ # ETCDCTL_API=3 etcdctl get "" --from-key --keys-only
cluster-id

master_token

pachyderm/1.7.0/pachyderm_pfs/repos/__spec__

pachyderm/1.7.0/pachyderm_pfs/repos/images

pachyderm/1.7.0/pachyderm_pps/_master_lock/694d6667676aab45
```

The key that we are interested in is `pachyderm/1.7.0/pachyderm_pfs/repos/images`, and its value is
encoded with protocol buffer. We can deserialize the protobuf and look at id `5`, which contains
[RepoInfo](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/client/pfs/pfs.proto#L56) message.

```console
$ kubectl exec -it etcd-6dd89cf985-758nn sh
/ # ETCDCTL_API=3 etcdctl get pachyderm/1.7.0/pachyderm_pfs/repos/images -w=json
{"header":{"cluster_id":14841639068965178418,"member_id":10276657743932975437,"revision":14,"raft_term":2},"kvs":[{"key":"cGFjaHlkZXJtLzEuNy4wL3BhY2h5ZGVybV9wZnMvcmVwb3MvaW1hZ2Vz","create_revision":6,"mod_revision":14,"version":5,"value":"CggKBmltYWdlcxILCJa4gd4FENPctyIY9pcnOhIKCAoGaW1hZ2VzEgZtYXN0ZXI="}],"count":1}

/ # ETCDCTL_API=3 etcdctl get pachyderm/1.7.0/pachyderm_pfs/repos/images -w=protobuf > /var/data/etcd/cbin

$ cat /var/pachyderm/etcd/cbin | protoc --decode_raw
1 {
  1: 14841639068965178418
  2: 10276657743932975437
  3: 14
  4: 2
}
2 {
  1: "pachyderm/1.7.0/pachyderm_pfs/repos/images"
  2: 6
  3: 14
  4: 5
  5 {    <----- contains 'RepoInfo'
    1 {
      1: "images"
    }
    2 {
      1: 1539333142
      2: 72216147
    }
    3: 642038
    7 {
      1 {
        1: "images"
      }
      2: "master"
    }
  }
}
4: 1
```

## Put file

We can upload data to Pachyderm from remote url:

```console
$ pachctl put-file images master liberty.png -c -f http://imgur.com/46Q8nDz.png

$ pachctl list-commit images
REPO   ID                               PARENT                           STARTED      DURATION           SIZE
images 4f1cbc6d633c4c02b654c78e6b71848f <none>                           23 hours ago Less than a second 57.27KiB
```

The request goes to `pachd` via gRPC (exposed via NodePort), which downloads data from remote source.
Command line will block until pachd finishes downloading data.

After downloading data, pachd (to be specific, `pfs` inside pachd) creates `branch` and `commit` and
persists in etcd. **That is, each `branch` and `commit` will have corresponding key/value in etcd**.
Corresponding protocol buffer definitions, `BranchInfo` and `CommitInfo`, can be found at [pfs.proto](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/client/pfs/pfs.proto).

```console
$ kubectl exec -it etcd-6dd89cf985-758nn sh
/# ETCDCTL_API=3 etcdctl get "" --from-key --keys-only
cluster-id

master_token

pachyderm/1.7.0/pachyderm_pfs/branches/images/master

pachyderm/1.7.0/pachyderm_pfs/commits/images/4f1cbc6d633c4c02b654c78e6b71848f

pachyderm/1.7.0/pachyderm_pfs/repos/__spec__

pachyderm/1.7.0/pachyderm_pfs/repos/images

pachyderm/1.7.0/pachyderm_pps/_master_lock/694d6667676aab45
```

Following is the structure in backing storage. The backing storage is initially empty before we call
`pachctl put-file`.

```console
$ tree /var/pachyderm/pachd/pach/
/var/pachyderm/pachd/pach/
├── block
│   ├── 9a5f0d5521b84220ad024d8033012f9b
│   ├── a5b0b57813d6453098968fa55ee8bc65
└── object
    ├── 6fc8eb03af273b6b68fca2b238f1b1eb6cef011f79c3a87f365f360da449a011ff3a7c4d390507ad7e8ad27971876cdf80cbd5642477400c553acef8c6b99ded
    ├── ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297

2 directories, 4 files
```

Here, file `9a5f0d5521b84220ad024d8033012f9b` under `block` directory is our data, we can inspect it
with (on linux):

```console
$ cat /var/pachyderm/pachd/pach/block/9a5f0d5521b84220ad024d8033012f9b | display
```

We'll look at other files later.

## Put more file

Now we put one more file to see how Pachyderm manages data. Note size of first image is about 58k,
second image is around 285k.

```console
$ pachctl put-file images master dog.png -c -f https://imgur.com/HJCjylV.jpg
```

Following is the output for:
- Pachyderm list commit
- All keys in etcd
- Local object storage structure

```
$ pachctl list-commit images
REPO   ID                               PARENT                           STARTED      DURATION           SIZE
images 13adce53d8924e66a7ab62bb47496520 4f1cbc6d633c4c02b654c78e6b71848f 27 hours ago Less than a second 342.1KiB
images 4f1cbc6d633c4c02b654c78e6b71848f <none>                           27 hours ago Less than a second 57.27KiB

$ kubectl exec -it etcd-6dd89cf985-758nn sh
/ # ETCDCTL_API=3 etcdctl get "" --from-key --keys-only
cluster-id

master_token

pachyderm/1.7.0/pachyderm_pfs/branches/images/master

pachyderm/1.7.0/pachyderm_pfs/commits/images/13adce53d8924e66a7ab62bb47496520

pachyderm/1.7.0/pachyderm_pfs/commits/images/4f1cbc6d633c4c02b654c78e6b71848f

pachyderm/1.7.0/pachyderm_pfs/repos/__spec__

pachyderm/1.7.0/pachyderm_pfs/repos/images

pachyderm/1.7.0/pachyderm_pps/_master_lock/694d6667676aab45

$ tree /var/pachyderm/pachd/pach/
/var/pachyderm/pachd/pach/
├── block
│   ├── 9a5f0d5521b84220ad024d8033012f9b
│   ├── a5b0b57813d6453098968fa55ee8bc65
│   ├── b79dd2253d3b4cefa0874be856419280
│   └── c6b88df2763f456289356e8f43f2a128
└── object
    ├── 0cf6e5780209cd77dfa96840f20ad283f1a35476cad8b4e13ac683f2915692c603e5c7d5f5d20f336b0b5be39a8732a2721973ebb9c35eec17bbc9fb05bec846
    ├── 6fc8eb03af273b6b68fca2b238f1b1eb6cef011f79c3a87f365f360da449a011ff3a7c4d390507ad7e8ad27971876cdf80cbd5642477400c553acef8c6b99ded
    ├── ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297
    └── d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc
```

Here, file `b79dd2253d3b4cefa0874be856419280` under `block` directory is our data. The structure and
`list-commit` output shows that files are saved incrementally, meaning that newer commit sits on top
of old commit and new commit contains files from old commit.

## Put directory

Now we continue puting one more file under a directory named `dir`. Pay attention here that we are
putting the same file `HJCjylV.jpg`.

```console
pachctl put-file images master dir/dog.png -c -f https://imgur.com/HJCjylV.jpg
```

Following is the output for:
- Pachyderm list commit
- Local object storage structure

```console
$ pachctl list-commit images
REPO   ID                               PARENT                           STARTED     DURATION           SIZE
images aace5bc556d24155ad14326cb7b7d465 13adce53d8924e66a7ab62bb47496520 4 hours ago Less than a second 627KiB
images 13adce53d8924e66a7ab62bb47496520 4f1cbc6d633c4c02b654c78e6b71848f 5 hours ago Less than a second 342.1KiB
images 4f1cbc6d633c4c02b654c78e6b71848f <none>                           5 hours ago Less than a second 57.27KiB

$ tree /var/pachyderm/pachd/pach/
/var/pachyderm/pachd/pach/
├── block
│   ├── 5f3052bcdb4d4f48831d2435d816f13d
│   ├── 9a5f0d5521b84220ad024d8033012f9b
│   ├── a5b0b57813d6453098968fa55ee8bc65
│   ├── b79dd2253d3b4cefa0874be856419280
│   └── c6b88df2763f456289356e8f43f2a128
└── object
    ├── 0cf6e5780209cd77dfa96840f20ad283f1a35476cad8b4e13ac683f2915692c603e5c7d5f5d20f336b0b5be39a8732a2721973ebb9c35eec17bbc9fb05bec846
    ├── 6fc8eb03af273b6b68fca2b238f1b1eb6cef011f79c3a87f365f360da449a011ff3a7c4d390507ad7e8ad27971876cdf80cbd5642477400c553acef8c6b99ded
    ├── ab25f7680f0811dc115c904a5b4690a90353a0b4daa6ccb5f750880d44742d73a2a335eb2d4e0a5e6031ae1b84bb2e4fc48b533fb299d0e16d9e16ae9b526c44
    ├── ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297
    └── d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc

2 directories, 10 files
```

Note here since we are puting the same file, there's no image saved in `block` directory. As we'll
see in next section, the hashtree proto output shows that both `dir/dog.png` and `dog.png` has the
same object hash.

## Storage Structure

Let's look at the top level commit. Using `--raw` will print the [CommitInfo](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/client/pfs/pfs.proto#L96)
protocol buffer in json format:

```console
$ pachctl inspect-commit images aace5bc556d24155ad14326cb7b7d465 --raw
{
  "commit": {
    "repo": {
      "name": "images"
    },
    "id": "aace5bc556d24155ad14326cb7b7d465"
  },
  "parentCommit": {
    "repo": {
      "name": "images"
    },
    "id": "13adce53d8924e66a7ab62bb47496520"
  },
  "started": "2018-10-12T09:41:07.075721977Z",
  "finished": "2018-10-12T09:41:07.083673622Z",
  "sizeBytes": "642038",
  "tree": {
    "hash": "ab25f7680f0811dc115c904a5b4690a90353a0b4daa6ccb5f750880d44742d73a2a335eb2d4e0a5e6031ae1b84bb2e4fc48b533fb299d0e16d9e16ae9b526c44"
  }
}
```

Here, the `tree:hash` value points to a [serialized tree](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pkg/hashtree/hashtree.proto#L48)
which saves the serialized form of a hashtree that represents **the entire file system hierarchy of
the repo at this commit**. The object above is saved under `object` directory, which is the [ObjectIndex](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/client/pfs/pfs.proto#L535)
protocol buffer (TBD).

```console
$ cd $GOPATH/src/github.com/pachyderm/pachyderm
$ cat /var/pachyderm/pachd/pach/object/ab25f7680f0811dc115c904a5b4690a90353a0b4daa6ccb5f750880d44742d73a2a335eb2d4e0a5e6031ae1b84bb2e4fc48b533fb299d0e16d9e16ae9b526c44 \
  | protoc --decode pfs.ObjectIndex src/client/pfs/pfs.proto \
  -I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  -I${GOPATH}/src/github.com/gogo/protobuf \
  -I${GOPATH}/src \
  -Isrc
objects {
  key: "5f3052bcdb4d4f48831d2435d816f13d"
}
tags {
  2: 751
}
```

The value `5f3052bcdb4d4f48831d2435d816f13d` in ObjectIndex references the real hashtree proto:

```console
$ cd $GOPATH/src/github.com/pachyderm/pachyderm
$ cat /var/pachyderm/pachd/pach/block/5f3052bcdb4d4f48831d2435d816f13d \
  | protoc --decode HashTreeProto src/server/pkg/hashtree/hashtree.proto \
  -I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  -I${GOPATH}/src/github.com/gogo/protobuf \
  -I${GOPATH}/src \
  -Isrc
version: 1
fs {
  value {
    hash: "\327Y\373\372q\023l\343\225U\315\177\364\326\204\264FD-\236\374[\212\235\316\340\340B\013CR\304"
    subtree_size: 642038
    dir_node {
      children: "dir"
      children: "dog.png"
      children: "liberty.png"
    }
  }
}
fs {
  key: "/dir"
  value {
    name: "dir"
    hash: "\025\373:\212\272\316\232\010\260o\206\r\271\302\3539\241\263O9\226b\342\034hI\357bWx\275["
    subtree_size: 291697
    dir_node {
      children: "dog.png"
    }
  }
}
fs {
  key: "/dir/dog.png"
  value {
    name: "dog.png"
    hash: "9\225#\316\255\365\377\370\\X\017\225\001-?\277\254\211s\007\365\377\210Y\202K\276\n3\321\322\036"
    subtree_size: 291697
    file_node {
      objects {
        hash: "d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc"
      }
    }
  }
}
fs {
  key: "/dog.png"
  value {
    name: "dog.png"
    hash: "9\225#\316\255\365\377\370\\X\017\225\001-?\277\254\211s\007\365\377\210Y\202K\276\n3\321\322\036"
    subtree_size: 291697
    file_node {
      objects {
        hash: "d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc"
      }
    }
  }
}
fs {
  key: "/liberty.png"
  value {
    name: "liberty.png"
    hash: "\341H\347\235\370\301WoUFw3\317K\232>\253\3432iU\253\267\245\213%J,I\365X\023"
    subtree_size: 58644
    file_node {
      objects {
        hash: "ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297"
      }
    }
  }
}
```

Pay attention here that in `CommitInfo` proto, the `tree:hash` value is NOT the hash of its hashtree
proto. Instead, it's an opaque hash which logically points to the real hashtree proto. There is
another layer of abstraction in [pfs object API](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pfs/server/obj_block_api_server.go)
to do the translation. This is true for our image data as well.

In another word, in Pachyderm, both user uploaded data (like the image we uploaded) and internal
data (like the hash tree) are objects served via pfs object API. The API returns an opaque hash to
its clients. When retrieving data, the opaque hash is passed to pfs object API. It uses the hash to
locate ObjectIndex, which contains hashes of the real data underneath.

For example, below is the code snippet for retrieving hashtree proto:

```go
# in src/server/pfs/server/driver.go

treeRef := commitInfo.Tree

if treeRef == nil {
    t, err := hashtree.NewHashTree().Finish()
    if err != nil {
        return nil, err
    }
    return t, nil
}

// read the tree from the block store
var buf bytes.Buffer
if err := pachClient.GetObject(treeRef.Hash, &buf); err != nil {
    return nil, err
}

h, err := hashtree.Deserialize(buf.Bytes())
if err != nil {
    return nil, err
}
```

Here, the driver directly uses:
```
treeRef := commitInfo.Tree (value ab25f7680f0811dc115c904a5b4690a90353a0b4daa6ccb5f750880d44742d73a2a335eb2d4e0a5e6031ae1b84bb2e4fc48b533fb299d0e16d9e16ae9b526c44)
```
to find serialized proto, it is the `pachClient.GetObject` (part of pfs object API) which uses the
opaque object hash to find real data.

## FUSE Mount

To use FUSE mount, first edit `etc/fuse.conf` to add option `user_allow_other`, then run:

```
$ pachctl mount /tmp/pachmnt
Filesystem mounted, CTRL-C to exit.

$ tree /tmp/pachmnt
/tmp/pachmnt
└── images
    ├── 13adce53d8924e66a7ab62bb47496520
    │   ├── dog.png
    │   └── liberty.png
    ├── 4f1cbc6d633c4c02b654c78e6b71848f
    │   └── liberty.png
    ├── aace5bc556d24155ad14326cb7b7d465
    │   ├── dir
    │   ├── dog.png
    │   └── liberty.png
    └── master
        ├── dir
        ├── dog.png
        └── liberty.png

7 directories, 7 files

$ ls /tmp/pachmnt/images/aace5bc556d24155ad14326cb7b7d465/dir
ls: reading directory '/tmp/pachmnt/images/aace5bc556d24155ad14326cb7b7d465/dir': Input/output error
```

It shows that Pachyderm mount all repositories and all commits in out mount point. We can browse
individual commit separately. Note it seems to be a bug that we are unable to view directory with
deeper level.

Implementation-wise, Pachyderm uses [bazil.org/fuse](https://github.com/bazil/fuse), which is a Go
implementation of FUSE protocol (doesn't rely on C library). The [filesystem](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pfs/fuse/filesystem.go#L28)
object in Pachyderm implements methods required in bazil API, e.g. Root(), Open(), Attr(), Lookup(),
Mkdir(), etc.

## Delete File

Unlike `pachctl put-file` where we use `-c` option to automatically start/finish commit, to delete
file in Pachyderm, we need to explicitly call `pachctl start-commit` and `pachctl finish-commit`.

```shell
$ pachctl list-commit images
REPO   ID                               PARENT                           STARTED      DURATION           SIZE
images aace5bc556d24155ad14326cb7b7d465 13adce53d8924e66a7ab62bb47496520 47 hours ago Less than a second 627KiB
images 13adce53d8924e66a7ab62bb47496520 4f1cbc6d633c4c02b654c78e6b71848f 2 days ago   Less than a second 342.1KiB
images 4f1cbc6d633c4c02b654c78e6b71848f <none>                           2 days ago   Less than a second 57.27KiB

# Here we start a new commit to delete file.
$ pachctl start-commit images master
50cf2d7a0c324380b0ef109fef4303cb

# We must explicitly use the commit to delete file.
$ pachctl delete-file images 50cf2d7a0c324380b0ef109fef4303cb dog.png

# Then finish the commit.
$ pachctl finish-commit images 50cf2d7a0c324380b0ef109fef4303cb
```

After finishing the commit, we can see that our commit has smaller size than its parent commit, and
the `dog.png` doesn't exist from `pachctl list-file`:

```shell
$ pachctl list-commit images
REPO   ID                               PARENT                           STARTED        DURATION           SIZE
images 50cf2d7a0c324380b0ef109fef4303cb aace5bc556d24155ad14326cb7b7d465 30 seconds ago 26 seconds         342.1KiB
images aace5bc556d24155ad14326cb7b7d465 13adce53d8924e66a7ab62bb47496520 47 hours ago   Less than a second 627KiB
images 13adce53d8924e66a7ab62bb47496520 4f1cbc6d633c4c02b654c78e6b71848f 2 days ago     Less than a second 342.1KiB
images 4f1cbc6d633c4c02b654c78e6b71848f <none>                           2 days ago     Less than a second 57.27KiB

$ pachctl list-file images 50cf2d7a0c324380b0ef109fef4303cb
NAME        TYPE SIZE
dir         dir  284.9KiB
liberty.png file 57.27KiB
```

Based on our experience above, it should be easy to understand how it works. Following is the output for:
- Local object storage structure
- Pachyderm inspect top commit
- HashTree proto

```
$ tree /var/pachyderm/pachd
/var/pachyderm/pachd
└── pach
    ├── block
    │   ├── 4154d7fd50d4419c9e096796ea6424d8
    │   ├── 5f3052bcdb4d4f48831d2435d816f13d
    │   ├── 9410ee7d0bb5412fb8166ff9e66f19f9
    │   ├── 9a5f0d5521b84220ad024d8033012f9b
    │   ├── a5b0b57813d6453098968fa55ee8bc65
    │   ├── b79dd2253d3b4cefa0874be856419280
    │   └── c6b88df2763f456289356e8f43f2a128
    └── object
        ├── 0cf6e5780209cd77dfa96840f20ad283f1a35476cad8b4e13ac683f2915692c603e5c7d5f5d20f336b0b5be39a8732a2721973ebb9c35eec17bbc9fb05bec846
        ├── 25226d705a85c6d1632725c4016b56ec74c3ddcc3779690f0c5d16d2f9e4140c93d05fbda8a8d88878561147820ce529de82b748be2f169f6e168cf0c033c341
        ├── 6fc8eb03af273b6b68fca2b238f1b1eb6cef011f79c3a87f365f360da449a011ff3a7c4d390507ad7e8ad27971876cdf80cbd5642477400c553acef8c6b99ded
        ├── ab25f7680f0811dc115c904a5b4690a90353a0b4daa6ccb5f750880d44742d73a2a335eb2d4e0a5e6031ae1b84bb2e4fc48b533fb299d0e16d9e16ae9b526c44
        ├── ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297
        ├── c735513fc941aad91a407d03c91b4d2bb77d4a1450733406f9330141be9c38dab5180faee9fc57b45b20fb8c69bc305fd776db344528ec6332dd8687c41a566e
        └── d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc

3 directories, 14 files

$ pachctl inspect-commit images 50cf2d7a0c324380b0ef109fef4303cb --raw
{
  "commit": {
    "repo": {
      "name": "images"
    },
    "id": "50cf2d7a0c324380b0ef109fef4303cb"
  },
  "parentCommit": {
    "repo": {
      "name": "images"
    },
    "id": "aace5bc556d24155ad14326cb7b7d465"
  },
  "started": "2018-10-14T08:14:33.564651776Z",
  "finished": "2018-10-14T08:15:00.170776189Z",
  "sizeBytes": "350341",
  "tree": {
    "hash": "25226d705a85c6d1632725c4016b56ec74c3ddcc3779690f0c5d16d2f9e4140c93d05fbda8a8d88878561147820ce529de82b748be2f169f6e168cf0c033c341"
  }
}

$ cat /var/pachyderm/pachd/pach/object/25226d705a85c6d1632725c4016b56ec74c3ddcc3779690f0c5d16d2f9e4140c93d05fbda8a8d88878561147820ce529de82b748be2f169f6e168cf0c033c341 | protoc --decode_raw
1 {
  1: "9410ee7d0bb5412fb8166ff9e66f19f9"
}
2 {
  2: 542
}

$ cd $GOPATH/src/github.com/pachyderm/pachyderm
$ cat /var/pachyderm/pachd/pach/block/9410ee7d0bb5412fb8166ff9e66f19f9 \
  | protoc --decode HashTreeProto src/server/pkg/hashtree/hashtree.proto \
  -I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  -I${GOPATH}/src/github.com/gogo/protobuf \
  -I${GOPATH}/src \
  -Isrc
version: 1
fs {
  value {
    hash: "\257M\306\315\231\342V\370\033\330\323X\032\023\212\373$\2665Ab\366 Mnrzr\240\241\341\206"
    subtree_size: 350341
    dir_node {
      children: "dir"
      children: "liberty.png"
    }
  }
}
fs {
  key: "/dir"
  value {
    name: "dir"
    hash: "\025\373:\212\272\316\232\010\260o\206\r\271\302\3539\241\263O9\226b\342\034hI\357bWx\275["
    subtree_size: 291697
    dir_node {
      children: "dog.png"
    }
  }
}
fs {
  key: "/dir/dog.png"
  value {
    name: "dog.png"
    hash: "9\225#\316\255\365\377\370\\X\017\225\001-?\277\254\211s\007\365\377\210Y\202K\276\n3\321\322\036"
    subtree_size: 291697
    file_node {
      objects {
        hash: "d7b219392c59f2a9bdad155f4a076ac6c61fab89c4e8254ac16fd25cce6cc6b39d885bd66916730b2e8bc01cf784ca3df708fdb18c4f77d55026b548cbbc3cbc"
      }
    }
  }
}
fs {
  key: "/liberty.png"
  value {
    name: "liberty.png"
    hash: "\341H\347\235\370\301WoUFw3\317K\232>\253\3432iU\253\267\245\213%J,I\365X\023"
    subtree_size: 58644
    file_node {
      objects {
        hash: "ab3eed91f9886306a075bd67399205c45bd4baa3e4f1d3bca87600a54a618e5e4487e9c3d27cc0fae9e94bdecb029dbd2aaa4f98042f949b1deba03ab3ebb297"
      }
    }
  }
}
```

## Get file

To get file from pachyderm, we use command:

```console
$ pachctl get-file images master liberty.png | display
```

Based on source code from [pfs command line](https://github.com/pachyderm/pachyderm/blob/v1.7.3/src/server/pfs/cmds/cmds.go),
it calls pfs to walk repository filesystem at a specific commit, once file is found, it calls pfs
to download the file. pfs to locate the object and returns a stream to client. In short, the data
is proxied by pachd between client and backend storage.

Note for worker, it mounts backend storage to minimize hops, ref: https://github.com/pachyderm/pachyderm/issues/223

# PPS Experiments (with implementation)

## Pipeline Runtime

As soon as you create your pipeline, Pachyderm will launch worker pods on Kubernetes. These worker
pods will remain up and running, such that they are ready to process any data committed to their
input repos. This allows the pipeline to immediately respond to new data when it’s committed without
having to wait for their pods to "spin up". However, this has the downside that pods will consume
resources even while there’s no data to process. You can trade-off the other way by setting the
`standby` field to true in your pipeline spec. With this field set, the pipelines will "spin down"
when there is no data to process, which means they will consume no resources. However, when new data
does come in, the pipeline pods will need to spin back up, which introduces some extra latency.
Generally speaking, you should default to not setting `standby` until cluster utilization becomes a
concern. When it does, pipelines that run infrequently and are highly parallel are the best candidates
for standby.

Creating a pipeline tells Pachyderm to run the `cmd` (i.e., your code) in your image on the data in
the HEAD (most recent) commit of the input repo(s) as well as all future commits to the input repo(s).
You can think of this pipeline as being “subscribed” to any new commits that are made on any of its
input repos. It will automatically process the new data as it comes in.

By default, every pipeline has pod, e.g. after creating two pipelines, we have:

```console
$ kubectl get pods
NAME                        READY     STATUS    RESTARTS   AGE
dash-57df5f5879-l7ccw       2/2       Running   0          30m
etcd-6dd89cf985-nxjwm       1/1       Running   0          30m
pachd-6f94b7966b-4jknn      1/1       Running   0          30m
pipeline-edges-v1-84lg4     2/2       Running   0          20m
pipeline-montage-v1-prbkv   2/2       Running   0          18m
```

For each pipeline, there are one init container and two regular containers:
- init container: running image `pachyderm/worker:1.7.3` with command `/pach/worker.sh`
  - the container mounts the same volume as user container and copies pachyderm specific binary to user container
- user container: running pipeline image, e.g. `pachyderm/opencv` from pipeline spec, with command `/pach-bin/worker`
  - this is called user container but actually runs Pachyderm worker
  - the container is responsible to watch pipeline, download data, exec user code, upload data, etc
- storage container: running image `pachyderm/pachd:1.7.3` with command `/pachd --mode sidecar`
  - the `pachd` sidecar mode has auth service, pfs and a stripped-down version of pps
  - the container is responsible to serve storage requests and interact with pfs

The pipeline worker is long running. For example, we put an image then another new image into `images`
repository, which triggers the pipeline to run twice. The log shows that pipeline worker re-executes
the same pipeline again. Since user code is launched via os.exec, there is no extra pod launched in
Kubernetes.

```console
$ kubectl logs -f pipeline-edges-v1-84lg4 -c user
{"pipelineName":"edges","workerId":"pipeline-edges-v1-84lg4","master":true,"ts":"2018-10-17T05:32:14.366795216Z","message":"Launching worker master process"}
{"pipelineName":"edges","workerId":"pipeline-edges-v1-84lg4","master":true,"ts":"2018-10-17T05:32:14.393445467Z","message":"waitJob: 43391b3703f749a29fb87de6d7d9495a"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.406629616Z","message":"starting to download data"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.418599391Z","message":"finished downloading data after 11.866467ms"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.418781767Z","message":"beginning to run user code"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"user":true,"ts":"2018-10-17T05:32:14.927122268Z","message":"/usr/local/lib/python3.4/dist-packages/matplotlib/font_manager.py:273: UserWarning: Matplotlib is building the font cache using fc-list. This may take a moment."}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"user":true,"ts":"2018-10-17T05:32:14.927238923Z","message":"  warnings.warn('Matplotlib is building the font cache using fc-list. This may take a moment.')"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"user":true,"ts":"2018-10-17T05:32:14.927296980Z","message":"/usr/local/lib/python3.4/dist-packages/matplotlib/font_manager.py:273: UserWarning: Matplotlib is building the font cache using fc-list. This may take a moment."}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"user":true,"ts":"2018-10-17T05:32:14.927330869Z","message":"  warnings.warn('Matplotlib is building the font cache using fc-list. This may take a moment.')"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.963536367Z","message":"finished running user code after 544.716018ms"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.963601648Z","message":"starting to upload output"}
{"pipelineName":"edges","jobId":"43391b3703f749a29fb87de6d7d9495a","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T05:32:14.967316516Z","message":"finished uploading output after 3.68324ms"}


{"pipelineName":"edges","workerId":"pipeline-edges-v1-84lg4","master":true,"ts":"2018-10-17T11:44:41.382586175Z","message":"waitJob: 740818148f80421fb51b494250c6384c"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.398003462Z","message":"starting to download data"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.404516754Z","message":"finished downloading data after 6.420197ms"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.404649350Z","message":"beginning to run user code"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.783007226Z","message":"finished running user code after 378.322953ms"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.783087057Z","message":"starting to upload output"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"dc7551c0f094c902287fdfe2c3a100710f7e66cfdea8d4690cb709d6da17bed3","data":[{"path":"/kitten.png","hash":"02rRTQewfKV2JXxaU7zPW/rEML3uI/DLi+XmPbyntEs="}],"ts":"2018-10-17T11:44:41.791406299Z","message":"finished uploading output after 8.274027ms"}
{"pipelineName":"edges","jobId":"740818148f80421fb51b494250c6384c","workerId":"pipeline-edges-v1-84lg4","datumId":"b72e3cae6917061bec01b92a1e14d7530cfa4525695b7be033d6b365dfaa6bd0","data":[{"path":"/liberty.png","hash":"4UjnnfjBV29VRnczz0uaPqvjMmlVq7eliyVKLEn1WBM="}],"ts":"2018-10-17T11:44:41.814700078Z","message":"skipping datum"}
```

As mentioned above, the worker is responsible to:
- watch pipeline/job: pipeline worker launches user code based on job
- download data: pipeline worker downloads data of a repo at a certain commit (only diff)
- exec user code: pipeline worker executes user code via `exec`
- upload data: pipeline worker uploads all data from `/pfs/output`

## Input/Output data

Worker will download data into `/pfs` in user container. Note that:
- looks like only diff will be downloaded
- data will really be downloaded (not linked), even if it's quite large, we can see from container
  volume (here `c005735e-d283-11e8-b52c-2c4d54ed3845` is pod id):
  ```
  $ sudo ls -alh /var/lib/kubelet/pods/c005735e-d283-11e8-b52c-2c4d54ed3845/volumes/kubernetes.io~empty-dir/pachyderm-worker/611035a136024700b6d69594c63e3d5f/images
  total 140M
  drwx------ 2 root root 4.0K Oct 18 11:13 .
  drwx------ 4 root root 4.0K Oct 18 11:13 ..
  -rw-r--r-- 1 root root 140M Oct 18 11:13 kube-controller
  ```

Any content inside of `/pfs/output` will be uploaded to pfs by worker, and every run of user code
has different view of input data (data is wiped out after each pipeline execution), despite the fact
that user code in running on the same container every time.

## Data Provenance

We can inspect data provenance via `flush-commit`, here we can see which commits come out of a
specific commit in `images` repo.

```
$ pachctl list-commit images
REPO                ID                                 PARENT                             STARTED              DURATION             SIZE
images              c721c4bb9a8046f3a7319ed97d256bb9   a9678d2a439648c59636688945f3c6b5   About a minute ago   1 seconds            932.2 KiB
images              a9678d2a439648c59636688945f3c6b5   87f5266ef44f4510a7c5e046d77984a6   About a minute ago   Less than a second   238.3 KiB
images              87f5266ef44f4510a7c5e046d77984a6   <none>                             10 minutes ago       Less than a second   57.27 KiB
$ pachctl list-commit edges
REPO                ID                                 PARENT                             STARTED              DURATION             SIZE
edges               f716eabf95854be285c3ef23570bd836   026536b547a44a8daa2db9d25bf88b79   About a minute ago   Less than a second   233.7 KiB
edges               026536b547a44a8daa2db9d25bf88b79   754542b89c1c47a5b657e60381c06c71   About a minute ago   Less than a second   133.6 KiB
edges               754542b89c1c47a5b657e60381c06c71   <none>                             2 minutes ago        Less than a second   22.22 KiB

$ pachctl flush-commit images/a9678d2a439648c59636688945f3c6b5
REPO                ID                                 PARENT                             STARTED             DURATION             SIZE
edges               026536b547a44a8daa2db9d25bf88b79   754542b89c1c47a5b657e60381c06c71   3 minutes ago       Less than a second   133.6 KiB
```

## Re-processing data

As of 1.5.1, updating a pipeline will NOT reprocess previously processed data by default. New data
that's committed to the inputs will be processed with the new code and "mixed" with the results of
processing data with the previous code. Furthermore, data that Pachyderm tried and failed to process
with the previous code due to code erroring will be processed with the new code.

If you'd like to update your pipeline and have that updated pipeline reprocess all the data that is
currently in the HEAD commit of your input repos, you should use the `--reprocess` flag.

## Distributed

Pachyderm support spliting data upon uploading, ref [here](http://docs.pachyderm.io/en/v1.7.3/cookbook/splitting.html).
The core distributed capability comes from the glob pattern, ref [here](http://docs.pachyderm.io/en/v1.7.3/fundamentals/distributed_computing.html).
For example, if dataset looks like:

```
/California
   /San-Francisco.json
   /Los-Angeles.json
   ...
/Colorado
   /Denver.json
   /Boulder.json
   ...
...
```

then:
- `/` means all data are handled in one batch
- `/*` means each state can be handled individually
- `/*/*` means each city can be handled individually
