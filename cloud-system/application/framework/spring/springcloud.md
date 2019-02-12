<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Spring Cloud Netflix](#spring-cloud-netflix)
  - [Overview](#overview-1)
  - [Eureka](#eureka)
  - [Ribbon](#ribbon)
  - [Hystrix](#hystrix)
  - [Archaius](#archaius)
  - [Feign](#feign)
  - [Zuul](#zuul)
- [Spring Cloud Sleuth](#spring-cloud-sleuth)
- [Spring Cloud Config](#spring-cloud-config)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Spring Cloud provides tools for developers to quickly build some of the common patterns in distributed
systems (e.g. configuration management, service discovery, circuit breakers, intelligent routing,
micro-proxy, control bus, one-time tokens, global locks, leadership election, distributed sessions,
cluster state).

Note, Spring Cloud is one of the projects in Spring, which helps development teams build simple,
portable, fast and flexible JVM-based systems and applications; Other projects in Spring are Spring
Batch, Spring Security, Spring Boot, etc.

# Spring Cloud Netflix

## Overview

Spring Cloud Netflix provides Netflix OSS integrations for Spring Boot apps through autoconfiguration
and binding to the Spring Environment and other Spring programming model idioms. With a few simple
annotations you can quickly enable and configure the common patterns inside your application and build
distributed systems with battle-tested Netflix components. The patterns provided include:
- Service Discovery (Eureka)
- Circuit Breaker (Hystrix)
- Intelligent Routing (Zuul) and
- Client Side Load Balancing (Ribbon)

## Eureka

Eureka is used for service discovery in spring cloud. A cluster of eureka servers are setup first to
serve as a central service registry. Application servers register themselves to eureka, and client
discovers them through the so called "vipAddress", e.g. sampleservice.mydomain.net. When querying,
eureka will return all services backing the vipAddress; eureka has built-in client library which can
pick up one from the pool (client-side loadbalancing). Check out the following example and tutorial.

A little bit code browsing shows that client loadbalancing is done at `discovery/DiscoveryClient.java`.
Eureka client (application server) has heatbeat with eureka server, thus eureka knows application
server status and will only return healthy ones.

- https://github.com/Netflix/eureka/tree/master/eureka-examples
- http://www.baeldung.com/spring-cloud-netflix-eureka
- https://spring.io/guides/gs/service-registration-and-discovery/

From eureka 2.0 overview:

> From CAP theorem perspective, Eureka write cluster is an AP system (highly available, and partition
> tolerant). This choice is driven by the primary requirements of a cloud based discovery service.
> In the cloud, especially for large deployments, the failures happen all the time. This could be
> failure of a Eureka server itself, the registered clients or a network partition. Under all those
> circumstances, Eureka remains to be available by providing registry information and accepting new
> registrations from each available node in isolation. Since, Eureka chooses availability, the data
> in such a scenario is not consistent between these nodes. Since this model causes that there is
> always some level of staleness of the registry data, it should be complemented by proper client
> side load balancing and failover mechanisms. In Netflix ecosystem these features are provided by
> Ribbon.

## Ribbon

Ribbon primarily provides client-side load balancing algorithms (think of it as an enhancement for
eureka built-in client load balancing). Load balancers in Ribbon normally get their server lists
from a Netflix Eureka service registry, but can also be static list, etc.

- http://www.baeldung.com/spring-cloud-rest-client-with-netflix-ribbon
- https://spring.io/guides/gs/client-side-load-balancing/

Note that ribbon is in maintenance mode; netflix team has instead started building an RPC solution
on top of gRPC, two main reasons: multi-language support and better extensibility/composability
through request interceptors.

**How loadbalance work in ribbon**

Load balancer is built in ribbon; user can choose which load balancer to use. For example, if we want
"Weighted Round Robin", then we need to run `ResponseTimeWeightedRule`. If client chooses to use it,
then a background thread is running which maintains the weights and returns an appropriate server when
called.

- https://github.com/Netflix/ribbon/wiki/Working-with-load-balancers
- https://github.com/Netflix/ribbon/blob/ff4b5feedc7760337e1f748999187270fd327893/ribbon-loadbalancer/src/main/java/com/netflix/loadbalancer

## Hystrix

Hystrix is a latency and fault tolerance library designed to isolate points of access to remote
systems, services and 3rd party libraries, stop cascading failure and enable resilience in complex
distributed systems where failure is inevitable.

Note Hystrix is a library, not a service, and is mainly used for circuit breaker pattern. Hystrix
also has a nice dashboard to monitor services.

- https://medium.com/netflix-techblog/introducing-hystrix-for-resilience-engineering-13531c1ab362
- https://spring.io/guides/gs/circuit-breaker/
- http://www.baeldung.com/spring-cloud-netflix-hystrix
- https://github.com/Netflix/Hystrix/wiki/How-it-Works

**How circuit breaker pattern works in hystrix**

Hystrix reports successes, failures, rejections, and timeouts to the circuit breaker, which maintains
a rolling set of counters that calculate statistics. It uses these stats to determine when the circuit
should "trip", at which point it short-circuits any subsequent requests until a recovery period
elapses. After this amount of time, the next single request is let through (this is the HALF-OPEN
state). If the request fails, the circuit-breaker returns to the OPEN state for the duration of the
sleep window. If the request succeeds, the circuit breaker transitions to CLOSED again.

## Archaius

Archaius is a library for configuration management. At the heart of Archaius is the concept of Composite
Configuration which is an ordered list of one or more Configurations. Each Configuration can be sourced
from a Configuration Source such as JDBC, REST API, a .properties file etc. Configuration Sources can
optionally be polled at runtime for changes. Client can provide callbacks for handling config changes.
The final value of a property is determined based on the top most Configuration that contains that
property. i.e. If a property is present in multiple configurations, the actual value seen by the
application will be the value that is present in the topmost slot in the hierarchy of Configurations.
The order of the configurations in the hierarchy can be configured.

- https://medium.com/netflix-techblog/announcing-archaius-dynamic-properties-in-the-cloud-bc8c51faf675
- https://jlordiales.me/2014/10/07/configuration-management-with-archaius-from-netflix/

## Feign

Feign is a java to http client binder, a declarative web service client. Feign can integrate with
Hystrix to provide fault tolerance; it can also integrate with Ribbon for client-side load-balancing,
and with eureka for service discovery.

- http://www.baeldung.com/intro-to-feign

## Zuul

Zuul is an edge service that provides dynamic routing, monitoring, resiliency, security, and more.
It is the front door for all requests from devices and web sites to the backend of the Netflix
streaming application. The highlight of Zuul is its filters, but it has a lot of other features,
e.g. Authentication, Load Shedding, etc.

- https://medium.com/netflix-techblog/announcing-zuul-edge-service-in-the-cloud-ab3af5be08ee
- https://spring.io/guides/gs/routing-and-filtering/
- http://instea.sk/2015/04/netflix-zuul-vs-nginx-performance/

# Spring Cloud Sleuth

Spring Cloud Sleuth implements a distributed tracing solution for Spring Cloud, borrowing heavily
from Dapper, Zipkin and HTrace. Once sleuth is added to the CLASSPATH, it automatically generates
trace data. Data collection is a start but the goal is to understand the data, not just collect it.
In order to appreciate the big picture, we need to get beyond individual events. This is where zipkin
comes into play. Zipkin is an open source project that provides mechanisms for sending, receiving,
storing, and visualizing traces. This allows us to correlate activity between servers and get a much
clearer picture of exactly what is happening in our services. To use integration between sleuth and
zipkin, we can simply use annotation "@EnableZipkinStreamServer". Sleuth will stream logs to zipkin.
Note sleuth itself is a library.

- http://cloud.spring.io/spring-cloud-sleuth/
- http://www.baeldung.com/tracing-services-with-zipkin
- http://www.baeldung.com/spring-cloud-sleuth-single-application

# Spring Cloud Config

Spring Cloud Config provides server and client-side support for externalized configuration in a
distributed system. It polls configuration from version controlled system, e.g. gitlab.

- https://spring.io/guides/gs/centralized-configuration/
