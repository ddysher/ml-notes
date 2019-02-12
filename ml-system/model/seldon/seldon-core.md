<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Terminology](#terminology)
- [Architecture](#architecture)
  - [Components](#components)
  - [APIs](#apis)
- [Experiments (v0.2.0)](#experiments-v020)
  - [Installation](#installation)
  - [Basic Serving](#basic-serving)
  - [More examples](#more-examples)
- [Experiments (v1.2.1)](#experiments-v121)
  - [Installation](#installation-1)
  - [Basic Serving](#basic-serving-1)
  - [Random ABTest](#random-abtest)
  - [Feature Transformer](#feature-transformer)
  - [Python Module](#python-module)
- [Projects](#projects)
  - [alibi](#alibi)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 07/08/2018, v0.2.0*
- *Date: 07/22/2020, v1.2.1*

Seldon Core is an open source platform for deploying machine learning models on Kubernetes. Seldon
Core focuses on model serving, the goals are:
- Allow data scientists to create models using any machine learning toolkit or programming language.
- Expose machine learning models via REST and gRPC automatically when deployed.
- Allow complex runtime inference graphs to be deployed as microservices.
- Handle full lifecycle management of the deployed model.

As of v1.2.1, the feature-set expands to:
- Easy way to containerise ML models using our language wrappers or pre-packaged inference servers.
- Out of the box endpoints which can be tested through Swagger UI, Seldon Python Client or Curl / GRPCurl
- Cloud agnostic and tested on AWS EKS, Azure AKS, Google GKE, Alicloud, Digital Ocean and Openshift.
- Powerful and rich inference graphs made out of predictors, transformers, routers, combiners, and more.
- A standardised serving layer across models from heterogeneous toolkits and languages.
- Advanced and customisable metrics with integration to Prometheus and Grafana.
- Full auditability through model input-output request logging integration with Elasticsearch.
- Microservice tracing through integration to Jaeger for insights on latency across microservice hops.

# Terminology

List of terminologies found in Seldon:
- Model: A service to return predictions.
- Router: A service to route requests to one of its children and receive feedback rewards for them. User can use custom router implementation, or use existing implementation, e.g. ABTesting, see PredictiveUnitImplementation.
- Combiner: A service to combine reponses from its children into a single response.
- Transformer: A service to transform its input.
- Output_Transformer: A service to transform the response from its child.

Implementation of built-in router, combiner, etc, can be found at [here@v0.2.0](https://github.com/SeldonIO/seldon-core/tree/v0.2.0/engine/src/main/java/io/seldon/engine)
and [here@v1.2.1](https://github.com/SeldonIO/seldon-core/tree/v1.2.1/executor).

# Architecture

## Components

Components of selcon-core@0.2.0:

- API Frontend: Frontend of seldon-core, can be replaced by ambassador.
- Cluster Manager: Manages SeldonDeployment CRD
- Core Builder: N/A
- Engine: Implementation of deployment strategy
- Redis: N/A

As of seldon-core@v1.2.1, the components changed quite a bit, but the core concepts remain the same:
- `seldon-controller-manager` is the only long-running component, which manages seldon deployment;
- `executor` is used for orchestration purpose (previously called engine); it runs as a sidecar of user models;
- `s2i builder` wrapps models using seldon's python (or other language) modules;
- `servers` include sklearn server, tfserving, xgboost server, triton, etc;
  - for sklearn, xgboost, etc, seldon uses `s2i` to build image;
  - for tfserver triton, etc, seldon uses official images.

## APIs

Seldon provides two different kinds of **external** APIs: seldon protocol and tfserving protocol.
The tfserving protocol use official tfserving APIs. The seldon protocol exposes three main
**external** APIs, i.e (for rest):
- Prediction: `POST /api/v1.0/predictions`
- Feedback: `POST /api/v1.0/feedback`
- Metadata:
  - Graph level: `GET /api/v1.0/metadata`
  - Model level: `GET /api/v1.0/metadata/{MODEL_NAME}`

When using seldon protocol, different components, i.e. Model, Router, Combiner, Transformer and
Output_Transformer can use an internal microservice APIs to communicate. Apart from `/predict`,
which is similar to external API, internal APIs include `/combine`, `/transform-output`, etc.

The internal API has two levels: the REST/gRPC level and the language (python, java, etc) level.
For language API, seldon uses `s2i` to build an image which can serve REST/gRPC API, using common
framework like Flask (python), Spring Boot (java), etc.

> To add microservice components to a runtime prediction graph users need to create service that
> respects the internal API. The API provides a default service for each type of component within
> the system.

However, when using tfserving protocol, Combining and Routing are not supported. Note that we can
use `tfserving` server with seldon protocol, in which case the official tfserving image will be
used, and seldon will run a proxy sidecar along with the model to translate seldon API to tfserving
API.

# Experiments (v0.2.0)

## Installation

Follow [installation guide](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/install.md).

Install helm:

```
$ kubectl -n kube-system create sa tiller
$ kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
$ helm init --service-account tiller
```

Install seldon-core via helm:

<details><summary>Install via helm</summary><p>

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

</p></details></br>

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

## Basic Serving

**Step1: wrap prediction model**

First, we need to wrap our model into a runnable container; this is best done using redhat source-to-image
(for python), e.g.
```
s2i build https://github.com/SeldonIO/seldon-core --context-dir=wrappers/s2i/python/test/model-template-app seldonio/seldon-core-s2i-python2 seldon-core-template-model
```

The command will create a docker image named "seldon-core-template-model" that is ready to be run,
see [wrappers](https://github.com/SeldonIO/seldon-core/tree/v0.2.0/docs/wrappers).

**Step2: define runtime deployment graph**

Seldon provides a lot deployment strategy to make our model prediction effective, like A/B testing,
prediction combination, etc. For more information, see:
- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/crd/readme.md
- https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/reference/seldon-deployment.md

**Step3 deploy deployment graph**

Once the graph is defined, we can create a seldon deployment CRD. For example, we can create a very
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
- [microservice.py](https://github.com/SeldonIO/seldon-core/blob/3ee8f635b96792146e4abe42febcb855302ef574/wrappers/python/microservice.py#L51)
- [internal api](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/docs/reference/internal-api.md)

## More examples

- [Model serving](https://github.com/SeldonIO/seldon-core/tree/v0.2.0/examples/models)
- [Route: epsilon greedy notebook](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/notebooks/epsilon_greedy_gcp.ipynb)
- [Route: epsilon greedy example]( https://github.com/SeldonIO/seldon-core/tree/v0.2.0/examples/routers/epsilon_greedy)
- [Transformer: mean transformer example](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/examples/transformers/mean_transformer)
- [All in once: advanced graph <-- **important**](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/notebooks/advanced_graphs.ipynb)
- [seldon with istio](https://github.com/SeldonIO/seldon-core/blob/v0.2.0/examples/istio/)

# Experiments (v1.2.1)

## Installation

Install istio via istioctl:

```
$ curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.6.5 sh -
...

# If there is no loadbalancer, we can set `istio-ingressgateway` to `NodePort`.
$ istioctl install --set profile=demo --set values.gateways.istio-ingressgateway.type=NodePort
...

$ kubectl get service -n istio-system
NAME                        TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                                      AGE
istio-ingressgateway        NodePort       10.0.0.38    <none>        15020:30505/TCP,80:31945/TCP,443:30371/TCP,31400:32046/TCP,15443:32749/TCP   22m
...
```

Create a istio gateway for seldon:

```
kubectl apply -f - << END
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: seldon-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway # use istio default controller
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
END
```

Then install seldon-core:

```
$ kubectl create namespace seldon-system
namespace/seldon-system created

$ helm install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --namespace seldon-system \
    --set istio.enabled=true
    # You can set ambassador instead with --set ambassador.enabled=true
...
```

After all resources are created, the running pods are:

```
$ kubectl get pods --all-namespaces
NAMESPACE       NAME                                               READY   STATUS    RESTARTS   AGE
istio-system    grafana-5dc4b4676c-jxwpq                           1/1     Running   0          6m45s
istio-system    istio-egressgateway-6b879688d7-hlxd9               1/1     Running   0          6m46s
istio-system    istio-ingressgateway-7fcd6df8f9-ljj8w              1/1     Running   0          6m46s
istio-system    istio-tracing-8584b4d7f9-5zpck                     1/1     Running   0          6m45s
istio-system    istiod-94db55459-mt2ww                             1/1     Running   0          6m50s
istio-system    kiali-6f457f5964-x2htp                             1/1     Running   0          6m45s
istio-system    prometheus-547b4d6f8c-xlxsp                        2/2     Running   0          6m45s
kube-system     kube-dns-547db76c8f-gkzx6                          3/3     Running   0          7m13s
seldon-system   seldon-controller-manager-8475c8f894-vbgsd         1/1     Running   0          5m35s
seldon          iris-model-default-0-classifier-78954f446d-xs5lw   2/2     Running   0          5m
```

## Basic Serving

Create a single demo model using sklearn server:

```
$ kubectl create namespace seldon
...

$ kubectl apply -f - << END
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: iris-model
  namespace: seldon
spec:
  name: iris
  predictors:
  - graph:
      implementation: SKLEARN_SERVER
      modelUri: gs://seldon-models/sklearn/iris
      name: classifier
    name: default
    replicas: 1
END
seldondeployment.machinelearning.seldon.io/iris-model created
```

Under the hood, seldon will create a Pod running the iris model classifier, as well as creating
service and istio resources. The Pod contains one init container and two regular containers
- init container `classifier-model-initializer` loads the model
- one regular container `classifier` runs the model and serve predictions
- one regular contaiiner `seldon-container-engine` runs seldone engine for advanced serving capabilities

```
$ kubectl get pods -n seldon
NAMESPACE       NAME                                               READY   STATUS    RESTARTS   AGE
seldon          iris-model-default-0-classifier-78954f446d-xs5lw   2/2     Running   0          5m

$ kubectl get svc -n seldon
NAME                            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
iris-model-default              ClusterIP   10.0.0.18    <none>        8000/TCP,5001/TCP   15m
iris-model-default-classifier   ClusterIP   10.0.0.111   <none>        9000/TCP            15m

$ kubectl get virtualservices.networking.istio.io -n seldon
NAMESPACE   NAME              GATEWAYS                        HOSTS   AGE
seldon      iris-model-grpc   [istio-system/seldon-gateway]   [*]     15m
seldon      iris-model-http   [istio-system/seldon-gateway]   [*]     15m

$ kubectl get destinationrules.networking.istio.io -n seldon
NAME                 HOST                 AGE
iris-model-default   iris-model-default   15m
```

Summary of IP and port information:
- service `iris-model-default-classifier` exposes model API, has IP `10.0.0.111` and port `9000`
- service `iris-model-default` exposes the engine API, has IP `10.0.0.18` and port `8000` (http) and `5001` (grpc)
- service `istio-ingressgateway` exposes a gateway service, has IP `10.0.0.38`, and NodePort `31945` (http), etc

Now we can start querying the endpoints:
```
# This will directly query the model API.
$ curl -X POST http://10.0.0.111:9000/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
{"data":{"names":["t:0","t:1","t:2"],"ndarray":[[0.0006985194531162841,0.003668039039435755,0.9956334415074478]]},"meta":{}}

# This will go through seldon engine to query the model API (seldon engine will proxy to "localhost:9000".
$ curl -X POST http://10.0.0.18:8000/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
{"data":{"names":["t:0","t:1","t:2"],"ndarray":[[0.0006985194531162841,0.003668039039435755,0.9956334415074478]]},"meta":{}}

# This will go through istio ingressgateway and seldon engine to query the model API.
# Path is rewrite from "seldon/<model_namespace>/<model_name>" to "/" in istio ingressgateway.
$ curl -X POST http://127.0.0.1:31945/seldon/seldon/iris-model/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
{"data":{"names":["t:0","t:1","t:2"],"ndarray":[[0.0006985194531162841,0.003668039039435755,0.9956334415074478]]},"meta":{}}
```

Followign is a detailed list of resources configurations, note that:
- `SeldonDeployment` contains a status field with all the connection information;
- The images used here are all pre-defined, esp. serving container `seldonio/sklearnserver_rest:1.2.1`

<details><summary>More resources configurations</summary><p>

```
$ kubectl get seldondeployments.machinelearning.seldon.io -n seldon iris-model -o yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"machinelearning.seldon.io/v1","kind":"SeldonDeployment","metadata":{"annotations":{},"name":"iris-model","namespace":"seldon"},"spec":{"name":"iris","predictors":[{"graph":{"implementation":"SKLEARN_SERVER","modelUri":"gs://seldon-models/sklearn/iris","name":"classifier"},"name":"default","replicas":1}]}}
  creationTimestamp: "2020-07-22T14:43:29Z"
  generation: 1
  name: iris-model
  namespace: seldon
  resourceVersion: "3033"
  selfLink: /apis/machinelearning.seldon.io/v1/namespaces/seldon/seldondeployments/iris-model
  uid: 0809da5a-99d2-4622-a94e-bc88fff1c1ba
spec:
  name: iris
  predictors:
  - componentSpecs:
    - metadata:
        creationTimestamp: "2020-07-22T14:43:29Z"
      spec:
        containers:
        - image: seldonio/sklearnserver_rest:1.2.1
          name: classifier
          ports:
          - containerPort: 6000
            name: metrics
            protocol: TCP
          resources: {}
          volumeMounts:
          - mountPath: /etc/podinfo
            name: seldon-podinfo
    engineResources: {}
    graph:
      endpoint:
        service_host: localhost
        service_port: 9000
        type: REST
      implementation: SKLEARN_SERVER
      modelUri: gs://seldon-models/sklearn/iris
      name: classifier
      type: MODEL
    labels:
      version: default
    name: default
    replicas: 1
    svcOrchSpec: {}
status:
  address:
    url: http://iris-model-default.seldon.svc.cluster.local:8000/api/v1.0/predictions
  deploymentStatus:
    iris-model-default-0-classifier:
      availableReplicas: 1
      replicas: 1
  replicas: 1
  serviceStatus:
    iris-model-default:
      grpcEndpoint: iris-model-default.seldon:5001
      httpEndpoint: iris-model-default.seldon:8000
      svcName: iris-model-default
    iris-model-default-classifier:
      httpEndpoint: iris-model-default-classifier.seldon:9000
      svcName: iris-model-default-classifier
  state: Available


$ kubectl get destinationrules.networking.istio.io -n seldon iris-model-default -o yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  creationTimestamp: "2020-07-23T00:19:25Z"
  generation: 1
  name: iris-model-default
  namespace: seldon
  ownerReferences:
  - apiVersion: machinelearning.seldon.io/v1
    blockOwnerDeletion: true
    controller: true
    kind: SeldonDeployment
    name: iris-model
    uid: 3d900931-2fbd-46bb-90ee-9c3fae340472
  resourceVersion: "1537"
  selfLink: /apis/networking.istio.io/v1beta1/namespaces/seldon/destinationrules/iris-model-default
  uid: 60d4cd3f-075a-4b7c-a746-c69b6130d16e
spec:
  host: iris-model-default
  subsets:
  - labels:
      version: default
    name: default


$ kubectl get virtualservices.networking.istio.io -n seldon iris-model-http -o yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  creationTimestamp: "2020-07-23T00:19:24Z"
  generation: 1
  name: iris-model-http
  namespace: seldon
  ownerReferences:
  - apiVersion: machinelearning.seldon.io/v1
    blockOwnerDeletion: true
    controller: true
    kind: SeldonDeployment
    name: iris-model
    uid: 3d900931-2fbd-46bb-90ee-9c3fae340472
  resourceVersion: "1533"
  selfLink: /apis/networking.istio.io/v1beta1/namespaces/seldon/virtualservices/iris-model-http
  uid: 4f7e6bab-6000-4f11-83fc-2187c7bdd245
spec:
  gateways:
  - istio-system/seldon-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /seldon/seldon/iris-model/
    rewrite:
      uri: /
    route:
    - destination:
        host: iris-model-default
        port:
          number: 8000
        subset: default
```

</p></details></br>

Similarly, we can create a tfserving model (minimal_tf.yaml); the main difference is that tfserving
will run a seldon proxy server, while sklearn's server (built by seldon) natively supports seldon
internal API. However, we can ask seldon to use tfserving as our external API (minial_tf_protocol.yaml),
thus there will be no proxy server.

```
$ kubectl get pods -n seldon
NAME                                                              READY   STATUS    RESTARTS   AGE
rest-tfserving-model-0-halfplustwo-7fc9d487fc-tgx4d               2/2     Running   0          2m55s
tfserving-default-0-mnist-model-687bf8fb87-4jb5v                  3/3     Running   0          3h16m
...
```

## Random ABTest

Seldon's java-based engine (now deprecated in favor of golang-based executor) contains different
predictive implementations, following is an example of random abtest.

Create the seldon deployment:

```
$ kubectl apply -f 2.randome_db_test.yaml
...

$ kubectl get pods -n seldon
NAME                                                       READY   STATUS    RESTARTS   AGE
random-abtest-abtest-0-classifier-1-5859bf58bf-cpgxg       2/2     Running   0          5m36s
random-abtest-abtest-1-classifier-2-5b845dbc5c-rwz4f       1/1     Running   0          5m36s

$ kubectl get service -n seldon
NAME                                            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
random-abtest-abtest                            ClusterIP   10.0.0.151   <none>        8000/TCP,5001/TCP   5m11s
random-abtest-abtest-classifier-1               ClusterIP   10.0.0.210   <none>        9000/TCP            5m38s
random-abtest-abtest-classifier-2               ClusterIP   10.0.0.39    <none>        9001/TCP            5m38s

$ kubectl get endpoints -n seldon
NAME                                          ENDPOINTS                           AGE
random-abtest-abtest                          172.17.0.13:8000,172.17.0.13:8000   10s
random-abtest-abtest-classifier-1             172.17.0.13:9000                    38s
random-abtest-abtest-classifier-2             172.17.0.14:9001                    38s

$ kubectl get virtualservices.networking.istio.io -n seldon
NAME                      GATEWAYS                        HOSTS   AGE
random-abtest-grpc        [istio-system/seldon-gateway]   [*]     9m6s
random-abtest-http        [istio-system/seldon-gateway]   [*]     9m6s
```

Note that the first random-abtest pod contains two containers while the second one has only one
container. The additional container in first pod is the seldon executor. As shown above, both
`random-abtest-abtest` and `random-test-abtest-classifier-1` endpoints select the same Pod.

As before, we can query the serving via service endpoint `randome-abtest-abtest`, but this time,
executor will send request to two different models at random.

```
# via service endpoint.
$ curl -X POST http://10.0.0.151:8000/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[0]] } }'
...

# via ingress gateway.
$ curl -X POST http://127.0.0.1:31945/seldon/seldon/random-abtest/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[0]] } }'
```

## Feature Transformer

Seldon supports transformer (and out_transformer). Similarly, transformer is a node in the inference graph.

First, we need to build a model transformer:

```
# under 'feature-transform' directory.
$ s2i build . seldonio/seldon-core-s2i-python3:1.2.1 mean_transformer:1.2.1
...
```

Then run the seldon deployment:

```
$ kubectl apply -f 3.feature_transform.yaml
seldondeployment.machinelearning.seldon.io/feature-transformer created

$ kubectl get pods -n seldon
NAME                                                              READY   STATUS    RESTARTS   AGE
feature-transformer-transformer-0-classifier-transformer-76qdzm   3/3     Running   0          43s

$ kubectl get service -n seldon
NAME                                          TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
feature-transformer-transformer               ClusterIP   10.0.0.153   <none>        8000/TCP,5001/TCP   19s
feature-transformer-transformer-classifier    ClusterIP   10.0.0.110   <none>        9000/TCP            47s
feature-transformer-transformer-transformer   ClusterIP   10.0.0.130   <none>        9001/TCP            47s

$ kubectl get endpoints -n seldon
NAME                                          ENDPOINTS                           AGE
feature-transformer-transformer               172.17.0.11:8000,172.17.0.11:8000   45s
feature-transformer-transformer-classifier    <none>                              73s
feature-transformer-transformer-transformer   172.17.0.11:9001                    73s
```

Query the model with transformer:

```
# via service endpoint.
$ curl -X POST http://10.0.0.31:8000/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
{"data":{"names":["proba"],"ndarray":[[0.0819105771553252]]},"meta":{}}

# via ingress gateway.
$ curl -X POST http://127.0.0.1:31945/seldon/seldon/iris-model/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
{"data":{"names":["t:0","t:1","t:2"],"ndarray":[[0.0006985194531162841,0.003668039039435755,0.9956334415074478]]},"meta":{}}
```

Note here transformer and classifier runs in the same Pod, while in the above ABTest example, the
two classifiers run in different Pod.

## Python Module

The example follows the [blog](https://becominghuman.ai/seldon-inference-graph-pipelined-model-serving-211c6b095f62),
where three models are defined using seldon-core's python module. The python module's use case is
when using the out-of-box serving implementations (e.g. sklearn-server, tf-serving, etc) are not
enough when running custom models. Seldon provides [APIs](https://docs.seldon.io/projects/seldon-core/en/latest/python/python_component.html)
for the python module class.

Build each of the model using `s2i` (under 'sentiment-pipeline' directory) and create a seldon
deployment, then we can query the three models, which is called in sequence.

```
$ kubectl apply -f 3.sentiment_pipeline.yaml
...

$ kubectl get pods -n seldon
NAME                                                       READY   STATUS    RESTARTS   AGE
seldon-1e1450367213fb62a0dbd642b6b031e0-858f4f98fb-kss8w   4/4     Running   0          28m

$ kubectl get service -n seldon
NAME                                            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
sentiment-pipeline-example                      ClusterIP   10.0.0.144   <none>        8000/TCP,5001/TCP   27m
sentiment-pipeline-example-sentiment-analysis   ClusterIP   10.0.0.18    <none>        9000/TCP            28m
sentiment-pipeline-example-summarize-text       ClusterIP   10.0.0.209   <none>        9002/TCP            28m
sentiment-pipeline-example-text-tagging         ClusterIP   10.0.0.200   <none>        9001/TCP            28m
```

Query the model service engine:

```
$ curl -s -X POST -H 'Content-Type: application/json' -d '{"meta": {"tags": {}},"data": {"names": ["message"],"ndarray": ["In an attempt to build an AI-ready workforce, Microsoft announced Intelligent Cloud Hub which has been launched to empower the next generation of students with AI-ready skills. Envisioned as a three-year collaborative program, Intelligent Cloud Hub will support around 100 institutions with AI infrastructure, course content and curriculum, developer support, development tools and give students access to cloud and AI services. As part of the program, the Redmond giant which wants to expand its reach and is planning to build a strong developer ecosystem in India with the program will set up the core AI infrastructure and IoT Hub for the selected campuses. The company will provide AI development tools and Azure AI services such as Microsoft Cognitive Services, Bot Services and Azure Machine Learning. According to Manish Prakash, Country General Manager-PS, Health and Education, Microsoft India, said, With AI being the defining technology of our time, it is transforming lives and industry and the jobs of tomorrow will require a different skillset. This will require more collaborations and training and working with AI. That’s why it has become more critical than ever for educational institutions to integrate new cloud and AI technologies. The program is an attempt to ramp up the institutional set-up and build capabilities among the educators to educate the workforce of tomorrow. The program aims to build up the cognitive skills and in-depth understanding of developing intelligent cloud connected solutions for applications across industry. Earlier in April this year, the company announced Microsoft Professional Program In AI as a learning track open to the public. The program was developed to provide job ready skills to programmers who wanted to hone their skills in AI and data science with a series of online courses which featured hands-on labs and expert instructors as well. This program also included developer-focused AI school that provided a bunch of assets to help build AI skills"]}}' http://127.0.0.1:31945/seldon/seldon/sentiment-pipeline/api/v0.1/predictions | jq
{
  "data": {
    "names": [],
    "ndarray": [
      "In an attempt to build an AI-ready workforce, Microsoft announced Intelligent Cloud Hub which has been launched to empower the next generation of students with AI-ready skills. Envisioned as a three-year collaborative program, Intelligent Cloud Hub will support around 100 institutions with AI infrastructure, course content and curriculum, developer support, development tools and give students access to cloud and AI services. As part of the program, the Redmond giant which wants to expand its reach and is planning to build a strong developer ecosystem in India with the program will set up the core AI infrastructure and IoT Hub for the selected campuses. The company will provide AI development tools and Azure AI services such as Microsoft Cognitive Services, Bot Services and Azure Machine Learning. According to Manish Prakash, Country General Manager-PS, Health and Education, Microsoft India, said, With AI being the defining technology of our time, it is transforming lives and industry and the jobs of tomorrow will require a different skillset. This will require more collaborations and training and working with AI. That’s why it has become more critical than ever for educational institutions to integrate new cloud and AI technologies. The program is an attempt to ramp up the institutional set-up and build capabilities among the educators to educate the workforce of tomorrow. The program aims to build up the cognitive skills and in-depth understanding of developing intelligent cloud connected solutions for applications across industry. Earlier in April this year, the company announced Microsoft Professional Program In AI as a learning track open to the public. The program was developed to provide job ready skills to programmers who wanted to hone their skills in AI and data science with a series of online courses which featured hands-on labs and expert instructors as well. This program also included developer-focused AI school that provided a bunch of assets to help build AI skills"
    ]
  },
  "meta": {
    "tags": {
      "input_text": "In an attempt to build an AI-ready workforce, Microsoft announced Intelligent Cloud Hub which has been launched to empower the next generation of students with AI-ready skills. Envisioned as a three-year collaborative program, Intelligent Cloud Hub will support around 100 institutions with AI infrastructure, course content and curriculum, developer support, development tools and give students access to cloud and AI services. As part of the program, the Redmond giant which wants to expand its reach and is planning to build a strong developer ecosystem in India with the program will set up the core AI infrastructure and IoT Hub for the selected campuses. The company will provide AI development tools and Azure AI services such as Microsoft Cognitive Services, Bot Services and Azure Machine Learning. According to Manish Prakash, Country General Manager-PS, Health and Education, Microsoft India, said, With AI being the defining technology of our time, it is transforming lives and industry and the jobs of tomorrow will require a different skillset. This will require more collaborations and training and working with AI. That’s why it has become more critical than ever for educational institutions to integrate new cloud and AI technologies. The program is an attempt to ramp up the institutional set-up and build capabilities among the educators to educate the workforce of tomorrow. The program aims to build up the cognitive skills and in-depth understanding of developing intelligent cloud connected solutions for applications across industry. Earlier in April this year, the company announced Microsoft Professional Program In AI as a learning track open to the public. The program was developed to provide job ready skills to programmers who wanted to hone their skills in AI and data science with a series of online courses which featured hands-on labs and expert instructors as well. This program also included developer-focused AI school that provided a bunch of assets to help build AI skills",
      "sentiment_analysis_passed": true,
      "sentiment_analysis_result": {
        "compound": 0.9769,
        "neg": 0.008,
        "neu": 0.891,
        "pos": 0.101
      },
      "summarize_text_passed": true,
      "summarize_text_result": "[' As part of the program, the Redmond giant which wants to expand its reach and is planning to build a strong developer ecosystem in India with the program will set up the core AI infrastructure and IoT Hub for the selected campuses', ' The program was developed to provide job ready skills to programmers who wanted to hone their skills in AI and data science with a series of online courses which featured hands-on labs and expert instructors as well']",
      "tags": "['#track', '#transforming', '#envisioned', '#selected', '#reach']",
      "text_tagging_passed": true
    }
  }
}
```

# Projects

## alibi

> Alibi is an open source Python library aimed at machine learning model inspection and interpretation.
> The focus of the library is to provide high-quality implementations of black-box, white-box, local
> and global explanation methods for classification and regression models.

The API of alibi is simple Python functions, e.g.

```python
from alibi.explainers import AnchorTabular

# initialize and fit explainer by passing a prediction function and any other required arguments
explainer = AnchorTabular(predict_fn, feature_names=feature_names, category_map=category_map)
explainer.fit(X_train)

# explain an instance
explanation = explainer.explain(x)
```
