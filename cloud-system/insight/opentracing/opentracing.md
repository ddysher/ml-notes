<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Contrib](#contrib)
  - [go-stdlib](#go-stdlib)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 01/20/2018, v1*

OpenTracing is consistent, expressive, vendor-neutral APIs for distributed tracing and context
propagation. The project contains a specification, semantics and language APIs.
- Specification is the most important part of the project, it defines concepts and capabilities
  of opentracing. Tracers that implements the specification includes zipkin, jaeger, appdash, etc;
  there is also a reference implementation called basictracer.
- Semantics comes along with specification, which defines suggested standard tags and logs.
- OpenTracing supports several languages, e.g. Java, Go, Python, Javascript, etc. OpenTracing
  provides libraries for those supported languages.

A couple takeaway points:
- For Inject/Extract, in the absence of data corruption or other errors, the server can get a
  SpanContext instance that belongs to the same trace as the one in the client
- Parent span does not depend on the completion of the child span, for example if the child represents
  a best-effort, fire-and-forget cache write.

For more details, refer to the [tutorial from yurishkuro](https://github.com/yurishkuro/opentracing-tutorial/tree/9b053de60630394a2a179df6c0590a73b1106598).

*References*

- http://opentracing.io/documentation/
- https://github.com/opentracing/specification/blob/1.1/specification.md
- https://github.com/opentracing/specification/blob/1.1/semantic_conventions.md

# Contrib

## [go-stdlib](https://github.com/opentracing-contrib/go-stdlib)

The library has two parts. At server side, it instruments http server via middleware, i.e. it is
the entrypoint for http.ServeHTTP, and wraps user handler with span.
