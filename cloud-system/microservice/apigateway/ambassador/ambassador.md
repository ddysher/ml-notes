<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concetps](#concetps)
  - [Mapping](#mapping)
  - [Resources](#resources)
  - [Services](#services)
  - [Rewrite Rules](#rewrite-rules)
  - [Modules](#modules)
  - [Consumers](#consumers)
- [How it works](#how-it-works)
- [Reference](#reference)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Ambassador is an API Gateway for microservices built on Envoy. The most highted feature is dynamically
add mapping between public URLs to services running inside a Kubernetes cluster (called self-service).

For example:

```
# Add the service mapping through ambassador, i.e. for all URLs starting with
# "/user", send request to kubernetes service "usersvc".
curl -XPOST -H "Content-Type: application/json" \
     -d '{ "prefix": "/user/", "service": "usersvc" }' \
     http://localhost:8888/ambassador/mapping/user_map

# Now we can do the query.
curl http://localhost:8000/user/
```

Other features includes integrated monitoring, Authentication, etc.

# Concetps

## Mapping

As mentioned above, mapping means URLs to kubernetes services mapping. You can also specify rewrite
rules and modules to be used, i.e.

```
{
  "prefix": <url-prefix>,
  "service": <service-name>,
  "rewrite": <rewrite-as>,
  "modules": <module-dict>
}
```

For rewrite rule, the default rule is to rewrite to "/", e.g. if we match "/user" to "usersvc", then
request like "/user/health" will be passed as "/health" to "usersvc" application. For modules, one
can apply different modules to a match, for example, we can add "authentication" module to the above
match so that all requests to "/user" must be authenticated.

## Resources

To Ambassador, a resource is a group of one or more URLs that all share a common prefix in the URL path.

## Services

A service is exactly the same thing to Ambassador as it is to Kubernetes.

## Rewrite Rules

As mentioned above, URL rewrite when matched.

## Modules

As mentioned above, module is used when matched. Modules let you configure special behaviors for
Ambassador, in ways that may apply to Ambassador as a whole or which may apply only to some mappings.

## Consumers

Consumers represent human end users of Ambassador, and may be required for some modules to function.
For example, the authentication module may require defining consumers to let Ambassador know who's
allowed to authenticate. A consumer is created with a POST request:

```
curl -XPOST -H"Content-Type: application/json" \
     -d<consumer-dict> \
     http://localhost:8888/ambassador/consumer
```

# How it works

For self-service, ambassador uses hot-reload feature of envoy to reload envoy when user creates a
new mapping via admin interface. For modules, at least for authentication module, ambassador listens
on `localhost:5000` and adds a filter to envoy; requests hit envoy and envoy uses ambassador for auth.
Ambassador uses postgres to store information, e.g. consumers.

# Reference

- https://www.getambassador.io/about/why-ambassador
