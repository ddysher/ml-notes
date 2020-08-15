<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [kustomize](#kustomize)
- [Experiments (v3.6.1)](#experiments-v361)
  - [Helloworld](#helloworld)
  - [Wordpress](#wordpress)
  - [Loki (kustimze + helm)](#loki-kustimze--helm)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# kustomize

- *Date: 06/04/2020, v3.6.1*

[kustomize](https://kustomize.io/) is a Declarative Application Management tool, which
- Understands Kubernetes API objects and concepts
- Avoid being a template engine like ksonnet, helm, rather, it uses merge, patch to customize configuration

Concepts in kustomize:
- Base
- Overlay
- Kustomization ([kustomization.yaml reference](https://kubectl.docs.kubernetes.io/pages/reference/kustomize.html))
  - Generators
  - Transformers
  - Meta

# Experiments (v3.6.1)

## Helloworld

**Estabilish Base**

Introduction to `Base`:
> A base is a kustomization referred to by some other kustomization. A kustomization refers to the
> `kustomization.yaml` file, or more generally, to the directory containing a `kustomization.yaml`
> file and all the relative file paths.

Any kustomization, including an overlay, can be a base to another kustomization.

```
$ cd helloworld
$ curl -o "./base/#1.yaml" "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/examples/helloWorld/{configMap,deployment,kustomization,service}.yaml"
...
```

A base can be directly applied to Kubernetes, except the `kustomization.yaml` won't be recognized.

```
$ kubectl apply -f ./base
...
```

**Build Base**

Now we can build the base using `kustomize` command. The build process will parse the
`kustomization.yaml`, apply changes, then emit standard Kubernetes resources.

```
$ kustomize build ./base > /tmp/kustomize-hello-world.yaml
```

Here, since we define a `commonLabels` field in `kustomization.yaml`, the generated Kubernetes
resources will all carry the labels.

**Create Overlays**

Introduction to `Overlay`:
> - An overlay is a kustomization that depends on another kustomization.
> - The kustomizations an overlay refers to (via file path, URI or other method) are called bases.
> - An overlay is unusable without its bases.
> - An overlay may act as a base to another overlay.

The overlays directory contains two overlays, which differ in:
- Staging enables a risky feature not enabled in production.
- Production has a higher replica count.
- Web server greetings from these cluster variants will differ from each other.

Now we can build the overlays using `kustomize` command, similar to building base:

```
# ..skip download...

$ kustomize build overlays/staging > /tmp/kustomize-staging.yaml
$ kustomize build overlays/production > /tmp/kustomize-production.yaml
```

**References**

- https://github.com/kubernetes-sigs/kustomize/tree/kustomize/v3.6.1/examples/helloWorld

## Wordpress

**Establish Base for Each Component**

Similar to HelloWorld, but we create base for each component, i.e. MySQL and WordPress:

```
CONTENT="https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/examples/wordpress/wordpress"
curl -o "./wordpress/worldpress/#1.yaml" "$CONTENT/{deployment,service,kustomization}.yaml"

CONTENT="https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/examples/wordpress/mysql"
curl -o "./wordpress/mysql/#1.yaml" "$CONTENT/{deployment,service,secret,kustomization}.yaml"
```

The two bases are just plain Kubernetes resources:

```
$ cat wordpress/kustomization.yaml
resources:
- deployment.yaml
- service.yaml

$ cat mysql/kustomization.yaml
resources:
- deployment.yaml
- service.yaml
- secret.yaml
```

**Establish "Parent" Base and a Patch**

Now we create a base that includes the previous two bases. This allows us to easily create the whole
wordpress application using a single base.

```
cat <<EOF >$DEMO_HOME/kustomization.yaml
resources:
- wordpress
- mysql
namePrefix: demo-
patchesStrategicMerge:
- patch.yaml
EOF
```

For demo purpose, the `patch.yaml` contains a few runtime data that we want to inject into the
containers, i.e.
- Add an initial container to show the mysql service name
- Add environment variable that allow wordpress to find the mysql database

```
$ cat patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
spec:
  template:
    spec:
      initContainers:
      - name: init-command
        image: debian
        command:
        - "echo $(WORDPRESS_SERVICE)"
        - "echo $(MYSQL_SERVICE)"
      containers:
      - name: wordpress
        env:
        - name: WORDPRESS_DB_HOST
          value: $(MYSQL_SERVICE)
        - name: WORDPRESS_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-pass
              key: password
```

**Bind Variables to Kubernetes Objects**

The above patch requires environment variables, we can bind variables using `vars` keyword in
`kustomization.yaml`. The following snippet shows how:

```
cat <<EOF >>$DEMO_HOME/kustomization.yaml
vars:
  - name: WORDPRESS_SERVICE
    objref:
      kind: Service
      name: wordpress
      apiVersion: v1
    fieldref:
      fieldpath: metadata.name
  - name: MYSQL_SERVICE
    objref:
      kind: Service
      name: mysql
      apiVersion: v1
EOF
```

Before running the above snippet, the result of `kustomize build .` is:

```
(truncated)
...
      initContainers:
      - command:
        - echo $(WORDPRESS_SERVICE)
        - echo $(MYSQL_SERVICE)
        image: debian
        name: init-command

```

After the binding, the result is:

```
(truncated)
...
     initContainers:
     - command:
       - echo demo-wordpress
       - echo demo-mysql
       image: debian
       name: init-command
```

**References**

- https://github.com/kubernetes-sigs/kustomize/tree/kustomize/v3.6.1/examples/helloWorld/wordpress

## Loki (kustimze + helm)

Add loki helm repository:

```
$ helm repo add loki https://grafana.github.io/loki/charts
"loki" has been added to your repositories

$ helm repo update
```

Take a look at the resource configurations from loki/loki chart:

```
# Using default values in Values.yaml.
helm template loki -n monitoring loki/loki > loki.yaml

# Set non-default values.
helm template loki loki/loki -n monitoring --set "persistence.enabled=true" --set "persistence.storageClassName=local-storage" > loki.yaml
```

Now we add the above `loki.yaml` as kustomzie base:

```
$ kustomize edit add base loki.yaml

$ ls
kustomization.yaml  loki.yaml

$ cat kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- loki.yaml
```

The problem with `loki.yaml` is that we use local-storage PV to replace emptydir, but still, the
emptydir is whitelisted in PSP, which we can remove. To do this, we patch it with `loki-patch.yaml`:

```
$ kustomize edit add patch loki-patch.yaml

$ cat kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- loki.yaml
patchesStrategicMerge:
- loki-patch.yaml

# Build to see the actual content.
$ kustomize build
...
```

The secretGenerator in kustomization can be used to replace the config set in helm:

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: monitoring
secretGenerator:
- files:
  - loki.yaml=loki-conf.yaml
  name: loki
  behavior: replace
  namespace: monitoring
```
