# OpenVINO

Intel OpenVINO (Open Visual Inference and Neural network Optimization) is a toolkit to
quickly deploys vision-based applications and solutions. It is very similar to Nvidia TensorRT.
At its core, it contains:
- A model optimizer that optimizes and converts models from deep learning frameworks
- A model inference engine that serves converted models
- Optimized libraries for Intel hardware, e.g. OpenCV

A typical workflow when using OpenVINO:
- Train or download a vision model from deep learning frameworks.
- Use the Model Optimizer to convert the model to the `.bin` and `.xml` Intermediate Representation (IR) files.
- Run OpenVINO inference engine.

OpenVINO is suitable for:
- optimized inference on Intel hardware
- edge environment

**Model Optimizer**

The Model Optimizer is a Python-based command line tool for importing trained models from popular
deep learning frameworks such as Caffe, TensorFlow, Apache MXNet, ONNX and Kaldi. The Model Optimizer
is a key component of the Intel Distribution of OpenVINO toolkit. You cannot perform inference on
your trained model without running the model through the Model Optimizer.

**Model Inference Engine**

The Inference Engine is a C++ library with a set of C++ classes to infer input data (images) and get
a result. The C++ library provides an API to read the Intermediate Representation, set the input and
output formats, and execute the model on devices.

*References*

- https://docs.openvinotoolkit.org/latest/index.html
- https://mc.ai/optimizing-neural-networks-for-production-with-intels-openvino/
- https://medium.com/@rachittayal7/getting-started-with-openvino-serving-3810361a7368
- https://medium.com/sugarkubes/openvino-quickstart-9501e6be2db9
