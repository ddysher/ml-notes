<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Concetps](#concetps)
  - [Dynamic Graph](#dynamic-graph)
  - [Torch.JIT](#torchjit)
- [PyTorch APIs](#pytorch-apis)
  - [Python API](#python-api)
  - [C++ API](#c-api)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Concetps

## Dynamic Graph

Dynamic graph means that we can use python native code to construct graph, and the graph will be
constructed for each sample. `dynamic_graph.py` has an example network that utilizes the concepts
(copied from this [discussion](https://discuss.pytorch.org/t/what-is-truly-happening-when-we-define-dynamic-graph-models/23669)).

Also, due to the dynamic characteristics of pytorch, saving model is less intuitive than other
static graph based framework, where the whole model (graph) and parameters can be serialized, e.g.
tensorflow SavedModel. There are two recommended approaches in pytorch:
- The first (recommended) saves and loads only the model parameters, using `torch.save` and
  `torch.load_state_dict`. This approach assumes that we have access to source code.
- The second saves and loads the entire model, using `torch.save` and `torch.load`. Under the hood,
  this is actually to pickle our in-memory model object to persist disk, unlike in static graph based
  framework, where the graph structure is persisted instead of in-memory model object. As mentioned
  in official doc, in this case, the serialized data is bound to the specific classes and the exact
  directory structure used, so it can break in various ways when used in other projects, or after
  some serious refactors.

## Torch.JIT

Since PyTorch is dynamic, it never knows what operations will be executed next, which makes it hard
to perform optimization. There are two features proposed in pytorch v1.0 to help solve the problem:
- tracing mode
- script mode

Basically, in tracing mode, we provide an example input to pytorch to execute our model, and it
records all native pytorch operations. However, it's hard for tracing mode to trace dynamic part
and control flow. In script mode, we annotate our model function to 'hint' pytorch to transform
our model to high-performance C++ runtime. Python code written in this model function cannot use
complicated language features: there is always tradeoffs. In another word, TorchScript can be seen
as a **slimed-down version of Python**, with few custom decorations.

Torch.jit feature can be used gradually: PyTorch will not sacrifice usability. For example, tracing
only 20% of a model, and whenever appropriate, trace more portion of the model.

**PyTorch v1.0**

[The blog](https://pytorch.org/2018/05/02/road-to-1.0.html) is an important summary of PyTorch
characteristics. PyTorch excels at first-class python support, which means users can create neural
networks by just using imperative python language (compare with other frameworks where users have
to pre-declare the networks). However, this flexibility has its drawbacks: it's hard to perform
optimization, export to different runtime, etc, which makes pytorch a framework mostly used for
research. PyTorch 1.0 aims to solve the problems by making it support both quick prototype as well
as production efficiency. There are quite a few creative solutions mentioned in the blog which will
be merged into 1.0 release, notably, tracing/script mode and libtorch C++ API.

*References*

- [pytorch-1-0-tracing-jit-and-libtorch-c-api-to-integrate-pytorch-into-nodejs](http://blog.christianperone.com/2018/10/pytorch-1-0-tracing-jit-and-libtorch-c-api-to-integrate-pytorch-into-nodejs/)
- https://blog.algorithmia.com/exploring-the-deep-learning-framework-pytorch/
- https://towardsdatascience.com/a-first-look-at-pytorch-1-0-8d3cce20b3ee

# PyTorch APIs

## Python API

[PyTorch Python API](https://pytorch.org/docs/stable/torch.html) is the goto APIs for writing
PyTorch models.

## C++ API

[PyTorch C++ API](https://pytorch.org/cppdocs/) provides APIs accessing core PyTorch capabilities
using C++, which can be divided into five parts:
- ATen: The foundational tensor and mathematical operation library on which all else is built;
- Autograd: Augments ATen with automatic differentiation;
- C++ Frontend: High level constructs for training and evaluation of machine learning models (like python API);
- TorchScript: An interface to the TorchScript JIT compiler and interpreter;
- C++ Extensions: A means of extending the Python API with custom C++ and CUDA routines.

Using C++ API is useful in several cases:
- deploy PyTorch model to devices without dependencies on python
- add custom operations with CUDA or other libraries
- etc
