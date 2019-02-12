#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import onnx
import os

onnx_model = onnx.load(os.path.join('resources', 'single_relu.onnx'))
print(onnx_model)
