<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Flintrock](#flintrock)
- [Spark Operator](#spark-operator)
- [Troee](#troee)
- [Zeppelin](#zeppelin)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Flintrock

[flintrock](https://github.com/nchammas/flintrock) is a command-line tool for launching Apache Spark
clusters. By Spark cluster, it means a Spark standalone cluster. flintrock super spark-ec2, a tool
from amplab to launch Spark cluster in AWS.

# Spark Operator

[Spark operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator/) provides Kubernetes
native approach to run Spark on Kubernetes. It exposes a handfule of CRDs as its API, which
encapsulate most spark configurations, e.g. for the following CR, specs like `mode`, `mainClass`
are all spark options, but are specified using yaml file.

```yaml
apiVersion: "sparkoperator.k8s.io/v1alpha1"
kind: SparkApplication
metadata:
  name: spark-pi
  namespace: default
spec:
  type: Scala
  mode: cluster
  image: "gcr.io/spark-operator/spark:v2.4.0"
  imagePullPolicy: Always
  mainClass: org.apache.spark.examples.SparkPi
  mainApplicationFile: "local:///opt/spark/examples/jars/spark-examples_2.11-2.4.0.jar"
  volumes:
    - name: "test-volume"
      hostPath:
        path: "/tmp"
        type: Directory
  driver:
    cores: 0.1
    coreLimit: "200m"
    memory: "512m"
    labels:
      version: 2.4.0
    serviceAccount: spark
    volumeMounts:
      - name: "test-volume"
        mountPath: "/tmp"
  executor:
    cores: 1
    instances: 1
    memory: "512m"
    labels:
      version: 2.4.0
    volumeMounts:
      - name: "test-volume"
        mountPath: "/tmp"
```

The images used above are built from both spark operator and spark core, ref [issue](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator/issues/113).

# Troee

Apache Toree is a Jupyter kernel with one main goal: provide the foundation for interactive applications
to connect and use Apache Spark.

When the user creates a new Notebook and selects Toree, the Notebook server launches a new Toree process
that is configured to connect to a Spark cluster. Once in the Notebook, the user can interact with Spark
by writing code that uses the managed Spark Context instance.

By default, toree runs local Spark, we can use resource manager using option `--spark_opts`:

```
jupyter toree install\
 --replace\
 --user\
 --kernel_name="Spark GeoMesa"\
 --spark_home=${SPARK_HOME}\
 --spark_opts="--master yarn --jars file://${GEOMESA_LIB}/common/jai_core-1.1.3.jar,file://${GEOMESA_LIB}/common/jai_codec-1.1.3.jar,file://${GEOMESA_LIB}/common/jai_imageio-1.1.jar,file://${GEOMESA_SRC}/geomesa-compute_2.10-1.2.5-shaded.jar"
```

For more information, ref:
- https://toree.apache.org/docs/current/user/how-it-works/
- http://bailiwick.io/2018/08/31/connect-jupyter-to-remote-spark-clusters-with-apache-toree/

# Zeppelin

Zeppelin is a web-based notebook that enables data-driven, interactive data analytics and collaborative
documents with SQL, Scala and more. It is commonly used with data analyst and data engineer.

Zeppelin is NOT built on top of Jupyuter: its notebook format is not compatible with Jupyter notebook
(although both uses json format). Architecture-wise, similar to Jupyter, Zeppelin has a two-process
mode: server process communicates with interpreter through thrift (Jupyter uses 0MQ).

A quick comparison with Jupyter:
- Jupyter notebooks are mainly popular among Python users (even though other kernels exist). They are
  suited when working with data that can fit into memory.
- Zeppelin is better when the data doesn't fit into memory (i.e. it is distributed across a cluster).
  It is also (slightly) better for creating dashboards and sharing them.

Running Zeppelin is as simple as downloading tar file and run `./bin/zeppelin-daemon start`. A server
process will be launched to serve Zeppelin UI. Interpreters will be launched when we create or open
a notebook to execute code. All interpreters need to implement an abstract `Interpreter` class, ref
[interpreter.java](https://github.com/apache/zeppelin/blob/v0.8.0/zeppelin-interpreter/src/main/java/org/apache/zeppelin/interpreter/Interpreter.java).

The required methods are:

```java
public abstract void open();
public abstract void close();
public abstract InterpreterResult interpret(String st, InterpreterContext context);
```
