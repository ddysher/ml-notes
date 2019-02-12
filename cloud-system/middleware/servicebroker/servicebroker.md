<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview (v2)](#overview-v2)
- [Profile](#profile)
- [Takeaways](#takeaways)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview (v2)

The Service Broker API defines an HTTP interface between the services marketplace of a platform and
service brokers. In short:

```
service1 --
           \
service2 --- service broker1
           /                \
service3 --                  \
                              -- platform marketplace
serviceX --                  /
           \                /
serviceY --- service broker2
           /
serviceZ --
```

An example of 'service' is MySQL. A service can have multiple plans, i.e flavor. For example, for
MySQL, it can be different performance and size combination. Service broker manages these services.
It is an HTTP server that implements the service broker API and serves as a server for platform
marketplace (the platform marketplace is the client).

Service broker has synchronous and asynchronous operations. For sync operation, service broker
returns immediately about the provisioned service. For async operation, service broker returns an
operation handler; platform marketplace is responsible to poll a specific endpoint.

# Profile

The Open Service Broker API specification defines a standard HTTP service API; while the optional
profile document defines some best practices when using service broker APIs. For example, if the
platform is "kubernetes", the profile defines the suggested fields in "context", see link below.

# Takeaways

A list of notes while reading the specification:

- All requests contain a version header, e.g. `X-Broker-API-Version: 2.13`. Note the prefix `X-` is
  used in the header.
- Service name (e.g. mysql, redis) is usually used by platforms to present a service to their users.
  It is a common practice to add prefix to a service name by service broker, e.g. "example.com/mysql".
- To execute a request synchronously, the Service Broker needs only return the usual status codes:
  `201 Created` for provision and bind, and `200 OK` for update, unbind, and deprovision.
- If client doesn't support asynchronous operation and a request can only be done asynchronously,
  then the Service Broker SHOULD reject the request with the status code `422 Unprocessable Entity`
  with error code `AsyncRequired`. For normal asynchronous operation, response code is `202 Accepted`.
- An asynchronous response triggers the Platform to poll the endpoint
  ```
  GET /v2/service_instances/:instance_id/last_operation
  ```
  until the Service Broker indicates that the requested operation has succeeded or failed. The
  frequency and maximum duration of polling MAY vary by Platform client. If a Platform  has a max
  polling duration and this limit is reached, the Platform MUST cease polling and the operation
  state MUST be considered failed.
- What provisioning represents varies by service and plan, although there are several common use
  cases. For a MySQL service, provisioning could result in an empty dedicated database server running
  on its own VM or an empty schema on a shared database server. For non-data services, provisioning
  could just mean an account on an multi-tenant SaaS application.
- Orphans can result if the Service Broker does not return a response before a request from the
  Platform times out (typically 60 seconds). Platforms SHOULD initiate orphan mitigation.

# References
- https://github.com/openservicebrokerapi/servicebroker
- https://github.com/openservicebrokerapi/servicebroker/blob/v2.13/spec.md
- https://github.com/openservicebrokerapi/servicebroker/blob/v2.13/profile.md
- https://github.com/openservicebrokerapi/servicebroker/blob/v2.13/diagram.md
- https://github.com/kubernetes-incubator/service-catalog
- file://$HOME/code/projects/platforms/kubernetes/projects/service-catalog/service-catalog.md
