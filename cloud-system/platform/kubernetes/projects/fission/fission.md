<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 06/15/2017, alpha*

Fission is a fast serverless framework built on top of kubernetes. It has a pool manager which
manages a pool of pods to receive requests, for each env. There is a router that is used to proxy
traffic backend pods: user functions are loaded to the pod upon first request. Fission doesn't
use thirdparty resources; it has its own etcd to store function, route, env, etc. For example,
the following example will yield this result:

```
$ fission env list
NAME   UID                                  IMAGE
nodejs 367bc93e-5784-4d8b-8e72-995f1fbdd873 fission/node-env

$ fission function list
NAME  UID                                  ENV
hello 3bd0a155-f812-45b5-bee1-ed0eeccd6849 nodejs

$ fission route list
NAME                                 METHOD URL    FUNCTION_NAME FUNCTION_UID
2ac1e880-b36f-4ae6-b088-c665e08d0fb7 GET    /hello hello
```

For more information, ref [fission architecture](https://github.com/fission/fission/blob/0207d13b2323b79fe9caec5d31da3a88f12b840f/Documentation/Architecture.md).

*Updates on 04/07/2018, v0.7.0*

Fission has removed etcd and changes to use TPR (then to CRD), ref: https://github.com/fission/fission/pull/266

*Updates on 11/04/2018, v0.12.0*

As of v0.12.0, fission has following CRDs:
- Function: Describes the contents of the function. A function has references (kind/namespace/name) to environment, secret, configmap, etc.
- Environment: Defines runtime or builder, as well as information around runtime.
- Triggers: One CRD per trigger, HTTPTrigger, TimeTrigger (cron), MessageQueueTrigger, etc.
- Recorder: defines a policy for recording requests and responses.
- CanaryConfig: Canary configuration.
- Package: function-level images.

Fission also supports workflow, ref [fission-workflow](https://github.com/fission/fission-workflows).

*Reference*

- https://kubernetes.io/blog/2017/01/fission-serverless-functions-as-service-for-kubernetes/
- https://medium.com/@natefonseka/kubeless-vs-fission-the-kubernetes-serverless-match-up-41f66611f54d

# Experiment

Installation:

```
$ kubectl create -f http://fission.io/fission.yaml
namespace "fission" created
namespace "fission-function" created
deployment "controller" created
deployment "router" created
service "poolmgr" created
deployment "poolmgr" created
deployment "kubewatcher" created
service "etcd" created
deployment "etcd" created

$ kubectl create -f http://fission.io/fission-nodeport.yaml
service "router" created
service "controller" created

$ export FISSION_URL=http://$(minikube ip):31313
$ export FISSION_ROUTER=$(minikube ip):31314
```

Create an environment in fission, which will be used in poolmgr to create specific deployemnts:

```
# This command will create an environment in fission. An environment is similar to a language runtime.
$ fission env create --name nodejs --image fission/node-env

# fission creates a deployment with 3 pods. This deployment is created from poolmgr.
$ kubectl get pods -n fission-function
NAME                                                              READY     STATUS    RESTARTS   AGE
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv   2/2       Running   0          39m
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr   2/2       Running   0          39m
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462sfxcr   2/2       Running   0          39m

$ kubectl get deployment -n fission-function
NAME                                                   DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4   3         3         3            3           39m

$ kubectl logs -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c fetcher
```

The nodejs container in the pod is listening on 8888, with codepath set to `/userfunc/user`:

```
$ kubectl logs -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c nodejs
npm info it worked if it ends with ok
npm info using npm@4.1.2
npm info using node@v7.7.2
npm info lifecycle fission-nodejs-runtime@0.1.0~prestart: fission-nodejs-runtime@0.1.0
npm info lifecycle fission-nodejs-runtime@0.1.0~start: fission-nodejs-runtime@0.1.0

> fission-nodejs-runtime@0.1.0 start /usr/src/app
> node server.js

Codepath defaulting to  /userfunc/user
Port defaulting to 8888
```

Now we create a function and upload code to fission. We can list it via `function list` command. Note
unlike kubeless, which stores function as thirdparty resources, fission stores functions in etcd. At this
monent, no pod is touched from the pod pool.

```
$ fission function create --name hello --env nodejs --code hello.js

$ fission function list
NAME  UID                                  ENV
hello 3bd0a155-f812-45b5-bee1-ed0eeccd6849 nodejs
```

Now we map `GET /hello` to the new function. Note this also doesn't touch any backend pods; only the
route will be recorded in etcd. As we can see below, all pods doesn't have any user file.

```
$ fission route create --method GET --url /hello --function hello

$ fission route list
NAME                                 METHOD URL    FUNCTION_NAME FUNCTION_UID
2ac1e880-b36f-4ae6-b088-c665e08d0fb7 GET    /hello hello

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462sfxcr -c nodejs sh
# ls /userfunc
node_modules

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr -c nodejs sh
# ls /userfunc
node_modules

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c nodejs sh
# ls /userfunc
node_modules
```

Now run the function by requesting fission router. Fission router will send our request to a backend
pod; the pod is chosen by poolmgr.

```
$ curl http://$FISSION_ROUTER/hello
Hello, world!

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr -c nodejs sh
# ls /userfunc
node_modules  user
# cat /userfunc/user

module.exports = async function(context) {
    return {
        status: 200,
        body: "Hello, world!\n"
    };
}
```
