<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [anchore](#anchore)
- [clair](#clair)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# anchore

The [Anchore Engine](https://github.com/anchore/anchore-engine) is an open source project that
provides a centralized service for inspection, analysis and certification of container images.

For vulnerability data:
> It scans images using vulnerability data (feeds) from OS vendors like Red Hat, Debian or Alpine.
> For non-OS data it uses NVD (National Vulnerability Database), which includes vulnerabilities
> for RPM, Deb, APK as well as Python (PIP), Ruby Gems, etc.

Usage-wise, Anchore includes:
- cli: a command line for performing static analysis
- API: run anchore as an analysis service
- policy: collections of user-defined/pre-made policies, for pre-made policies, anchore provides a policy hub

Architecture-wise, Anchore includes following services:
```
# docker-compose ps
                Name                               Command               State           Ports
-------------------------------------------------------------------------------------------------------
aevolume_anchore-db_1                   docker-entrypoint.sh postgres    Up      5432/tcp
aevolume_engine-analyzer_1              /docker-entrypoint.sh anch ...   Up      8228/tcp
aevolume_engine-api_1                   /docker-entrypoint.sh anch ...   Up      0.0.0.0:8228->8228/tcp
aevolume_engine-catalog_1               /docker-entrypoint.sh anch ...   Up      8228/tcp
aevolume_engine-policy-engine_1         /docker-entrypoint.sh anch ...   Up      8228/tcp
aevolume_engine-simpleq_1               /docker-entrypoint.sh anch ...   Up      8228/tcp
```

*References*

- https://towardsdatascience.com/analyzing-docker-image-security-ed5cf7e93751

# clair

[Clair](https://github.com/quay/clair) is an open source project for the static analysis of
vulnerabilities in application containers. Clair consists of a main analyzer component and a
postgres database. The database is used to store vulnerability data and image features. Here,
feature means anything that present in a filesystem could be an indication of a vulnerability,
e.g. a file or a package.

Functionalities of Clair:
> - In regular intervals, Clair ingests vulnerability metadata from a configured set of sources and stores it in the database.
> - Clients use the Clair API to index their container images; this creates a list of features present in the image and stores them in the database.
> - Clients use the Clair API to query the database for vulnerabilities of a particular image; correlating vulnerabilities and features is done for each request, avoiding the need to rescan images.
> - When updates to vulnerability metadata occur, a notification can be sent to alert systems that a change has occurred.
