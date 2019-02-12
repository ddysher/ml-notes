<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment (v2.0.1)](#experiment-v201)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 07/25/2020, v2.0*

> Harbor is an open source trusted cloud native registry project that stores, signs, and scans
> content. Harbor extends the open source Docker Distribution by adding the functionalities
> usually required by users such as security, identity and management. Having a registry closer
> to the build and run environment can improve the image transfer efficiency. Harbor supports
> replication of images between registries, and also offers advanced security features such as
> user management, access control and activity auditing.

Native Components in Harbor:
- Core: the core component that provides apiservice, config/project/quota/retention/scan mgmt, registry driver, etc.
- Portal: a graphical user interface to help users manage images on the Registry.
- Job Service: asynchronous tasks running service for other components/services.
- Log collector: responsible for collecting logs of other modules into a single place.
- GC Controller: manages the online GC schedule settings and start and track the GC progress.

External Components in Harbor:
- Proxy: nginx-based proxy that sits in front of all other services.
- K/V Store: redis-based store that provides caching and temp storage.
- Database: postgre-based relational database to store user, project, policy, etc.
- Registry: the underline docker registry.

Optional External Components in Harbor:
- Chart Museum: 3rd party chart repository server providing helm chart management and access APIs.
- Notary: 3rd party content trust server, responsible for securely publishing and verifying content.
- Clair or Trivy or Anchore: 3rd party image scanning services.

# Experiment (v2.0.1)

Harbor installation without https:

```
# change hostname to externally accessible IP and run
$ sudo ./install.sh
...
```

The installation script will generate a docker-compose file; the components after installation include:

```
$ docker ps
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS                   PORTS                       NAMES
65c408b67e43        goharbor/harbor-jobservice:v2.0.1      "/harbor/entrypoint.…"   2 minutes ago       Up 2 minutes (healthy)                               harbor-jobservice
ca44afbf2660        goharbor/nginx-photon:v2.0.1           "nginx -g 'daemon of…"   2 minutes ago       Up 2 minutes (healthy)   0.0.0.0:80->8080/tcp        nginx
a03427b76ada        goharbor/harbor-core:v2.0.1            "/harbor/entrypoint.…"   2 minutes ago       Up 2 minutes (healthy)                               harbor-core
02b13fcfac94        goharbor/redis-photon:v2.0.1           "redis-server /etc/r…"   2 minutes ago       Up 2 minutes (healthy)   6379/tcp                    redis
d38b0087225e        goharbor/harbor-registryctl:v2.0.1     "/home/harbor/start.…"   2 minutes ago       Up 2 minutes (healthy)                               registryctl
526f9c65cc41        goharbor/registry-photon:v2.0.1        "/home/harbor/entryp…"   2 minutes ago       Up 2 minutes (healthy)   5000/tcp                    registry
a00e3aa1a848        goharbor/harbor-db:v2.0.1              "/docker-entrypoint.…"   2 minutes ago       Up 2 minutes (healthy)   5432/tcp                    harbor-db
eeb8f88234fa        goharbor/harbor-portal:v2.0.1          "nginx -g 'daemon of…"   2 minutes ago       Up 2 minutes (healthy)   8080/tcp                    harbor-portal
4671d7615f54        goharbor/harbor-log:v2.0.1             "/bin/sh -c /usr/loc…"   2 minutes ago       Up 2 minutes (healthy)   127.0.0.1:1514->10514/tcp   harbor-log
```

Additional components will be installed if we add more third-party component, e.g.

```
$ sudo ./install.sh  --with-clair --with-chartmuseum
...

$ docker ps
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS                   PORTS                       NAMES
1e12fd0a2ece        goharbor/clair-adapter-photon:v2.0.1   "/home/clair-adapter…"   2 minutes ago       Up 2 minutes (healthy)   8080/tcp                    clair-adapter
f68326d7ad74        goharbor/clair-photon:v2.0.1           "./docker-entrypoint…"   2 minutes ago       Up 2 minutes (healthy)   6060-6061/tcp               clair
6a33c58f21c3        goharbor/chartmuseum-photon:v2.0.1     "./docker-entrypoint…"   2 minutes ago       Up 2 minutes (healthy)   9999/tcp                    chartmuseum
...
```

To uninstall, just run:

```
$ sudo docker-compose down -v
...

$ sudo rm -rf /data
```

To push images, we can create a demo project in harbor portal. Note the docker daemon needs to add
the host IP to insecure registry:

```
$ docker login 192.168.50.179:80
...

$ docker tag busybox:1.30.1 192.168.50.179:80/demo/busybox:1.30.1
..

# Use port 80 (nginx) instead of 5000; the docker registry runs behind nginx.
$ docker push 192.168.50.179:80/demo/busybox:1.30.1
...
```
