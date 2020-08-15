<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments (v0.23)](#experiments-v023)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

kaniko is a tool to build container images from a Dockerfile, inside a container or Kubernetes
cluster. kaniko can run on multiple platforms, including docker, gVisor or kubernetes. It doesn't
depend on docker daemon, and build container images in Dockerfile completely in userspace.

kaniko is an executor binary, usually compiled in an image called `gcr.io/kaniko-project/executor`.
It's not a system running in any of the platforms.

**Caching**

kaniko by default doesn't provide any caching capability, but users can opt-in caching via flags.
There are two kinds of caches: layers and base images.

Layer caches are saved in remote registry: kaniko will pull the layer if it exists without rebuilding
the layer.

Base image caches will be saved to `/cache` of a warmer image. Users usually mount a persistent
volume to the directory.

<details><summary>warmer image</summary><p>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kaniko-warmer
spec:
  containers:
  - name: kaniko-warmer
    image: gcr.io/kaniko-project/warmer:latest
    args: ["--cache-dir=/cache",
           "--image=gcr.io/google-appengine/debian9"]
    volumeMounts:
      - name: kaniko-secret
        mountPath: /secret
      - name: kaniko-cache
        mountPath: /cache
    env:
      - name: GOOGLE_APPLICATION_CREDENTIALS
        value: /secret/kaniko-secret.json
  restartPolicy: Never
  volumes:
    - name: kaniko-secret
      secret:
        secretName: kaniko-secret
    - name: kaniko-cache
      persistentVolumeClaim:
        claimName: kaniko-cache-claim
```

</p></details></br>

**Security**

kaniko doesn't provide any security features and depends on security capabilities of the container
runtime.

*References*

- https://www.giantswarm.io/blog/container-image-building-with-kaniko

# Experiments (v0.23)

To run kaniko in Kubernetes, we first create a secret to push image:

```
kubectl create secret docker-registry regcred --docker-server=https://index.docker.io/v1/ --docker-username=<username> --docker-password=<password> --docker-email=<email>
```

Then run pod to build a hello-world image directly from github:

```
$ kubectl create -f pod-git.yaml
pod/kaniko-git created

$ kubectl logs kaniko-git
Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
Compressing objects: 100% (4/4), done.
Total 42 (delta 0), reused 0 (delta 0), pack-reused 38
E0627 12:52:43.715607       1 aws_credentials.go:77] while getting AWS credentials NoCredentialProviders: no valid providers in chain. Deprecated.
        For verbose messaging see aws.Config.CredentialsChainVerboseErrors
INFO[0031] Using dockerignore file: /kaniko/buildcontext/.dockerignore
INFO[0031] Retrieving image manifest python:3-alpine
INFO[0037] Retrieving image manifest python:3-alpine
INFO[0043] Built cross stage deps: map[]
INFO[0043] Retrieving image manifest python:3-alpine
INFO[0049] Retrieving image manifest python:3-alpine
INFO[0055] Executing 0 build triggers
INFO[0055] Unpacking rootfs as cmd COPY requirements.txt . requires it.
INFO[0060] WORKDIR /usr/src/app
INFO[0060] cmd: workdir
INFO[0060] Changed working directory to /usr/src/app
INFO[0060] Creating directory /usr/src/app
INFO[0060] Resolving 1 paths
INFO[0060] Taking snapshot of files...
INFO[0060] EXPOSE 8000
INFO[0060] cmd: EXPOSE
INFO[0060] Adding exposed port: 8000/tcp
INFO[0060] COPY requirements.txt .
INFO[0060] Resolving 1 paths
INFO[0060] Taking snapshot of files...
INFO[0060] RUN pip install -qr requirements.txt
INFO[0060] Taking snapshot of full filesystem...
INFO[0061] Resolving 2779 paths
INFO[0061] cmd: /bin/sh
INFO[0061] args: [-c pip install -qr requirements.txt]
INFO[0061] Running: [/bin/sh -c pip install -qr requirements.txt]
INFO[0067] Taking snapshot of full filesystem...
INFO[0068] Resolving 3757 paths
INFO[0068] COPY server.py .
INFO[0068] Resolving 1 paths
INFO[0068] Taking snapshot of files...
INFO[0068] CMD ["python3", "./server.py"]
```

It's also possible to run kaniko with:
- local storage
- object storage bucket
- etc
