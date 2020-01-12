<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Builder](#builder)
  - [BuildPack](#buildpack)
  - [Stack](#stack)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Concepts in buildpacks:
- Builder
- BuildPack
- Stacks

## Builder

Builder is a container image used to build application image: it can be treated as the final output
of the BuildPack Standard.

A Builder is built from a `builder.toml` file. For example, the following Builder includes three
BuildPacks with specific order, and one stack.

```toml
# Buildpacks to include in builder
[[buildpacks]]
uri = "samples/buildpacks/hello-moon"

[[buildpacks]]
uri = "samples/buildpacks/hello-processes"

[[buildpacks]]
uri = "samples/buildpacks/hello-world"

# Order used for detection
[[order]]
    # This buildpack will display build-time information (as a dependency)
    [[order.group]]
    id = "io.buildpacks.samples.hello-world"
    version = "0.0.1"

    # This buildpack will display build-time information (as a dependant)
    [[order.group]]
    id = "io.buildpacks.samples.hello-moon"
    version = "0.0.1"

    # This buildpack will create a process type "sys-info" to display runtime information
    [[order.group]]
    id = "io.buildpacks.samples.hello-processes"
    version = "0.0.1"

# Stack that will be used by the builder
[stack]
id = "io.buildpacks.samples.stacks.bionic"
# This image is used at runtime
run-image = "cnbs/sample-stack-run:bionic"
# This image is used at build-time
build-image = "cnbs/sample-stack-build:bionic"
```

## BuildPack

BuildPack includes different scripts and configurations to detect and build application. Typical
BuildPack directory layout is:

```
ruby-cnb
├── bin
│   ├── build
│   └── detect
└── buildpack.toml
```

And an example `buildpack.toml`:

```toml
# Buildpack API version
api = "0.2"

# Buildpack ID and metadata
[buildpack]
id = "io.buildpacks.samples.java-maven"
version = "0.0.1"
name = "Sample Java Maven Buildpack"

# Stacks that the buildpack will work with
[[stacks]]
id = "io.buildpacks.samples.stacks.bionic"

[[stacks]]
id = "io.buildpacks.samples.stacks.alpine"
```

## Stack

A Stack provides the buildpack lifecycle with build-time and run-time environments in the form of images.
Stacks are used by builders and are configured through a Builder's configuration file.

In short, Stack is the base image for building Builder image.

# References

- https://buildpacks.io/docs/app-journey/
- https://buildpacks.io/docs/buildpack-author-guide/create-buildpack/
