<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Road to v1.0](#road-to-v10)
  - [References](#references)
- [Dynamic Graph & Serialization](#dynamic-graph--serialization)
- [Experiments](#experiments)
  - [Learning PyTorch with Examples](#learning-pytorch-with-examples)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Road to v1.0

[The blog](https://pytorch.org/2018/05/02/road-to-1.0.html) is an important summary of pytorch
characteristics. PyTorch excels at first-class python support, which means users can create neural
networks by just using imperative python language (compare with other frameworks where users have
to pre-declare the networks). However, this flexibility has its drawbacks: it's hard to perform
optimization, export to different runtime, etc, which makes pytorch a framework mostly used for
research. PyTorch 1.0 aims to solve the problems by making it support both quick prototype as well
as production efficiency. There are quite a few creative solutions mentioned in the blog which will
be merged into 1.0 release.

**torch.jit (tracing & script)**

Since pytorch is dynamic, it never knows what operations will be executed next, which makes it hard
to perform optimization. There are two features proposed in pytorch v1.0 to help solve the problem:
- tracing mode
- script mode

Basically, in tracing mode, we provide an example input to pytorch to execute our model, and it
records all native pytorch operations. However, it's hard for tracing mode to trace dynamic part
and control flow. In script mode, we annotate our model function to 'hint' pytorch to transform
our model to high-performance C++ runtime. Python code written in this model function cannot use complicated
language features: there is always tradeoffs.

**Usability**

PyTorch v1.0 will not sacrifice usability for performance, and the above torch.jit feature can also
be used gradually. For example, tracing only 20% of a model, and whenever appropriate, trace more
portion of the model.

## References

- https://blog.algorithmia.com/exploring-the-deep-learning-framework-pytorch/

# Dynamic Graph & Serialization

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

# Experiments

## Learning PyTorch with Examples

- https://pytorch.org/tutorials/beginner/pytorch_with_examples.html
