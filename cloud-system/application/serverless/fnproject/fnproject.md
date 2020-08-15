<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Caveats](#caveats)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

The Fn project is an open-source container-native serverless platform from Oracle.

The core of fn is a component called `fnserver`, which handles CRUD operations for routes and
functions, sync and async function invocation, etc. For each function, fnserver saves the information
into sql database, including request, source code, response, etc. For each invocation of a function,
fnserver will start a container, or if invocation interval is short, it will reuse existing container.
fnserver will clean up idle containers automatically, and containers that have done function execution
but haven't been cleaned up, will enter `Paused` status. The supporting services for `fnserver`
includes:
- SQL: MySQL, sqlite3, Postgres
- Queue: Redis, Kafka
- Registry: Docker Registry

There are two sub-project in fn:
- fn-lb: fn-lb deals with load balancing and intelligent traffic routing. It manages a pool of
  fnservers and routes invocations to these hot functions to ensure optimal performance. If fn-lb
  is running, client interacts with fn-lb instead of fnservers.
- fn-flow: fn-flow is a code-first approach to orchestrate function execution flow by using the Java
  8 CompletableFutures API with methods such as thenApply() or then thenCompose(), etc. No graphical
  tool or lengthy YAML file is required; the composition of functions is done with Java 8 constructs
  only and is therefore easily readable.

# Caveats

Unlike a 'real' serverless platform, in Fn, user uses `fn` command line to build a container and
then push to a registry. Even though everything is wrapped via the cli, user is still exposed to
the concept of container. For similar reasons, Fn's Kubernetes integration is not quite native.

Another difference is that unlike other serverless platform, user code contains full runnable source,
i.e. not just a function. For example:

```go
package main

import (
	...
	fdk "github.com/fnproject/fdk-go"
)

func main() {
	fdk.Handle(fdk.HandlerFunc(myHandler))
}

func myHandler(ctx context.Context, in io.Reader, out io.Writer) {
	...
}
```

# References

- https://hackernoon.com/playing-with-the-fn-project-8c6939cfe5cc
- https://developer.oracle.com/opensource/serverless-with-fn-project
- https://www.n-k.de/2017/10/fnproject-first-impressions.html
