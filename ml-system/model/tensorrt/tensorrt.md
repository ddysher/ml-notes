<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [TensorRT](#tensorrt)
  - [TensorRT Inference Server (TRTIS)](#tensorrt-inference-server-trtis)
- [TRTIS Designs](#trtis-designs)
  - [Architecture](#architecture)
  - [Model Repository](#model-repository)
  - [Model Configuration](#model-configuration)
  - [Model Control](#model-control)
  - [Model Type](#model-type)
  - [Scheduler and Batcher](#scheduler-and-batcher)
  - [Performance Optimization](#performance-optimization)
  - [Client HTTP/gRPC APIs](#client-httpgrpc-apis)
- [Experiments](#experiments)
  - [Prerequisites](#prerequisites)
  - [Start TRTIS](#start-trtis)
  - [Run Client Query](#run-client-query)
- [Projects](#projects)
  - [onnx-tensorrt](#onnx-tensorrt)
  - [tensorflow-tensorrt](#tensorflow-tensorrt)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## TensorRT

- *Date: 04/05/2019, v5.0*

NVIDIA [TensorRT](https://developer.nvidia.com/tensorrt) is a platform for high-performance deep
learning inference on GPU. At its core, it's an inference execution engine for deep learning graphs
(using cuda): it implements many common layers in deep learning, e.g. pooling layer, RNN layer, etc.
Developers can implement custom layers using TensorRT C++ or Python APIs. TensorRT is generally not
used during any part of the training phase.

TensorRT can be part high-performance inference optimizer and part runtime engine.
- it can take in neural networks trained on popular frameworks,
- optimize the neural network computation,
- generate a light-weight runtime engine (which is the only thing you need to deploy to your production environment),
- it will then maximize the throughput, latency, and performance on these GPU platforms.

TensorRT optimizes the network by combining layers and optimizing kernel selection for improved
latency, throughput, power efficiency and memory consumption. If the application specifies, it will
additionally optimize the network to run in lower precision, further increasing performance and
reducing memory requirements.

TensorRT engine's serialized format is also called a `plan` file. It can be created from scratch,
just as we could using other framework like TensorFlow, but generally, we take the saved neural
network and parse it from its saved format into TensorRT using the ONNX parser, Caffe parser, or
TensorFlow/UFF parser.

Note the generated plan files are not portable across platforms or TensorRT versions. Plans are
specific to the exact GPU model they were built on (in addition to platforms and the TensorRT
version) and must be re-targeted to the specific GPU in case you want to run them on a different
GPU.

*References*

- https://github.com/NVIDIA/tensorrt
- https://github.com/ktkrhr/tensorrt-sample
- https://docs.nvidia.com/deeplearning/sdk/tensorrt-developer-guide/index.html

## TensorRT Inference Server (TRTIS)

The NVIDIA [TensorRT Inference Server (TRTIS)](https://developer.nvidia.com/tensorrt) builds on top
of TensorRT runtime (as well as other frameworks) to provide an inferencing microservice optimized
for Nvidia GPUs (and CPU). The server provides an inference service via an HTTP or gRPC endpoint,
allowing remote clients to request inferencing for any model being managed by the server. Many
aspects of TRTIS resembles TensorFlow Serving. Features of TRTIS includes:
- Multiple deep learning framework support
- Concurrent model execution support
- Batching support
- Custom backend support
- Ensemble support
- Minor features
  - Multiple GPU support
  - Model management, e.g. reload
  - Model repository
  - Health check
  - Metrics
  - C server API library
  - C/Python client library

By default the inference server supports NVIDIA GPUs. Use `-DTRTIS_ENABLE_GPU=OFF` to disable GPU
support when building from source. When GPUs are disable the inference server will run models on CPU
when possible; that is, on a system without GPUs, the inference server should be run using `docker`
instead of `nvidia-docker`, but is otherwise identical to GPU version.

Run with GPU:

```
$ nvidia-docker run --rm --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 -p8000:8000 -p8001:8001 -p8002:8002 -v/path/to/model/repository:/models <tensorrtserver image name> trtserver --model-store=/models
```

Run without GPU:

```
$ docker run --rm --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 -p8000:8000 -p8001:8001 -p8002:8002 -v/path/to/model/repository:/models <tensorrtserver image name> trtserver --model-store=/models
```

Here, `<tensorrtserver image name>` can be `nvcr.io/nvidia/tensorrtserver:19.07-py3`.

Supported backend include:
- TensorFlow, via its [C++ API](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/core/public), e.g. call `session_.run()`
- PyTorch, via [LibTorch C++ API](https://pytorch.org/cppdocs/)
- ONNX, via [onnxruntime C++ API](https://github.com/microsoft/onnxruntime/blob/v0.5.0/docs/C_API.md)
  - onnxruntime excution provider includes TensorRT, OpenVINO, etc
- TensorRT, via [C++ API](https://docs.nvidia.com/deeplearning/sdk/tensorrt-api/index.html)
- Caffe2, via its NetDef C API
- Custom .so library via C API
- Ensemble of multiple stages for an inference task

*Reference*

- https://github.com/NVIDIA/tensorrt-inference-server
- https://devblogs.nvidia.com/nvidia-serves-deep-learning-inference/
- https://docs.nvidia.com/deeplearning/sdk/tensorrt-inference-server-master-branch-guide/docs/index.html

# TRTIS Designs

- *Date: 01/05/2020, v19.11*

## Architecture

*Reference*

- https://docs.nvidia.com/deeplearning/sdk/tensorrt-inference-server-guide/docs/architecture.html

## Model Repository

Model repository is where TRTIS loads models to serve, following is an examples repository:

```
<model-repository-path>/
  model_0/
    config.pbtxt
    output0_labels.txt
    1/
      model.plan
    2/
      model.plan
  model_1/
    config.pbtxt
    output0_labels.txt
    output1_labels.txt
    0/
      model.graphdef
    7/
      model.graphdef
```

Here,
- two models named `model_0` and `model_1` will be served
- each model has two versions, identified by numeric subdirectory
- configuration and labels are specified using `config.pbtxt` and `*_labels.txt`
- model definition filename must be `model.*` (there can be multiple model definition file, for different GPU compute capacity)

Model repository supports two more backends apart from deep learning backends (e.g. tensorflow,
pytorch), namely custom backend and ensemble backend.

**Custom Backend**

The core of custom backend is to implement the [custom.h](https://github.com/NVIDIA/tensorrt-inference-server/blob/r19.11/src/backends/custom/custom.h)
interface. TRTIS uses the [custom backend factory and loader](https://github.com/NVIDIA/tensorrt-inference-server/tree/r19.11/src/backends/custom)
to load library `libcustom.so` compiled from user, and then run `Context::Execute` function defined
in the interface: most of the custom logics are implemented in this function. Essentially, the
function takes the input tensors and generates output tensors. For example, here is an [image_preprocess](https://github.com/NVIDIA/tensorrt-inference-server/tree/r19.11/src/custom/image_preprocess)
custom backend that reshapes an image before sending to image detection model.

**Ensemble Backend**

Models using ensemble backend is essentially a pipeline of models, e.g. [preprocess_resnet50_ensemble](https://github.com/NVIDIA/tensorrt-inference-server/blob/r19.11/docs/examples/ensemble_model_repository/preprocess_resnet50_ensemble/config.pbtxt).

## Model Configuration

Each model in the model repository must contain a configuration `config.pbtxt`. In some cases, the
file can be automatically generated from underline model definition file. For example:

```
name: "mymodel"
platform: "tensorrt_plan"
max_batch_size: 8
input [
  {
    name: "input0"
    data_type: TYPE_FP32
    dims: [ 16 ]
  },
  {
    name: "input1"
    data_type: TYPE_FP32
    dims: [ 16 ]
  }
]
output [
  {
    name: "output0"
    data_type: TYPE_FP32
    dims: [ 16 ]
  }
]
```

Notes:
- If `max_batch_size` is 0, then the model is considered not support batching; if it's >0, then
  batching is supported and the first dimension is batch size, i.e. in the above example, [x, 16]
- The model configuration can be more restrictive than what is allowed by the underlying model,
  e.g. in the above configuration, even if the underline model can accept any size in the first
  dimension, TRTIS will only allow inference request with size 16 in the first dimension.
- Generated model configuration does have some limitations depending on the frameworks.
- Important & useful configurations:
  - name
  - platform
  - max_batch_size
  - input
  - output
  - version_policy
  - optimization
  - scheduling and batching
  - instance_group
  - default_model_filename
  - cc_model_filenames
  - tags
  - warmup

**Reshape**

The `ModelTensorReshape` property on a model configuration input or output is used to indicate that
the input or output shape accepted by the inference API differs from the input or output shape
expected or produced by the underlying framework model or custom backend.

**Instance Groups**

The instance-group setting can be used to place multiple execution instances of a model on every GPU
or on only certain GPUs. By default, only one inference request can be handled at a time; with multiple
execution instances, multiple simultaneous inference requests for that model can be handled
simultaneously. For more information, refer to [architecture guide](https://docs.nvidia.com/deeplearning/sdk/tensorrt-inference-server-guide/docs/architecture.html#section-concurrent-model-execution).

For example, following configuration uses 2 execution instances.

```
name: "mymodel"
platform: "tensorrt_plan"
max_batch_size: 8
input [
  {
    name: "input0"
    data_type: TYPE_FP32
    dims: [ 16 ]
  },
  {
    name: "input1"
    data_type: TYPE_FP32
    dims: [ 16 ]
  }
]
output [
  {
    name: "output0"
    data_type: TYPE_FP32
    dims: [ 16 ]
  }
]
instance_group [
  {
    count: 2
    kind: KIND_CPU
  }
]
```

## Model Control

Model control means how TRTIS loads/unloads models, control policies includes:
- NONE: trtis loads all models under model repository path at starts, but will ignore any changes afterwards
- POLL: trtis will poll model repository path at specified interval to load/unload/update models
- EXPLICIT: trtis will only load specified models, and can be controlled via a model control API

## Model Type

TRTIS categorizes models into three categories:
- stateless models
- stateful models
- ensemble models

**Stateless Models**

A stateless model (or stateless custom backend) does not maintain state between inference requests.
Examples of stateless models are CNNs such as image classification and object detection. RNNs have
state but as long as the state is not carried across inference requests, then it's also considered
stateless.

**Stateful Models**

A stateful model (or stateful custom backend) does maintain state between inference requests. The
model is expecting multiple inference requests to form a sequence of inferences that must be routed
to the same model; and due to the state, the model may require control signal, e.g. sequence start.
The control signals are specified in model configuration.

When making inference requests for a stateful model, the client application must provide the same
correlation ID to all requests in a sequence, and must also mark the start and end of the sequence.
The correlation ID allows the inference server to identify that the requests belong to the same
sequence.

**Ensemble Models**

An ensemble model represents a pipeline of one or more models and the connection of input and output
tensors between those models. Ensemble models are intended to be used to encapsulate a procedure
that involves multiple models, such as "data preprocessing -> inference -> data postprocessing".

## Scheduler and Batcher

There are four types of scheduler and batcher in TRTIS:
- default scheduler
- dynamic batcher
- sequence batcher
- ensemble scheduler

**Default Scheduler**

The default scheduler is used for a model if none of the scheduling_choice configurations are specified.

**Dynamic Batcher**

Dynamic batching is a feature of the inference server that allows inference requests to be combined
by the server, so that a batch is created dynamically.

Dynamic batcher can be used for stateless models.

**Sequence Batcher**

Like the dynamic batcher, the sequence batcher combines non-batched inference requests, so that a
batch is created dynamically. Unlike the dynamic batcher, the sequence batcher should be used for
stateful models where a sequence of inference requests must be routed to the same model instance.
Sequence batcher has two strategies: Direct and Oldest.

As mentioned above, sequence batcher has configuration for control signal, e.g.

<details><summary>sequence_batching</summary><p>

```
sequence_batching {
  control_input [
    {
      name: "START"
      control [
        {
          kind: CONTROL_SEQUENCE_START
          fp32_false_true: [ 0, 1 ]
        }
      ]
    },
    {
      name: "END"
      control [
        {
          kind: CONTROL_SEQUENCE_END
          fp32_false_true: [ 0, 1 ]
        }
      ]
    },
    {
      name: "READY"
      control [
        {
          kind: CONTROL_SEQUENCE_READY
          fp32_false_true: [ 0, 1 ]
        }
      ]
    },
    {
      name: "CORRID"
      control [
        {
          kind: CONTROL_SEQUENCE_CORRID
          data_type: TYPE_UINT64
        }
      ]
    }
  ]
}
```

</p></details></br>

**Ensemble Scheduler**

The ensemble scheduler must be used for ensemble models. For example,

<details><summary>ensemble_model</summary><p>

```
name: "ensemble_model"
platform: "ensemble"
max_batch_size: 1
input [
  {
    name: "IMAGE"
    data_type: TYPE_STRING
    dims: [ 1 ]
  }
]
output [
  {
    name: "CLASSIFICATION"
    data_type: TYPE_FP32
    dims: [ 1000 ]
  },
  {
    name: "SEGMENTATION"
    data_type: TYPE_FP32
    dims: [ 3, 224, 224 ]
  }
]
ensemble_scheduling {
  step [
    {
      model_name: "image_preprocess_model"
      model_version: -1
      input_map {
        key: "RAW_IMAGE"
        value: "IMAGE"
      }
      output_map {
        key: "PREPROCESSED_OUTPUT"
        value: "preprocessed_image"
      }
    },
    {
      model_name: "classification_model"
      model_version: -1
      input_map {
        key: "FORMATTED_IMAGE"
        value: "preprocessed_image"
      }
      output_map {
        key: "CLASSIFICATION_OUTPUT"
        value: "CLASSIFICATION"
      }
    },
    {
      model_name: "segmentation_model"
      model_version: -1
      input_map {
        key: "FORMATTED_IMAGE"
        value: "preprocessed_image"
      }
      output_map {
        key: "SEGMENTATION_OUTPUT"
        value: "SEGMENTATION"
      }
    }
  ]
}
```

</p></details></br>

## Performance Optimization

Performance optimization in TRTIS includes:
- dynamic batching
- model instances, i.e. instance group
- framework-specific optimization

The first two are self-explanatory, the third one is about TensorRT integration with deep learning
frameworks, i.e. ONNX with TensorRT optimization, TensorFlow with TensorRT optimization. When
enabled for a model, TensorRT optimization will be applied to the model at load time or when it
first receives inference requests. TensorRT optimizations include specializing and fusing model
layers, and using reduced precision (for example 16-bit floating-point) to provide significant
throughput and latency improvements.

TRTIS provides perf_client tool, and server side tracing to help with performance optimization.

## Client HTTP/gRPC APIs

TRTIS exposes both HTTP and gRPC endpoints for client consumption, including:
- Health
- Status
- Model Control
- Inference
- Stream Inference (only gRPC)

Specifically, the Inference APIs takes `POST` request with predefined headers `NV-InferRequest`,
input & output tensor data are delivered via POST body.

# Experiments

## Prerequisites

Checkout TRTIS repository and fetch models:

```
$ git clone https://github.com/NVIDIA/tensorrt-inference-server
$ cd tensorrt-inference-server
$ git checkout r19.11

$ cd ./docs/examples
$ ./fetch_models
$ cd -
```

This will fetch the following models under `./model_repository` directory:
- Caffe2 ResNet50: `init_model.netdef` & `model.netdef`
- TensorFlow Inception: `model.graphdef`
- ONNX DenseNet: `model.onnx`

In addition, each model comes with a `config.pbtxt` and `*_labels.txt` required by TRTIS. For example,

```
$ cat model_repository/inception_graphdef/config.pbtxt
name: "inception_graphdef"
platform: "tensorflow_graphdef"
max_batch_size: 128
input [
  {
    name: "input"
    data_type: TYPE_FP32
    format: FORMAT_NHWC
    dims: [ 299, 299, 3 ]
  }
]
output [
  {
    name: "InceptionV3/Predictions/Softmax"
    data_type: TYPE_FP32
    dims: [ 1001 ]
    label_filename: "inception_labels.txt"
  }
]
instance_group [
  {
    kind: KIND_GPU,
    count: 4
  }
]


$ cat model_repository/inception_graphdef/inception_labels.txt
UNUSED BACKGROUND
TENCH
GOLDFISH
...
BOLETE
EAR
TOILET TISSUE
```

The above models require GPUs, if it's not available, we can use the `simple` model, which takes
2 input tensors of 16 integers each and returns 2 output tensors of 16 integers each. One output
tensor is the element-wise sum of the inputs and one output is the element-wise difference.

```
$ cp -r docs/examples/model_repository/simple /tmp/models

$ cat docs/examples/model_repository/simple/config.pbtxt
name: "simple"
platform: "tensorflow_graphdef"
max_batch_size: 8
input [
  {
    name: "INPUT0"
    data_type: TYPE_INT32
    dims: [ 16 ]
  },
  {
    name: "INPUT1"
    data_type: TYPE_INT32
    dims: [ 16 ]
  }
]
output [
  {
    name: "OUTPUT0"
    data_type: TYPE_INT32
    dims: [ 16 ]
  },
  {
    name: "OUTPUT1"
    data_type: TYPE_INT32
    dims: [ 16 ]
  }
]
```

## Start TRTIS

To start TRTIS, run the command (use `simple` model):

```
$ nvidia-docker run --rm --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 \
  -p8000:8000 -p8001:8001 -p8002:8002 \
  -v /tmp/models:/models \
  nvcr.io/nvidia/tensorrtserver:19.11-py3 \
  trtserver --model-store=/models
```

## Run Client Query

To run client query, run the following command. Note the clientsdk container image doesn't contain
`simple_client.py`, thus we need to mount the source code into the container.

<details><summary>client query</summary><p>

```
$ docker run -it --rm --net=host -v `pwd`:/trtis nvcr.io/nvidia/tensorrtserver:19.11-py3-clientsdk
root@mangosteen:/trtis# cd src/clients/python/
root@mangosteen:/trtis/src/clients/python# python simple_client.py
Health for model simple
Live: True
Ready: True
Status for model simple
id: "inference:0"
version: "1.5.0"
uptime_ns: 7501574309730
model_status {
  key: "simple"
  value {
    config {
      name: "simple"
      platform: "tensorflow_graphdef"
      version_policy {
        latest {
          num_versions: 1
        }
      }
      max_batch_size: 8
      input {
        name: "INPUT0"
        data_type: TYPE_INT32
        dims: 16
      }
      input {
        name: "INPUT1"
        data_type: TYPE_INT32
        dims: 16
      }
      output {
        name: "OUTPUT0"
        data_type: TYPE_INT32
        dims: 16
      }
      output {
        name: "OUTPUT1"
        data_type: TYPE_INT32
        dims: 16
      }
      instance_group {
        name: "simple"
        count: 1
        kind: KIND_CPU
      }
      default_model_filename: "model.graphdef"
    }
    version_status {
      key: 1
      value {
        ready_state: MODEL_READY
      }
    }
  }
}
ready_state: SERVER_READY

====Infer Statistcs====
completed_request_count: 1
cumulative_total_request_time_ns: 244994727
cumulative_send_time_ns: 163855
cumulative_receive_time_ns: 8276
=======================


0 + 1 = 1
0 - 1 = -1
1 + 1 = 2
1 - 1 = 0
2 + 1 = 3
2 - 1 = 1
3 + 1 = 4
3 - 1 = 2
4 + 1 = 5
4 - 1 = 3
5 + 1 = 6
5 - 1 = 4
6 + 1 = 7
6 - 1 = 5
7 + 1 = 8
7 - 1 = 6
8 + 1 = 9
8 - 1 = 7
9 + 1 = 10
9 - 1 = 8
10 + 1 = 11
10 - 1 = 9
11 + 1 = 12
11 - 1 = 10
12 + 1 = 13
12 - 1 = 11
13 + 1 = 14
13 - 1 = 12
14 + 1 = 15
14 - 1 = 13
15 + 1 = 16
15 - 1 = 14
```

</p></details></br>

The file `simple_client.py` locates under `src/clients/python` in TRTIS source tree, and the client
API definitions, e.g. `ServerStatusContext`, `InferContext` locates under `src/clients/python/__init__.py`.
Ref [here](https://github.com/NVIDIA/tensorrt-inference-server/blob/r19.11/src/clients/python/__init__.py).

# Projects

## onnx-tensorrt

[onnx-tensorrt](https://github.com/onnx/onnx-tensorrt/) creates a binary to convert onnx model, e.g.

```shell
onnx2trt my_model.onnx -o my_engine.trt
```

The core of the tool is to read the onnx model, call TensorRT onnx parser C++ API, then output the
model.

In addition, the project also provides a python package, which contains programming APIs to load onnx
model for TensorRT engine, using TensorRT python API. In the following example, the onnx model is
converted to TensorRT format (in `backend.prepare`, using onnx parser Python API), then feed into
TensorRT engine for inference (in `engine.run`).

```python
import onnx
import onnx_tensorrt.backend as backend
import numpy as np

model = onnx.load("/path/to/model.onnx")
engine = backend.prepare(model, device='CUDA:1')
input_data = np.random.random(size=(32, 3, 224, 224)).astype(np.float32)
output_data = engine.run(input_data)[0]
print(output_data)
print(output_data.shape)
```

## tensorflow-tensorrt

TensorFlow has native support for TensorRT, we can load TensorFlow model, convert to TensorRT
inference graph, and run the graph. TensorFlow will run sub-graph on TensorRT for all TensorRT
supported layers, and fall back to TensorFlow if not. The TensorFlow [blog](https://medium.com/tensorflow/high-performance-inference-with-tensorrt-integration-c4d78795fbfe)
has an in-depth introduction to the integration.

Following is an example of TF-TRT workflow with a SavedModel:

```python
# Import TensorFlow and TensorRT
import tensorflow as tf
import tensorflow.contrib.tensorrt as trt
# Inference with TF-TRT `SavedModel` workflow:
graph = tf.Graph()
with graph.as_default():
    with tf.Session() as sess:
        # Create a TensorRT inference graph from a SavedModel:
        trt_graph = trt.create_inference_graph(
            input_graph_def=None,
            outputs=None,
            input_saved_model_dir=”/path/to/your/saved/model”,
            input_saved_model_tags=[”your_saved_model_tags”],
            max_batch_size=your_batch_size,
            max_workspace_size_bytes=max_GPU_mem_size_for_TRT,
            precision_mode=”your_precision_mode”)
        # Import the TensorRT graph into a new graph and run:
        output_node = tf.import_graph_def(
            trt_graph,
            return_elements=[“your_outputs”])
       sess.run(output_node)
```

In TensorFlow 2.0, TensorRT has been moved to core compiler repository:

```python
from tensorflow.python.compiler.tensorrt import trt_convert as trt

converter = trt.TrtGraphConverter(
    input_graph_def=frozen_graph,
    nodes_blacklist=['logits', 'classes'],
    max_batch_size=batch_size,
    max_workspace_size_bytes=max_workspace_size,
    precision_mode=precision.upper(),
    minimum_segment_size=minimum_segment_size,
    is_dynamic_op=use_dynamic_op
)
frozen_graph = converter.convert()
```

*References*

- https://docs.nvidia.com/deeplearning/dgx/tf-trt-user-guide/index.html
- https://devblogs.nvidia.com/tensorrt-integration-speeds-tensorflow-inference/
- https://medium.com/tensorflow/high-performance-inference-with-tensorrt-integration-c4d78795fbfe
