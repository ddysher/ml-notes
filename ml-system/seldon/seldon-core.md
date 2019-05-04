<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
- [Terminology](#terminology)
- [Experiments](#experiments)
  - [Installation](#installation)
  - [Model: step1 wrap prediction model](#model-step1-wrap-prediction-model)
  - [Model: step2 define runtime deployment graph](#model-step2-define-runtime-deployment-graph)
  - [Model: step3 deploy deployment graph](#model-step3-deploy-deployment-graph)
  - [Model: more examples](#model-more-examples)
  - [Route: epsilon greedy example](#route-epsilon-greedy-example)
  - [Transformer: mean transformer example](#transformer-mean-transformer-example)
  - [All in once: advanced graph <-- important](#all-in-once-advanced-graph----important)
  - [Misc: istio](#misc-istio)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 07/08/2018, v0.2.0*

Seldon Core is an open source platform for deploying machine learning models on Kubernetes. Seldon
now only cares about model serving, the goals are:
- Allow data scientists to create models using any machine learning toolkit or programming language.
- Expose machine learning models via REST and gRPC automatically when deployed for easy integration into business apps that need predictions.
- Allow complex runtime inference graphs to be deployed as microservices.
- Handle full lifecycle management of the deployed model.

# Components

Components of selcon-core:

- API Frontend: Frontend of seldon-core, can be replaced by ambassador.
- Cluster Manager: Manages SeldonDeployment CRD
- Core Builder: N/A
- Engine: Implementation of deployment strategy
- Redis: N/A

# Terminology

Below is a list of terminologies found in seldon:
- Model: A service to return predictions.
- Router: A service to route requests to one of its children and receive feedback rewards for them.
  User can use custom router implementation, or use existing implementation, e.g. ABTesting, see
  PredictiveUnitImplementation.
- Combiner: A service to combine reponses from its children into a single response.
- Transformer: A service to transform its input.
- Output_Transformer: A service to transform the response from its child.
- Serving: seldon-core has its own serving (prediction, etc) component and API. For example, in python, it uses Flask to serve rest endpoint.

Implementation of built-in router, combiner, etc, can be found at [here](https://github.com/SeldonIO/seldon-core/tree/v0.2.0/engine/src/main/java/io/seldon/engine).

# Experiments

## Installation

https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/install.md

Install helm:
```
$ kubectl -n kube-system create sa tiller
$ kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
$ helm init --service-account tiller
```

Install seldon-core via helm:

```
$ https_proxy=127.0.0.1:8123 helm install seldon-core-crd --name seldon-core-crd --repo https://storage.googleapis.com/seldon-charts
NAME:   seldon-core-crd
LAST DEPLOYED: Sat Jul  7 21:18:08 2018
NAMESPACE: default
STATUS: DEPLOYED

RESOURCES:
==> v1beta1/CustomResourceDefinition
NAME                                         AGE
seldondeployments.machinelearning.seldon.io  1s


NOTES:
NOTES: TODO

$ https_proxy=127.0.0.1:8123 helm install seldon-core --name seldon-core --repo https://storage.googleapis.com/seldon-charts
NAME:   seldon-core
LAST DEPLOYED: Sat Jul  7 21:20:30 2018
NAMESPACE: default
STATUS: DEPLOYED

RESOURCES:
==> v1/ServiceAccount
NAME    SECRETS  AGE
seldon  1        0s

==> v1/RoleBinding
NAME    AGE
seldon  0s

==> v1/Pod(related)
NAME                    READY  STATUS             RESTARTS  AGE
redis-75c969d887-9gxbb  0/1    ContainerCreating  0         0s

==> v1beta1/Deployment
NAME                    DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
seldon-apiserver        1        0        0           0          0s
seldon-cluster-manager  1        0        0           0          0s
redis                   1        1        1           0          0s

==> v1/Service
NAME              TYPE       CLUSTER-IP  EXTERNAL-IP  PORT(S)                        AGE
seldon-apiserver  NodePort   10.0.0.42   <none>       8080:31607/TCP,5000:32741/TCP  0s
redis             ClusterIP  10.0.0.31   <none>       6379/TCP                       0s


NOTES:
NOTES: TODO
```

Final outputs:

```
$ kubectl get pods --all-namespaces
NAMESPACE     NAME                                      READY     STATUS    RESTARTS   AGE
default       redis-75c969d887-9gxbb                    1/1       Running   0          13h
default       seldon-apiserver-f8cd7bf54-wgwsg          1/1       Running   0          13h
default       seldon-cluster-manager-66cf946f95-fnsc5   1/1       Running   0          13h
kube-system   kube-dns-659bc9899c-prljw                 3/3       Running   0          17h
kube-system   tiller-deploy-5c688d5f9b-jx2lg            1/1       Running   0          17h
```

## Model: step1 wrap prediction model

First, we need to wrap our model into a runnable container; this is best done using redhat source-to-image
(for python), e.g.
```
s2i build https://github.com/SeldonIO/seldon-core --context-dir=wrappers/s2i/python/test/model-template-app seldonio/seldon-core-s2i-python2 seldon-core-template-model
```

The command will create a docker image named "seldon-core-template-model" that is ready to be run.
For more information, see https://github.com/SeldonIO/seldon-core/tree/v0.2.0/docs/wrappers

## Model: step2 define runtime deployment graph

Seldon provides a lot deployment strategy to make our model prediction effective, like A/B testing,
prediction combination, etc. For more information, see:
- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/crd/readme.md
- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/reference/seldon-deployment.md

## Model: step3 deploy deployment graph

Once the graph is defined, we can create a seldon deployment crd. For example, we can create a very
simple seldon deployment for the above template model:

```
$ kubectl create -f simple-seldon-deployment.json

$ kubectl get pods
NAME                                                              READY     STATUS    RESTARTS   AGE
redis-75c969d887-9gxbb                                            1/1       Running   0          13h
seldon-apiserver-f8cd7bf54-wgwsg                                  1/1       Running   0          13h
seldon-cluster-manager-66cf946f95-fnsc5                           1/1       Running   0          13h
test-deployment-fx-market-predictor-classifier-0-6c87cfb8fpj586   1/1       Running   0          1m
test-deployment-fx-market-predictor-svc-orch-744f5cf895-cf5hx     0/1       Running   0          1m

$ kubectl get svc
NAME                                             TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                         AGE
kubernetes                                       ClusterIP   10.0.0.1     <none>        443/TCP                         17h
redis                                            ClusterIP   10.0.0.31    <none>        6379/TCP                        13h
seldon-apiserver                                 NodePort    10.0.0.42    <none>        8080:31607/TCP,5000:32741/TCP   13h
test-deployment                                  ClusterIP   10.0.0.58    <none>        8000/TCP,5001/TCP               1m
test-deployment-fx-market-predictor-classifier   ClusterIP   10.0.0.59    <none>        9000/TCP                        1m
```

Based on wrapper source code, we can query endpoint via:

```
$ curl -d 'json={"data":{"names":["a","b"],"tensor":{"shape":[2,2],"values":[0,0,1,1]}}}' -H "Content-Type: application/x-www-form-urlencoded" -X POST 10.0.0.59:9000/predict
{
  "data": {
    "names": [
      "t:0",
      "t:1"
    ],
    "tensor": {
      "shape": [
        2,
        2
      ],
      "values": [
        0,
        0,
        1,
        1
      ]
    }
  }
}
```

For more information, see:
- https://github.com/SeldonIO/seldon-core/blob/3ee8f635b96792146e4abe42febcb855302ef574/wrappers/python/microservice.py#L51
- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/reference/internal-api.md

## Model: more examples

- https://github.com/SeldonIO/seldon-core/tree/v0.2.0/examples/models

## Route: epsilon greedy example

- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/notebooks/epsilon_greedy_gcp.ipynb
- https://github.com/SeldonIO/seldon-core/tree/v0.2.0/examples/routers/epsilon_greedy

## Transformer: mean transformer example

- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/examples/transformers/mean_transformer

## All in once: advanced graph <-- important

- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/notebooks/advanced_graphs.ipynb

## Misc: istio

- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/examples/istio/
