<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Tensorflow Serving (r1.4)](#tensorflow-serving-r14)
  - [Hello World](#hello-world)
    - [Build](#build)
    - [Training](#training)
    - [Serving:](#serving)
    - [Inference:](#inference)
    - [Look into SavedModel](#look-into-savedmodel)
    - [Create new model](#create-new-model)
  - [Official basic tutorial](#official-basic-tutorial)
    - [Training and Export](#training-and-export)
    - [Serving](#serving)
    - [Inference](#inference)
    - [Look into SavedModel](#look-into-savedmodel-1)
  - [Multiple Models](#multiple-models)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Tensorflow Serving (r1.4)

## Hello World

- https://medium.com/epigramai/tensorflow-serving-101-pt-1-a79726f7c103
- https://medium.com/epigramai/tensorflow-serving-101-pt-2-682eaf7469e7

### Build

```
git clone --recurse-submodules https://github.com/tensorflow/serving
cd serving
bazel build -c opt //tensorflow_serving/model_servers:tensorflow_model_server
```

### Training

Enter 'helloworld' directory:

```
python model.py --model_dir=/tmp/simple_model --model_version=1
```

This will save our model to `/tmp/simple_model/1`.

### Serving:

```
tensorflow_model_server --port=9000 --model_name=simple --model_base_path=/tmp/simple_model
```

Or using docker (tf v1.13, note the port):

```
docker run --rm -p 8500:8500 -p 8501:8501 -v /tmp/simple_model:/models/simple_model \
  tensorflow/serving:1.13.0 --model_name=simple --model_base_path=/models/simple_model
```

Note here we pass both `model_name` and `model_base_path` to tensorflow serving.
- default value for `model_name` is `model`
- default value for `model_base_path` is `/models`

Therefore:
- if we do not provide the two params, TFServing will try to locate model versions in `/models/model`
- if we only pass `model_name`, TFServing will try to locate model versions in `/models/{name}`
- if we pass `model_base_path`, TFServing will try to locate model versions there, regardless the value of `model_name`

Apart from locating models, `model_name` is also used when serving multiple models, shown below.

Newer version of TFServing supports gRPC as well as REST API, the default is:
- Port 8500 exposed for gRPC
- Port 8501 exposed for the REST API

### Inference:

```
python client.py --host=localhost:9000 --model_name=simple --model_version=1
```

### Look into SavedModel

```
python inspect_model.py --model_dir=/tmp/simple_model/1
```

### Create new model

Edit model.py to use different placeholder name, e.g. 'a' -> 'x'

```
python model.py --model_dir=/tmp/simple_model --model_version=2
```

This will save our model to `/tmp/simple_model/2`.

Now both of the following inferences will fail:

```
python client.py --host=localhost:9000 --model_name=simple --model_version=1
python client.py --host=localhost:9000 --model_name=simple --model_version=2
```

The first one fails because model 1 is unloaded; the second one fails because model 2 uses different
tensor input alias. If we change client code's input tensor name `in_tensor_name'`from 'a' -> 'x',
the second one will succeed.

Note all the above behavior is the standard serving binary; we can customize the behavior by building
custom serving binary.

## Official Tutorial

https://github.com/tensorflow/tensorflow/blob/r1.4/tensorflow/python/saved_model/README.md

### Training and Export

Enter 'mnist' directory, then run:

```sh
$ rm -rf /tmp/mnist_model && mkdir -p /tmp/mnist_model

$ python mnist_saved_model.py /tmp/mnist_model
$ python mnist_saved_model.py --model_version=2 /tmp/mnist_model
```

### Serving

```sh
tensorflow_model_server --port=9000 --model_name=mnist --model_base_path=/tmp/mnist_model/
```

Or using docker (tf v1.13, note the port):

```
docker run --rm -p 8500:8500 -p 8501:8501 -v /tmp/mnist_model:/models/mnist_model \
  tensorflow/serving:1.13.0 --model_name=mnist --model_base_path=/models/mnist_model
```

### Inference

```sh
python mnist_client.py --num_tests=100 --server=localhost:9000
```

## Multiple Models

On top directory, create two models:

```
python helloworld/model.py --model_dir=/tmp/simple_model  --model_version=1
python helloworld/model.py --model_dir=/tmp/another_model --model_version=1
python helloworld/model.py --model_dir=/tmp/another_model --model_version=2
```

Run serving binary:

```
tensorflow_model_server --port=9000 --model_config_file=./multiple/model_config.json
```

Or using docker (tf v1.13, note the port):

```
docker run --rm -p 8500:8500 -p 8501:8501 \
  -v /tmp:/models \
  -v `pwd`/multiple/model_config.docker.json:/tmp/model_config.docker.json \
  tensorflow/serving:1.13.0 --model_config_file=/tmp/model_config.docker.json
```

Inference (model name comes from the config file):

```
python helloworld/client.py --host=localhost:9000 --model_name=model1 --model_version=1
python helloworld/client.py --host=localhost:9000 --model_name=model2 --model_version=2
```

Each model is a single `config` entry in `model_config.json`. The default version policy for all
models is to serve the newest version, thus for model2, only version 2 is available. This version
policy configurable, ref: https://www.tensorflow.org/tfx/serving/serving_config
