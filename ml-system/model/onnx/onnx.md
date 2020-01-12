<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Technical Details](#technical-details)
  - [Specification](#specification)
  - [Limitations](#limitations)
- [Experiments](#experiments)
  - [Python API Overview](#python-api-overview)
  - [End-to-end Examples](#end-to-end-examples)
- [Projects](#projects)
  - [onnx-tensorflow](#onnx-tensorflow)
  - [onnxruntime](#onnxruntime)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Introduction

ONNX provides an open source format for AI models. It defines an extensible computation graph model,
as well as definitions of built-in operators and standard data types. With ONNX, AI developers can
more easily move models between state-of-the-art tools and choose the combination that is best for
them. ONNX enables models to be trained in one framework and transferred to another for inference.

*References*

- https://onnx.ai/
- https://www.linuxjournal.com/content/onnx-open-neural-network-exchange-format

## Technical Details

ONNX provides a definition of an extensible computation graph model, as well as definitions of
built-in operators and standard data types. Each computation dataflow graph is structured as a list
of nodes that form an acyclic graph. Nodes have one or more inputs and one or more outputs. Each
node is a call to an operator. The graph also has metadata to help document its purpose, author,
etc. Operators are implemented externally to the graph, but the set of built-in operators are
portable across frameworks.

**Every framework supporting ONNX will provide implementations of these operators on the applicable
data types.** For example, [here](https://github.com/onnx/onnx-tensorflow/tree/v1.3.0/onnx_tf/handlers/backend)
is the implementation of ONNX backend operators in TensorFlow.

## Specification

The specification consists of: IR (graph model), operators, versioning

- https://github.com/onnx/onnx/blob/v1.3.0/docs/IR.md
- https://github.com/onnx/onnx/blob/v1.3.0/docs/Operators.md
- https://github.com/onnx/onnx/blob/v1.3.0/docs/Operators-ml.md
- https://github.com/onnx/onnx/blob/v1.3.0/docs/Versioning.md

## Limitations

The two limitations are copied from https://pytorch.org/docs/stable/onnx.html
- The ONNX exporter is a *trace-based* exporter, which means that it operates by executing your
  model once, and exporting the operators which were actually run during this run. This means that
  if your model is dynamic, e.g., changes behavior depending on input data, the export won't be
  accurate. Similarly, a trace is likely to be valid only for a specific input size (which is one
  reason why we require explicit inputs on tracing.) We recommend examining the model trace and
  making sure the traced operators look reasonable.
- PyTorch and Caffe2 often have implementations of operators with some numeric differences. Depending
  on model structure, these differences may be negligible, but they can also cause major divergences
  in behavior (especially on untrained models.) In a future release, we plan to allow Caffe2 to call
  directly to Torch implementations of operators, to help you smooth over these differences when
  precision is important, and to also document these differences.

For limitation 1, recall that pytorch is a dynamic graph execution engine, meaning that graph
structure can change depending on input. Therefore, exporting our model by executing it once (using
dummy input) cannot capture the whole picture of our model - the exported model only applies to
the dummy input. On the other hand, if the model is static, executing the model using dummay input
will find out all operators in the model.

# Experiments

## Python API Overview

The experiments here are based on [PythonAPIOverview @ v1.3](https://github.com/onnx/onnx/blob/v1.3.0/docs/PythonAPIOverview.md).

**Make ONNX model**

The example here manually creates a model, i.e. we create a model by defining protos directly. The
model we defined here are structured as:

```
model [ModelProto] {
  graph [GraphProto] {
    node   [NodeProto] {}
    input  [ValueInfoProto] {}
    output [ValueInfoProto] {}
  }
}
```

To see the detailed output, run:

```console
python make_model.py
```

**Check ONNX Model**

In the above section, we also check ONNX Model. Checking model means validating model and catching
any potential errors like duplidate keys, etc.

Note that model checking is implemented in C and invoked from Python, see source [here](https://github.com/onnx/onnx/blob/v1.3.0/onnx/checker.cc).

**Save ONNX Model**

onnx model is represented as protobuf file, to save a onnx model, we use the built-in methods `save`
or `save_mode`, and onnx library will convert in-memory proto to serialized [ModelProto](https://github.com/onnx/onnx/blob/v1.3.0/onnx/onnx.proto).
`save_model.py` is a very simple demostration, just run:

```console
python save_model.py
```

**Load ONNX Model**

Loading ONNX model is the opposite of saving model, it loads a serialized ModelProto into memory.

```console
$ python load_model.py
```

**Optimize ONNX Model**

NOTE: optimization is highly experimental, as commented in the [source code](https://github.com/onnx/onnx/blob/v1.3.0/onnx/optimizer/optimize.h).

onnx library provides a set of optimizers to optimize model, following is a list of existing
optimizations (also called 'passes'):
- eliminate_identity
- eliminate_nop_pad
- eliminate_nop_transpose
- eliminate_unused_initializer
- extract_constant_to_initializer
- fuse_add_bias_into_conv
- fuse_bn_into_conv
- fuse_consecutive_squeezes
- fuse_consecutive_transposes
- fuse_transpose_into_gemm
- lift_lexical_references
- nop
- split_init
- split_predict

To optimize, import the optimizer module and call `optimizer.optimize` with model protocol buffer
and passes as the inputs. The optimizers can only perform a fraction of all optimizations; some of
them can only be done in backend implementation, as mentioned in this [doc](https://github.com/onnx/onnx/blob/v1.3.0/docs/Optimizer.md).

As an example, run:

```console
python optimize_model.py
```

**TensorProto and Numpy Array**

In deep learning framework, tensor is represented as numpy array. In onnx, we can manipulate tensor
protocol buffer with numpy, e.g.

```console
python nparray_tensorproto.py
```

In the example, we create a numpy array and convert it a TensorProto, defined in [onnx.proto](https://github.com/onnx/onnx/blob/v1.3.0/onnx/onnx.proto).
We can also load a TensorProto and convert it to a numpy array.

**Shape Inference**

To inference shape of a tensor, use `shape_inference.infer_shapes(model)`.

```console
python shape_inference.py
```

In the example, onnx is able to find out that shape of Y is [3,2,4]. Similar to optimiation and
others, the inference logic is implemented in C, see [here](https://github.com/onnx/onnx/tree/v1.3.0/onnx/shape_inference).

*How it works*

There are two pieces of information used in shape inference:
- shape of X and Z are both (2,3,4)
- permutation is (1,0,2)

Permutation means that the original first dimension now becomes the second dimension; the original
second dimension becomes the first dimension; and the last dimension stays the same.

## End-to-end Examples

**Pytorch**

The `simple_export.py` contains a two layer network, to export a model we use `torch.onnx.export`, e.g.

```python
dummy_input = torch.autograd.Variable(torch.randn(D_in))
torch.onnx.export(model, dummy_input, "/tmp/simple.onnx", verbose=True)
```

Note that the `dummy_input` is required to provide input shape. For more detailed examples, see
`alexnet_export.py` & `import_caffe2.py`. The onnx conversion code is part of pytorch and caffe2
codebase.

For more information: https://pytorch.org/docs/stable/onnx.html

**TensorFlow**

The `import_tensorflow.py` script loads a super_resolution model in onnx format and converts it to
a tensorflow representation. The conversion is done in the official [onnx-tensorflow library](https://github.com/onnx/onnx-tensorflow).
It works by examining the model and creating a tensorflow graph step by step, i.e.

```python
# defined in onnx_tf/backend.py

@classmethod
def _onnx_graph_to_tensorflow_rep(cls, graph_def, opset, strict):
  """ Convert ONNX graph to TensorflowRep.

  :param graph_def: ONNX GraphProto object.
  :param opset: ONNX OperatorSetIdProto list.
  :param strict: whether to enforce semantic equivalence between the original model
    and the converted tensorflow model.
  :return: TensorflowRep object.
  """
  handlers = cls._get_handlers(opset)

  tf_rep_graph = tf.Graph()
  with tf_rep_graph.as_default():
    # initializer: TensorProtos representing the values to initialize
    # a given tensor.
    # initialized: A list of names of the initialized tensors.
    if graph_def.initializer:
      input_dict_items = cls._onnx_initializer_to_input_dict_items(
          graph_def.initializer)
      initialized = {init.name for init in graph_def.initializer}
    else:
      input_dict_items = []
      initialized = set()

    # creating placeholders for currently unknown inputs
    for value_info in graph_def.input:
      if value_info.name in initialized:
        continue
      shape = list(
          d.dim_value if (d.dim_value > 0 and d.dim_param == "") else None
          for d in value_info.type.tensor_type.shape.dim)
      x = tf.placeholder(
          data_type.onnx2tf(value_info.type.tensor_type.elem_type),
          name=value_info.name,
          shape=shape)
      input_dict_items.append((value_info.name, x))

    # tensor dict: this dictionary is a map from variable names
    # to the latest produced TF tensors of the given name.
    # This dictionary will get updated as we build the graph to
    # record the names of newly produced tensors.
    tensor_dict = dict(input_dict_items)
    # Since tensor dict may be updated, we need to keep a copy
    # of the original input dict where we track the earliest
    # defined tensors so we can have access to the placeholders
    # to feed in input tensors when we run the graph.
    input_dict = dict(input_dict_items)

    for node in graph_def.node:
      onnx_node = OnnxNode(node)
      output_ops = cls._onnx_node_to_tensorflow_op(
          onnx_node, tensor_dict, handlers, opset=opset, strict=strict)
      curr_node_output_map = dict(zip(onnx_node.outputs, output_ops))
      tensor_dict.update(curr_node_output_map)

  tf_rep = TensorflowRep()
  tf_rep.graph = tf_rep_graph
  tf_rep.inputs = [
      value_info.name
      for value_info in graph_def.input
      if value_info.name not in initialized
  ]
  tf_rep.outputs = [value_info.name for value_info in graph_def.output]
  tf_rep.tensor_dict = tensor_dict
  return tf_rep
```

# Projects

## onnx-tensorflow

[onnx-tensorflow](https://github.com/onnx/onnx-tensorflow) is the official onnx implementation
(backend and frontend) in TensorFlow. Inference using onnx-tensorflow essentially parses onnx model
and uses tensorflow session.run().

For more information, refer to `import_tensorflow.py` under experiments directory.

## onnxruntime

[onnxruntime](https://github.com/microsoft/onnxruntime) is an inference engine for ONNX, from
[Microsoft blog](https://azure.microsoft.com/en-us/blog/onnx-runtime-integration-with-nvidia-tensorrt-in-preview/):

> ONNX Runtime is the first publicly available inference engine with full support for ONNX 1.2 and
> higher including the ONNX-ML profile. ONNX Runtime is lightweight and modular with an extensible
> architecture that allows hardware accelerators such as TensorRT to plug in as "execution providers."
> These execution providers unlock low latency and high efficiency neural network computations.
> Today, ONNX Runtime powers core scenarios that serve billions of users in Bing, Office, and more.

onnxruntime includes a [default execution provider](https://github.com/microsoft/onnxruntime/tree/v1.1.0/onnxruntime/core/providers/cpu)
that gurantees to support all onnx operators, other execution providers include openvino, cuda,
dnnl (was mkl-dnn), etc. All providers provide `GetCapability` to indicate supported operations,
and onnxruntime will fall back to default one if certain operations are not supported.

Using onnxruntime is simple, e.g.

```
import onnxruntime

sess = onnxruntime.InferenceSession(example_model)
result = sess.run([output_name], {input_name: x})
```
