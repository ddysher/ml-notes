<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [ModelDB](#modeldb)
  - [Installation](#installation)
  - [How it works](#how-it-works)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# ModelDB

## Installation

Follow [this link](https://github.com/mitdbg/modeldb/tree/910efb4df8304bb05ae4defce9bd55c53f26a759/dockerbuild)
to bring up a modeldb instance. It will bring up three components:
- backend
- frontend
- mongodb

There's no SQL database, but modeldb uses sqlite internally (in backend) to save
model information; only metadata is saved in mongodb.

For Python, make sure to run `./build_client.sh` in `client/python`.

## How it works

ModelDB backend provides RPC (thrift) calls to persist model information, the so
called ['light api'](https://github.com/mitdbg/modeldb/blob/910efb4df8304bb05ae4defce9bd55c53f26a759/client/python/light_api.md).
Right now it provides wrapper for sparkml and sklean. User should use client package
to automatically send metrics.

**Example**

Below is a short analysis of `SimpleSample.py`.

In client package, function [ModelDbSyncer.py#enable_sklearn_sync_functions(self)](https://github.com/mitdbg/modeldb/blob/910efb4df8304bb05ae4defce9bd55c53f26a759/client/python/modeldb/sklearn_native/ModelDbSyncer.py#L415)
adds more functions to sklearn package (via setattr), then users are required to
use these sync version instead of native methods. When sync version method is called,
an event (e.g. FitEvent) will be generated and saved in buffer, and then pushed to
server.
