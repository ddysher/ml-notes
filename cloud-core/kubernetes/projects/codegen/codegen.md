<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [gengo](#gengo)
  - [Overview](#overview)
  - [Concepts](#concepts)
  - [Example](#example)
- [client-gen](#client-gen)
  - [Overview](#overview-1)
  - [Usage](#usage)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# gengo

*Date: 08/25/2017, kubernetes v1.7*

## Overview

gengo is a package for generating things based on go files.

## Concepts

**Namer**

Namer defines a naming systems, it has support for different type naming systems. For example, if we
define `type foo string`, and we want to generate something like `func FooPrinter(f *foo) { Print(string(*f)) }`,
then we need three things for `foo`
- a public name (Foo)
- a literal name (foo)
- an underlying literal name (string).

There are several builtin namer. For example, a raw namer will return the literal type (for
`type map[string]string`, return `map[string]string`). One point about namer is how to deal with
package. In namer, if we print a `type.Name`, we have something like this `github.com/ddysher/hello-gengo/pkg/apis.Employee`,
where `github.com/ddysher/hello-gengo/pkg/apis` is the package name and `Employee` is the type name.
For more details, see "gengo/namer".

## Example

Here we use `set-gen` as example. First, `cd` into gengo directory and build (install) set-gen binary:

```
$ cd $GOPATH/src/k8s.io/gengo/examples/set-gen
$ go install .
```

A `set-gen` binary will be generated under `$GOPATH/bin`. Now we can use `set-gen` to generate sets
for our types.

```
# Copy the types under GOPATH
$ mkdir -p $GOPATH/src/github.com/ddysher
$ rm -rf $GOPATH/src/github.com/ddysher/hello-gengo
$ cp -r hello-gengo $GOPATH/src/github.com/ddysher

# Generate sets.
$ set-gen --input-dirs="github.com/ddysher/hello-gengo" --output-package="github.com/ddysher/hello-gengo"
```

Note gengo doesn't have release; the experiment is done with commit ID: 2ef5ef33e269934e14149598f5a85d1f561a7219

# client-gen

*Date: 09/04/2017, kubernetes v1.7*

## Overview

client-gen is part of code generation tools of kubernetes, other generations are deepcopy-gen,
conversion-gen, etc. These tools was located at kubernetes main repository, and are now being moved
to separate repositories, i.e.
```
k8s.io/kubernetes/cmd/libs ->
k8s.io/kubernetes/staging/src/k8s.io/code-generator -> (https://github.com/kubernetes/kubernetes/pull/49114)
k8s.io/code-generator
```

For introduction, ref [here](https://github.com/kubernetes/community/blob/8cd7304aa76ad9c792b0ea272b49f0d8712d8439/contributors/devel/generating-clientset.md).
client-gen is not specific to kubernetes; it can be used to generate client as long as the project
conforms to its convention. Usually, the generated output is put under `projectroot/kubernetes`.

## Usage

First, `cd` into client-gen directory and build (install) `client-gen` binary:

```
# Commit ID: bf449d588b78132603c5e2dba7286e7d335abedc
$ cd $GOPATH/src/k8s.io/code-generator/cmd/client-gen
$ go install .
```

A `client-gen` binary will be generated under `$GOPATH/bin`. Now we use `client-gen` to generate a
sample client for own types.

```
# Copy the types under GOPATH
$ mkdir -p $GOPATH/src/github.com/ddysher
$ cp -r hello-client-gen $GOPATH/src/github.com/ddysher

# Generate client packages.
$ client-gen --input-base="github.com/ddysher/hello-client-gen" --input="pkg/apis/release/v1alpha1" --clientset-path="github.com/ddysher/hello-client-gen/" --clientset-name="kubernetes"
```
