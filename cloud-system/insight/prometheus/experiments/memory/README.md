<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Container Memory](#container-memory)
  - [Compile](#compile)
  - [Run](#run)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Container Memory

Supplement of blog: https://medium.com/faun/how-much-is-too-much-the-linux-oomkiller-and-used-memory-d32186f29c9d

## Compile

Make sure go version >=1.12, and promethus client_golang is downloaded, then:

```
go build main.go
```

Build the container:

```
docker build -t memtest:v1 .
```

## Run

Run the container with:

```
kubectl run memtest --image=memtest:v1 --limits="memory=128Mi"
```

Notice the value of `container_memory_usage` is about twice of `container_memory_working_set`, and
kubernetes kills the container only when `container_memory_working_set` reaches the limits.
