<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Setters](#setters)
  - [Substitutions](#substitutions)
  - [Functions](#functions)
  - [Blueprints](#blueprints)
- [Workflow](#workflow)
  - [Consumers](#consumers)
  - [Publishers](#publishers)
  - [Ecosystem](#ecosystem)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 04/13/2020, v0.12.0*
- *Date: 06/05/2020, v0.29.0*

[kpt](https://googlecontainertools.github.io/kpt/) is a tool to fetch, display, customize, update,
validate and apply Kubernetes configurations. It is based Git & YAML, which means it works with
existing tools, framework and platforms, namely helm, kustomize, etc. In another word, any solution
which emits configuration can also generate kpt packages (because they are just configuration);
therefore, kpt can be treated as a higher-level package manager on top of configuration management
tools like helm and kustomize.

A list of terminology used in Kpt (and similar tools):
- Resource Configuration: this is the YAML files used to describe Kubernetes resources like Deployment.
  Kpt favors resource configuration (data) rather than templates or DSLs (code),

# Concepts

## [Setters](https://googlecontainertools.github.io/kpt/guides/producer/setters/)

Setters are used to set values to resource configuration: think of it as structured helm values.
Setters provide a solution for **template-free setting or substitution of field values** through
package metadata (OpenAPI). Setters mainly consist of two parts:
- Fields reference setters through OpenAPI definitions specified as line comments, e.g. [helloword-set comment](https://github.com/GoogleContainerTools/kpt/blob/v0.29.0/package-examples/helloworld-set/deploy.yaml#L23)
- OpenAPI definitions are provided through the Kptfile, e.g. [hello-set Kptfile](https://github.com/GoogleContainerTools/kpt/blob/v0.29.0/package-examples/helloworld-set/Kptfile#L7)

## [Substitutions](https://googlecontainertools.github.io/kpt/guides/producer/substitutions/)

Substitutions are similar to setters. Substitutions provide a solution for template-free substitution
of field values built on top of setters. They enable substituting values into part of a field,
including combining multiple setters into a single value.

As an example, users can use substitutions to substitue an image tag, instead of setting the whole
image.

## [Functions](https://googlecontainertools.github.io/kpt/guides/producer/functions/)

Functions are conceptually similar to Kubernetes controllers and validating webhooks. They are
programs which read resources as input, then write resources as output (creating, modifying, deleting,
or validating resources).

As an example, users can use functions to programmatically add namespace value to selected resource
configurations.

## [Blueprints](https://googlecontainertools.github.io/kpt/guides/producer/blueprint/)

Blueprint is not a functional unit in Kpt, instead, it is a pattern for developing reusable,
customizable configuration. reusable,

# Workflow

## Consumers

Consumers means kpt package consumers, the workflow is:
- Fetch a local copy of a remote package
- Modify the local copy
- Either using user-friendly editing commands Or direclty modifying the files with a text editor
- (Optional) Push the local package to a project / team repo (using Git directly)
- (Optional) Automation makes last-mile changes before pushing
- Automation pushes by applying to a cluster

The core commands used in kpt consumers include:
- `kpt pkg`: fetch and update configuration using Git and YAML
- `kpt cfg`: display and modify configuration in command line
- `kpt live`: next-generation of kubectl apply
- `kpt fn`: functions to generate, transform and validate configuration

Following is a typical usages for `kpt pkg`:
1. Fetch package: `kpt pkg get $REPO/package-examples/helloworld-set@v0.3.0 helloworld`
1. Make local changes and commit
1. Merge upstream changes: `kpt pkg update helloworld@v0.5.0 --strategy=resource-merge`
1. Resolve local conflicts

Following is an exmaple of `kpt fun`: run a function to apply labels to all namespaces for resources under `.`:

```
kpt fn run --image gcr.io/kpt-functions/label-namespace . -- label_name=color label_value=orange
```

For `kpt live`, the most notably feature is pruning live resources. In `kubectl apply`, if we apply
resource configurations under a directory and later remove one of the resources and the re-apply,
kubectl will not delete the removed resources in Kubernetes cluster. In Kpt, however, it will save
resources previously applied in a configmap in Kubernetes cluster, and compare the live state with
the newly applied resource configurations to determine which resources are no longer needed.

## Publishers

A kpt package is published as a git subdirectory containing configuration files (YAML). Publishes of
kpt packages can create or generate YAML files however they like using the tool of their choice, e.g.
helm or kustomize.

Publishing a package is done by pushing the git directory (and optionally tagging it with a version).
Multiple packages may exist in a single repo under separate subdirectories.

Publishers work with following
- Init: either manually create a directory or use `kpt pkg init` - it's just a directory of files
- Setters, see above
- Substitutions, see above
- Blueprints
- Variants

## Ecosystem

As mentioned abvoe, Kpt is a package mgmt tool, thus it can natively work with helm, kustomize and
many other solutions that emit configurations. One of the solutions is OAM. OAM includes CRD resources
as well, which Kpt can manage like native Kubernetes resources.

**OAM**

Get/Apply/Update packages from App/Git repositories:

```shell
# Get packages from App/Git Repository.
$ kpt pkg get https://github.com/oam-dev/samples.git/5.OAM_KPT_Demo/repository/sampleapp sampleapp

# Apply the resoruces (custom resources). OAM controller will create Kubernetes resources asynchronously.
$ kubectl apply -f sampleapp/
component.core.oam.dev/example-component created
applicationconfiguration.core.oam.dev/example-appconfig created

$ Update new packages from App/Git Repository.
$ kpt pkg update sampleapp@v0.1.0 --strategy=resource-merge
```

For Application Developer, we can use `kpt cfg create-setters` to create setters, for example:

```
$ kpt cfg create-setter sampleapp/ image nginx:1.16.1 --field "image" --description "use to set image for component" --set-by "sampleapp developer"
```

Setters info created in resource configuration files:

```
$ cat sampleapp/Kptfile
apiVersion: kpt.dev/v1alpha1
kind: Kptfile
metadata:
  name: sampleapp
upstream:
  type: git
  git:
    commit: e929bd53f0ec14c5c5efd4e11443ab892355b8a7
    repo: https://github.com/oam-dev/samples
    directory: /5.OAM_KPT_Demo/repository/sampleapp
    ref: master
openAPI:
  definitions:
    io.k8s.cli.setters.image:
      description: use to set image for component
      x-k8s-cli:
        setter:
          name: image
          value: nginx:1.16.1
          setBy: sampleapp developer

$ cat sampleapp/component.yaml
apiVersion: core.oam.dev/v1alpha2
kind: Component
metadata:
  name: example-component
spec:
  workload:
    apiVersion: core.oam.dev/v1alpha2
    kind: ContainerizedWorkload
    spec:
      containers:
      - name: my-nginx
        image: nginx:1.16.1 # {"$ref":"#/definitions/io.k8s.cli.setters.image"}
        resources:
          limits:
            memory: "200Mi"
        ports:
        - containerPort: 4848
          protocol: "TCP"
        env:
        - name: WORDPRESS_DB_PASSWORD
          value: ""
```
