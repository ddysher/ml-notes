<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [TensorRT](#tensorrt)
  - [TensorRT Inference Server](#tensorrt-inference-server)
- [Projects](#projects)
  - [onnx-tensorrt](#onnx-tensorrt)
  - [tensorflow-tensorrt](#tensorflow-tensorrt)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## TensorRT

*Date: 04/05/2019, v5.0*

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

TensorRT is not open source.

*References*

- https://docs.nvidia.com/deeplearning/sdk/tensorrt-developer-guide/index.html
- https://github.com/ktkrhr/tensorrt-sample

## TensorRT Inference Server

The NVIDIA [TensorRT Inference Server (TRTIS)](https://developer.nvidia.com/tensorrt) builds on top
of TensorRT runtime (as well as other frameworks like TensorFlow, Caffe2, etc, or custom framework)
to provide an inferencing microservice optimized for Nvidia GPUs. The server provides an inference
service via an HTTP or gRPC endpoint, allowing remote clients to request inferencing for any model
being managed by the server. Many aspects of TRTIS resembles TensorFlow Serving.

TensorRT Inference Server is open source.

*Reference*

- https://docs.nvidia.com/deeplearning/sdk/tensorrt-inference-server-master-branch-guide/docs/index.html
- https://devblogs.nvidia.com/nvidia-serves-deep-learning-inference/
- https://github.com/NVIDIA/tensorrt-inference-server

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
supported layers, and fall back to TensorFlow if not.

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

*References*

- https://docs.nvidia.com/deeplearning/dgx/tf-trt-user-guide/index.html
- https://devblogs.nvidia.com/tensorrt-integration-speeds-tensorflow-inference/
