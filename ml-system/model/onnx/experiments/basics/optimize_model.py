#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import onnx
import os
from onnx import optimizer

# Preprocessing: load the model contains two transposes.
model_path = os.path.join('resources', 'two_transposes.onnx')
original_model = onnx.load(model_path)

print('The model before optimization:\n{}'.format(original_model))

# A full list of supported optimization passes can be found using get_available_passes()
all_passes = optimizer.get_available_passes()
print("Available optimization passes:")
for p in all_passes:
  print('- ' + p)
print()

# Pick one pass as example
passes = ['fuse_consecutive_transposes']

# Apply the optimization on the original serialized model
optimized_model = optimizer.optimize(original_model, passes)

print('The model after optimization:\n{}'.format(optimized_model))
