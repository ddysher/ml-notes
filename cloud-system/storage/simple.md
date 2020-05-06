<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Noobaa](#noobaa)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Noobaa

[Noobaa](https://www.noobaa.io/) is a project for managing object storage across multiple private
and public clouds. Noobaa itself if not an object store, but rather a management plane: users add
real object store like GCS, S3, etc, then it provides a centralized place to manage all of them.
Noobaa can provide data placement policies like mirror, spread across underline storage.

Noobaa is part of OpenShift object storage product, providing ObjectBucket and ObjectBucketClaim
API similar to Kubernetes PV/PVC.
