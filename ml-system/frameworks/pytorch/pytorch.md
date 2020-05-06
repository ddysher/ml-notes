<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Concetps](#concetps)
  - [Dynamic Graph](#dynamic-graph)
  - [Torch.JIT](#torchjit)
- [PyTorch APIs](#pytorch-apis)
  - [Python API](#python-api)
  - [C++ API](#c-api)
- [Projects](#projects)
  - [Captum](#captum)
  - [Elastic](#elastic)
  - [TorchServe](#torchserve)

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

# Projects

## Captum

[Captum](https://github.com/pytorch/captum) helps you interpret and understand predictions of PyTorch
models by exploring features that contribute to a prediction the model makes. It also helps understand
which neurons and layers are important for model predictions.

Currently, the library uses gradient-based interpretability algorithms and attributes contributions
to each input of the model with respect to different neurons and layers, both intermediate and final.

<details><summary>sample.py</summary><p>

```
import numpy as np

import torch
import torch.nn as nn

from captum.attr import (
    GradientShap,
    DeepLift,
    DeepLiftShap,
    IntegratedGradients,
    LayerConductance,
    NeuronConductance,
    NoiseTunnel,
)

class ToyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(3, 3)
        self.relu = nn.ReLU()
        self.lin2 = nn.Linear(3, 2)

        # initialize weights and biases
        self.lin1.weight = nn.Parameter(torch.arange(-4.0, 5.0).view(3, 3))
        self.lin1.bias = nn.Parameter(torch.zeros(1,3))
        self.lin2.weight = nn.Parameter(torch.arange(-3.0, 3.0).view(2, 3))
        self.lin2.bias = nn.Parameter(torch.ones(1,2))

    def forward(self, input):
        return self.lin2(self.relu(self.lin1(input)))

model = ToyModel()
model.eval()

torch.manual_seed(123)
np.random.seed(123)

input = torch.rand(2, 3)
baseline = torch.zeros(2, 3)

ig = IntegratedGradients(model)
attributions, delta = ig.attribute(input, baseline, target=0, return_convergence_delta=True)
print('IG Attributions:', attributions)
print('Convergence Delta:', delta)
```

</p></details></br>

Output:

```
IG Attributions: tensor([[-0.5922, -1.5497, -1.0067],
                         [ 0.0000, -0.2219, -5.1991]])
Convergence Delta: tensor([2.3842e-07, -4.7684e-07])
```

> Positive attribution score means that the input in that particular position positively contributed
> to the final prediction and negative means the opposite. The magnitude of the attribution score
> signifies the strength of the contribution. Zero attribution score means no contribution from that
> particular feature.

## Elastic

- *Date: 02/27/2020, v0.1.0rc1*

PyTorch Elastic (torchelastic) is a library that enables distributed training jobs to be executed in
a fault tolerant and elastic manner; that is, your distributed job is able to start as soon as `min`
number of workers are present and allowed to grow up to `max` number of workers without being stopped
or restarted.

To use torchelastic, users need to provide two core methods:
- `sync`: in case of membership change (training start/resume, member joining, etc), `sync` performs
  synchronization tasks such as state sync, model init, data loader init, etc
- `train_step`: the unit of work in training, called from torchelastic during training loop

The synchronization process is called `Rendezvous`, as mentioned above, each time there is a change
in membership in the set of workers, torchelastic runs a rendezvous. torchelastic provides a default
implementation based on etcd, but custom Rendezvous can be implemented as long as it satifies Rendezvous
interface. The core of Rendezvous are:
- barrier - all nodes will block until rendezvous is complete before resuming execution.
- role assignment - on each rendezvous each node is assigned a unique integer valued rank between
  [0, n) where n is the world size (total number of workers).
- world size broadcast - on each rendezvous all nodes receive the new world_size.

For more information:
- [how torchelastic works](https://github.com/pytorch/elastic/tree/v0.1.0rc1#how-torchelastic-works)
- [torchelastic on kubernetes](https://github.com/pytorch/elastic/tree/c0a5436539a2f0cea0b15bf551f05465e9ae3f74/kubernetes)
- [torchelastic usage](https://github.com/pytorch/elastic/blob/v0.1.0rc1/USAGE.md)
- [checkpoint](https://github.com/pytorch/elastic/tree/v0.1.0rc1/torchelastic/checkpoint)
- [rendezvous](https://github.com/pytorch/elastic/tree/v0.1.0rc1/torchelastic/rendezvous)
- [metrics](https://github.com/pytorch/elastic/tree/v0.1.0rc1/torchelastic/metrics)

## TorchServe

- *Date: 04/27/2020, v0.1.0*

TorchServe is a new open-source model serving library & system under the PyTorch project. Features
of TorchServe include:
- APIs: Prediction APIs (e.g. for image prediction) and Management APIs (e.g. for registering models)
- Secure HTTPS Deployment
- Model Management: Full configuration of models
- Model Archival: A `.mar` file format that packages a model, parameters and supporting into a single file
- Model Handler: Handling inference logic, TorchServe provides built-in handles as well as custom handlers
- Logging and Metrics
- Prebuilt Images: Ready to use docker images

The core of TorchServe is `Model Archival` and the real inference logic resides in `Model Handler`.
TorchServe has a convention for how a handler should be written, and all default handlers conforms
to the convention. For default handlers, see [torch_handler](https://github.com/pytorch/serve/tree/v0.1.0/ts/torch_handler);
for an example custom handler, see [mnist example](https://github.com/pytorch/serve/tree/v0.1.0/examples/image_classifier/mnist).
Typically, the handlers will preprocess the data, load the model, run the inference, and postprocess
the result.

Quick demo:

```bash
# Install TorchServe:
pip install --upgrade torch torchtext torchvision sentencepiece
pip install -f https://download.pytorch.org/whl/torch_stable.html torchserve torch-model-archiver

# Prepare model boundle `mar` file:
wget https://download.pytorch.org/models/densenet161-8d451a50.pth
torch-model-archiver --model-name densenet161 --version 1.0 --model-file examples/image_classifier/densenet_161/model.py --serialized-file densenet161-8d451a50.pth --handler image_classifier --extra-files examples/image_classifier/index_to_name.json

# Prepare model store and start serving:
mkdir model_store
mv densenet161.mar model_store/
torchserve --start --model-store model_store --models densenet161=densenet161.mar
curl -X POST http://127.0.0.1:8080/predictions/densenet161 -T examples/image_classifier/kitten.jpg

# To stop:
torchserve --stop
```

For more information:
- [TorchServe Blog ANN](https://medium.com/pytorch/torchserve-and-torchelastic-for-kubernetes-new-pytorch-libraries-for-serving-and-training-models-2efd12e09adc)
- [Running TorchServe](https://github.com/pytorch/serve/blob/v0.1.0/docs/server.md)
- [Torch Model archiver for TorchServe](https://github.com/pytorch/serve/tree/v0.1.0/model-archiver)
- [Custom Service](https://github.com/pytorch/serve/blob/v0.1.0/docs/custom_service.md)
