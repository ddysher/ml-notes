<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Roles](#roles)
  - [Workload Definitions](#workload-definitions)
  - [Trait Definition](#trait-definition)
  - [Scope Definition](#scope-definition)
  - [Component](#component)
  - [Trait](#trait)
  - [Application Scopes](#application-scopes)
  - [Application Configurations](#application-configurations)
- [Projects](#projects)
  - [rudr](#rudr)
  - [crossplane](#crossplane)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/31/2020, v1.0.0-alpha2*

[Open Application Model (OAM)](https://oam.dev/) is a platform-agnostic specification for building
cloud native applications. It defines a set of concepts & roles, and an opionioned workflow that
separates the concerns of developers & operators, whilst providing flexibility and clarity. OAM is
a vendor-neutral specification, meaning implementation of it can run anywhere - a unified approach
that works across cloud platforms and edge devices.

For more introduction of OAM:
- [OAM introduction](https://github.com/oam-dev/spec/blob/f7110b62c02263549b463ccacf6d77d8726e9dc1/introduction.md)
- [Example workflow](https://github.com/oam-dev/spec/blob/f7110b62c02263549b463ccacf6d77d8726e9dc1/examples/workflow.md)

Specification of OAM:
- [Full Specification](https://github.com/oam-dev/spec)
- [Catalog of Traits, Workloads, etc](https://github.com/oam-dev/catalog)

# Concepts

The following concepts are based on [v1alpha2 API](https://github.com/oam-dev/spec/blob/f7110b62c02263549b463ccacf6d77d8726e9dc1/design/20200105-spec-v1alpha2-kubernetes-friendly.md).
To simply put, v1alpha2 is more kubernetes-native. It avoids redefining `ComponentSchematic`
(v1alph1 API) for CRD defined in OAM kubernetes runtime, and instead defines `WorkloadDefinition`
API that references to the CRD. Similar design applies to Traint and Scope.

## Roles

**Application Developer**

Application Developer is the person who writes business code and defines application operational
characteristics like required mount path, runtime parameters, etc.

**Application Operator**

Application Operator is responsible to satisfy operational characteristics, and deploy, install,
upgrade applications.

**Infrastructure Operator**

Infrastructure operators deliver value by managing low-level infrastructural components, like
physical machines, public cloud, etc.

## Workload Definitions

A platform that implements OAM supplies a runtime (or runtimes) that can execute components. Each
type of component that can be run by the OAM runtime is represented by a `workloadDefinition`. The
definition is provided by **infrastructure operator**.

There are three different levels of workload definitions:
- core: core workloads in OAM are defined [here](https://github.com/oam-dev/spec/tree/f7110b62c02263549b463ccacf6d77d8726e9dc1/core/workloads).
- standard
- extended

For example, following snippet is the core workload definition of `ContainerizedWorkload`: the
`definitionRef` is a reference to a schema that defines the workload - in kubernetes, the schema
is defined as yet another CRD.

In following section, we'll see an example `Component` using this containerized workload definition:

```yaml
apiVersion: core.oam.dev/v1alpha2
kind: WorkloadDefinition
metadata:
  name: containerizedworkloads.core.oam.dev
spec:
  definitionRef:
    name: containerizedworkloads.core.oam.dev
```

## Trait Definition

A platform that implements OAM defines the traits that are available on that platform using a
`traitDefinition`. The definition is provided by **infrastructure operator**.

Similar to workload definition, there are three different levels of trait definitions:
- core: core traits in OAM are defined [here](https://github.com/oam-dev/spec/tree/f7110b62c02263549b463ccacf6d77d8726e9dc1/core/traits).
- standard: standard traits in OAM are defined [here](https://github.com/oam-dev/spec/tree/f7110b62c02263549b463ccacf6d77d8726e9dc1/standard/traits).
- extended

For example, following snippet is the core trait definition of `ManualScaler`:

```yaml
apiVersion: core.oam.dev/v1alpha2
kind: TraitDefinition
metadata:
  name: manualscalertrait.core.oam.dev
spec:
  appliesToWorkloads:
    - core.oam.dev/v1alpha2.ContainerizedWorkload
  definitionRef:
    name: manualscalertrait.core.oam.dev
```

## Scope Definition

A platform that implements OAM defines the application scopes that are available on that platform
using a `scopeDefinition`.

Similarly, there are three different levels of scope definitions:
- core
- standard: standard scopes in OAM are defined [here](https://github.com/oam-dev/spec/tree/f7110b62c02263549b463ccacf6d77d8726e9dc1/standard/scopes).
- extended

## Component

Components enable developers to declare the operational characteristics of the code they deliver in
infrastructure neutral terms. Apart from not burdening developers with infrastructural concerns, this
frees operators and runtimes to meet a component's infrastructural needs in whatever opinionated
manner they see fit.

A component is composed of the following pieces of information:
- Metadata: Information about the component, primarily directed toward the application operator
- Workload spec: A specification about how to configure this component according to its workload definition
- Parameters: The parameters that can be adjusted during application runtime characteristics.

For example, following is a component of containerized workload, created from application developer:

```yaml
apiVersion: core.oam.dev/v1alpha2
kind: Component
metadata:
  name: frontend
  annotations:
    version: v1.0.0
    description: >
      Sample component schematic that describes the administrative interface for our Twitter bot.
spec:
  workload:
    apiVersion: core.oam.dev/v1alpha2
    kind: ContainerizedWorkload
    metadata:
      name: sample-workload
    spec:
      osType: linux
      containers:
      - name: my-cool-workload
        image: example/very-cool-workload:0.1.2@sha256:verytrustworthyhash
        resources:
          cpu:
            required: 1.0
          memory:
            required: 100MB
        cmd:
        - "bash lscpu"
        ports:
        - name: http
          value: 8080
        env:
        - name: CACHE_SECRET
        livenessProbe:
          httpGet:
            port: 8080
            path: /healthz
        readinessProbe:
          httpGet:
            port: 8080
            path: /healthz
  parameters:
  - name: imageName
    required: false
    fieldPaths:
    - "spec.containers[0].image"
  - name: cacheSecret
    required: true
    fieldPaths:
    - "spec.containers[0].env[0].value"
```

Application operator ferences components inside of Application Configuration, see below.

## Trait

A trait defines a piece of add-on functionality that pertains to the operation of a component. Traits
may be limited to certain workload types, and different OAM implementations may supply or support a
different set of traits. Traits represent features of the system that are operational concerns, not
developer concerns. For example, a developer may know whether or not their component can be scaled
(and so choose a workload type that declares this). But an operator may decide to apply a manual
scaling trait or an autoscaler trait to this component.

A trait is described as:
- Metadata: Information about the trait
- Applies-to list: Enumeration of workloads to which this trait applies
- Definition reference: A reference to a schema that defines the trait

Application operator defines traits inside of Application Configuration, see below.

## Application Scopes

Application scopes provide different ways to group components into applications. Components are added
to scopes by applying the name of the scope as a label on the component. Each scope represents some
associated behavior or functionality. For example, grouping components into a network application
scope would provide network visibility to all components within the scope.

An application scope is described as:
- Metadata: Information about the scope
- Allow overlap: Specifies whether a component can exist in multiple instances of the scope type
- Definition reference: A reference to a schema that defines the scope

Application operator defines scopes inside of Application Configuration, see below.

## Application Configurations

An application configuration is a resource that declares how all parts of an application are to be
instantiated and configured.

An application configuration has the following parts:
- Metadata: Information about the installed application configuration
- Components: A list of components to instantiate and run. Application operators apply traits to those component instances and supply values to parameters defined by the component author here.
- Traits: Setup operational traits
- Scopes: Setup application scopes

```yaml
apiVersion: core.oam.dev/v1alpha2
kind: ApplicationConfiguration
metadata:
  name: my-app-deployment
  annotations:
    version: v1.0.0
    description: "Description of this deployment"
spec:
  components:
    - componentName: my-web-app-component
      parameterValues:
        - name: PARAMETER_NAME
          value: SUPPLIED_VALUE
        - name: ANOTHER_PARAMETER
          value: "AnotherValue"
      traits:
        - name: manualscaler.core.oam.dev
          version: v1
          spec:
            replicaCount: 3
      scopes:
        - scopeRef:
            apiVersion: core.oam.dev/v1alpha2
            kind: NetworkScope
            name: example-vpc-network
```

# Projects

## rudr

[rudr](https://github.com/oam-dev/rudr) is a reference implementation for the initial working draft
of the OAM specification.

## crossplane

[crossplane](https://github.com/oam-dev/rudr) is a platform (kubernetes add-on) that aims to manage
any infrastructure one's applications need directly from Kubernetes. Similar to OAM, crossplane
defines three roles: application developer, application operator and infrastructure operator.
crossplane initially focused on infrastructure operator, and then collaborated with OAM community
to deliver solutions for the two previous roles.

crossplane is supposed to be the standard implementation of OAM based on Kubernetes; installation of
crossplane will create [these CRDs](https://github.com/oam-dev/crossplane-oam-sample/tree/203e2060d87d90d221c9d7f4afc83bff0633c681/charts/crossplane-oam/crds).
- The core types of OAM is defined in `core.oam.dev` prefix, including:
  - three definitions: `core.oam.dev_scopedefinitions`, `core.oam.dev_traitdefinitions` and `core.oam.dev_workloaddefinitions`
  - other core types, e.g. `core.oam.dev_applicationconfigurations`, `core.oam.dev_components`, etc
- The crossplane extended workloads, e.g. `workload.crossplane.io_kubernetesapplications`, `workload.crossplane.io_kubernetestargets`, etc
