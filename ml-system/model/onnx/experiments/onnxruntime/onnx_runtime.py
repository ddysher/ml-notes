# https://github.com/onnx/onnx-docker/blob/master/onnx-ecosystem/inference_demos/simple_onnxruntime_inference.ipynb

import onnxruntime
import numpy as np
from onnxruntime.datasets import get_example

# Load a simple onnx model and create an inference session.
example_model = get_example("sigmoid.onnx")
sess = onnxruntime.InferenceSession(example_model)

input_name = sess.get_inputs()[0].name
print("Input name  :", input_name)
input_shape = sess.get_inputs()[0].shape
print("Input shape :", input_shape)
input_type = sess.get_inputs()[0].type
print("Input type  :", input_type)

output_name = sess.get_outputs()[0].name
print("Output name  :", output_name)
output_shape = sess.get_outputs()[0].shape
print("Output shape :", output_shape)
output_type = sess.get_outputs()[0].type
print("Output type  :", output_type)

x = np.random.random(input_shape)
x = x.astype(np.float32)

result = sess.run([output_name], {input_name: x})
print(result)
