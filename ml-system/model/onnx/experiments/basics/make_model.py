#!/usr/bin/env python

import onnx
from onnx import helper
from onnx import AttributeProto, TensorProto, GraphProto

# The protobuf definition can be found here:
# https://github.com/onnx/onnx/blob/master/onnx/onnx.proto

# Create one input (ValueInfoProto)
X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1, 2])

# Create one output (ValueInfoProto)
Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1, 4])

# Create a node (NodeProto)
node_def = helper.make_node(
    'Pad', # node name
    ['X'], # inputs
    ['Y'], # outputs
    mode='constant', # attributes
    value=1.5,
    pads=[0, 1, 0, 1],
)

# Create the graph (GraphProto)
graph_def = helper.make_graph(
    [node_def],
    'test-model',
    [X],
    [Y],
)

# Create the model (ModelProto)
model_def = helper.make_model(graph_def, producer_name='onnx-example')

print('The model is:\n{}'.format(model_def))
onnx.checker.check_model(model_def)
print('The model is checked!')
