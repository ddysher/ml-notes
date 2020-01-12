<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Design](#design)
  - [Intermediate Representation (IR)](#intermediate-representation-ir)
  - [Commands](#commands)
- [Workflow](#workflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[MMdnn](https://github.com/microsoft/MMdnn) is a tool for deep learning model conversion between two
different frameworks.

# Design

## Intermediate Representation (IR)

MMdnn provides its own IR, which has limited set of operators:
- [ops.pbtxt](https://github.com/microsoft/MMdnn/blob/0.2.5/mmdnn/conversion/common/IR/ops.pbtxt)
- [graph.proto](https://github.com/microsoft/MMdnn/blob/0.2.5/mmdnn/conversion/common/IR/graph.proto)

Example operators include: Conv, FullyConnected, Maxpool, Dropout, Add, Relu, etc. To add new
unsupported operators, one needs to follow [contribution guideline](https://github.com/Microsoft/MMdnn/wiki/Contribution-Guideline).
Terms used in IR:
- parser: each framework has a parser, which parses source framework model and converts it to IR
  - parsing is done using framework library to load the graph and convert to IR layer by layer
- emiter: each framework has an emiter, which emits IR to destination framework python code
  - emitting is done via reading the IR graph and write out pre-defined python source code layer by layer
- saver: each frameowkr has a saver, which saves model python source to disk.
  - saving process is done via loading the python soruce code using `imp` package, and calling framework
    specific `save` method, e.g. in keras, it simply calls `model.save`.

All conversion logics reside in [conversions](https://github.com/microsoft/MMdnn/blob/0.2.5/mmdnn/conversion),
grouped by framework. The core methods include:
- `gen_IR`: generates IR from source framework
- `gen_code`: generates python code from IR
- `save_model`: generates model artifacts using loaded python source module
- `rename_[ops]`: convert specific operation to IR, called from `gen_IR`
- `emit_[ops]`: convert specific operation from IR, called from `gen_code`
- `_layer_[ops]`: pre-defined framework source code for an operation

Not that not all framework support conversion from/to IR.

## Commands

The main commands used in MMdnn is:
- `mmdownload`: download models of a pre-trained model from specific framework
- `mmconvert`: a one-step command to convert models between two frameworks
- `mmtoir`: convert pre-trained model files to intermediate representation
- `mmtocode`: convert IR files to original framework code
- `mmtomodel`: dump the original model

# Workflow

Conversion happends in the following order:
- Source model is converted into IR via `convertToIR._convert`.
  - Output from this step is IR network structure (.pb) and weights (.npy).
- IR is converted into destination framework source code via `IRToCode._convert`.
  - Output from this step is python code.
- Destimation model source code is dumped into binary model via `dump_code`.
  - Output from this step is model artifact.

**convert from keras to cntk**

Download keras model:

```
$ mmdownload -f keras -n resnet50 -o ./
```

Convert keras model to IR:

```
$ mmtoir -f keras -w imagenet_resnet50.h5 -o converted
$ ll
-rw-rw-r-- 1 deyuan deyuan 167K Aug  3 07:49 converted.json
-rw-rw-r-- 1 deyuan deyuan 148M Aug  3 07:49 converted.npy
-rw-rw-r-- 1 deyuan deyuan  26K Aug  3 07:49 converted.pb
-rw-rw-r-- 1 deyuan deyuan  99M Aug  3 07:39 imagenet_resnet50.h5
```

Convert IR to code:

```
mmtocode -f cntk -d converted_cntk.py -n converted.pb -w converted.npy
$ ll
-rw-rw-r-- 1 deyuan deyuan 167K Aug  3 07:49 converted.json
-rw-rw-r-- 1 deyuan deyuan  31K Aug  3 09:59 converted_keras.py
-rw-rw-r-- 1 deyuan deyuan 148M Aug  3 07:49 converted.npy
-rw-rw-r-- 1 deyuan deyuan  26K Aug  3 07:49 converted.pb
-rw-rw-r-- 1 deyuan deyuan  99M Aug  3 07:39 imagenet_resnet50.h5
```

Convert to binary model:

```
mmtomodel -f cntk -in converted_cntk -iw converted.npy -o cntk_resnet50.dnn
```
