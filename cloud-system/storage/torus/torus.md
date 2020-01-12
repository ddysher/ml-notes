<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Block](#block)
  - [BlockRef](#blockref)
  - [BlockSpec](#blockspec)
  - [BlockLayer and BlockLayerSpec](#blocklayer-and-blocklayerspec)
  - [BlockIndex](#blockindex)
  - [BlockMetadata](#blockmetadata)
  - [INode](#inode)
  - [INodeRef](#inoderef)
  - [Ring](#ring)
  - [StorageSize](#storagesize)
  - [BlockStore](#blockstore)
  - [INodeStore](#inodestore)
  - [MetadataService](#metadataservice)
  - [Distributor](#distributor)
- [Experiments](#experiments)
  - [Introduction](#introduction)
  - [Run etcd](#run-etcd)
  - [Initialize cluster](#initialize-cluster)
  - [Run torus daemon](#run-torus-daemon)
  - [Add peers](#add-peers)
  - [Create block volume](#create-block-volume)
  - [Mount that volume via NBD (TODO)](#mount-that-volume-via-nbd-todo)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 09/2016 v0.1.2*

Torus provides a resource pool and basic **file primitives** from a set of daemons running atop
multiple nodes. These primitives are made consistent by being append-only and coordinated by etcd.
From these primitives, a Torus server can support multiple types of volumes, the semantics of which
can be broken into subprojects. It ships with a simple block-device volume plugin, but is extensible
to more.

# Concepts

## Block

The data, default is 512K.

## BlockRef

192bit identities assigned to a block when it is written at an INode Version Index. Consists of:
- 24 bits Reference Type (Data, INode, ECC, ...)
- 40 bits Volume ID
- 64 bits INode Index
- 64 bits per-index ID

This is calculated from `storage/storage.go#BlockRefFromBytes`

## BlockSpec

Block Specification is the replication/error correction applied to blocks in storage cluster, default
value is "crc". It can be comma separated string, e.g. "crc,base".

## BlockLayer and BlockLayerSpec

A logical list of blocks. Appears as a linear array of blocks, but may hold other data (or other
blocks) as well, to enable certain redundancy, availability, and data protection properties. For
example, the base block layer is just an array of blocks. The CRC block layer has a layer beneath
it to represent the array of blocks, and holds a CRC hash to the side for each of the blocks as
they are read or written.

```go
type BlockLayer struct {
  Kind    BlockLayerKind
  Options string
}
type BlockLayerSpec []BlockLayer
```

From code above, we see BlockLayer is a struct containing BlockLayerKind and options. BlockLayerKind
is one of Base, CRC and Replication.

## BlockIndex

Block index is the index where current block locates in the whole BlockStore. For example, in the
following example, BlockIndex represents the location of a block in the 20GiB blocks.

## BlockMetadata

? block volume create/delete, managing INode

## INode

INode contains file-system level information; it has block volume ID, attributes, BlockLayer (a list
of blocks), etc.

## INodeRef

Reference to INode, consists of VolumeID + InodeID (VolumeID is created from etcd, which is simply a counter).

## Ring

A collection of Peers arranged in a ring to facilitate distribution of storage and work, which is
just standard DHT.

## StorageSize

StorageSize is the size of each torus node (a physical machine or machine can have multiple torus
node). In the following example, StorageSize is 20GiB.

## BlockStore

A low-level block storage provider; currently, there are two providers: mfile and temp, see storage/'.
In the codebase, BlockStore is the interface representing the standardized methods to interact with
something storing blocks.

## INodeStore

Storage for file-system level information; basically BlockStore with INode operations.

```go
type INodeStore struct {
  bs   BlockStore
  name string
}
```

## MetadataService

A consistent store and distributed lockserver. In the codebase, MetadataService is the interface
representing the basic ways to manipulate consistently stored fileystem metadata.

## Distributor

Distributor is a complex implementation of a Torus storage interface, that understands rebalancing
it's underlying storage and fetching data from peers, as necessary.

# Experiments

## Introduction

[Link with code analysis](https://github.com/coreos/torus/blob/a9c6bc183143c2f2780bd999dd47ae152c4f4757/Documentation/getting-started.md)

## Run etcd

Just run a single etcd instance suffice: `etcd --data-dir /tmp/etcd`

## Initialize cluster

Run `./bin/torusctl init` to init torus cluster. Under the hood, global metadata is written to etcd;
the metadata contains block size, blockspec, inode replication, etc.

## Run torus daemon

Run two instances of torus daemons:

```
./bin/torusd --etcd 127.0.0.1:2379 --peer-address http://127.0.0.1:40000 --data-dir /tmp/torus1 --size 20GiB
./bin/torusd --etcd 127.0.0.1:2379 --peer-address http://127.0.0.1:40001 --data-dir /tmp/torus2 --size 20GiB
```

When running 'torusd' daemon, a server will be created with following components:
- MetadataService, either etcd or temp. For etcd, a goroutine is running to watch ring changes.
- BlockStore, either mfile or temp. For mfile, a new data file is created and truncated to specified
  to size (20GiB in this example); and a new metadata file is created with size of
  ((StorageSize/BlockSize) * BlockRefByteSize). Also, blockRef is created from its corresponding block.
  ```
  $ ls -hl /tmp/torus1/block
  total 0
  -rw-rw-r-- 1 deyuan deyuan  20G Oct 26 16:03 data-current.blk
  -rw-rw-r-- 1 deyuan deyuan 960K Oct 26 16:03 map-current.blk
  ```
- INodeStore, wraps BlockStore.
- etc.

## Add peers

Add all peers into the ring.

```
./bin/torusctl peer add --all-peers
```

Ring contains peers that are actually serving requests, i.e. a peer is not part of the ring if it's
not serving request. There is a single ring in a torus storage cluster. If we don't add peers into
the ring, they will not be able to store data. Note Distributor will watch MetaService for ring change,
and do rebalance if necessary.

## Create block volume

Create a block volume of 10GiB:

```
./bin/torusctl volume create-block myVolume 10GiB
```

This creates a 10GiB virtual blockfile for use. It will be safely replicated and CRC checked, by
default. Under the hood, torus uses MetaService (etcd) to records that a certain size of blocks are
allocated. Note, in current version (v0.1.2), cluster storage size is not checked; that is, you can
create more than 40G volumes in this example. Following is the workflow when we issue the command:
- A new volume ID is created (an atomic increasing counter).
- An internal datastructure 'blockMetadata' is created which can be used to GetINode, CreateBlockVolume, etc
- The 'blockMetadata' is an interface; block/etcd.go implements the interface. blockEtcd is a superset of MetaDataService etcd.
- CreateBlockVolume is called on etcd.

A bit of code path: `block/volume.go#CreateBlockVolume`, which just call etcd to record volume info.

## Mount that volume via NBD (TODO)

Following command creates a local volume using NBD (Network Block Device):

```
sudo ./bin/torusblk nbd myVolume /dev/nbd0
```

The same server when runnning torusd daemon will be created (but no listening this time). It opens
blockfile, i.e.

```
/tmp/torus1/block/data-current.blk
/tmp/torus1/block/map-current.blk
```

A bit of code path: `block/volume.go#OpenBlockVolume` opens BlockVolume, then use
`BlockVolume.OpenBlockFile` to open the actual file.
