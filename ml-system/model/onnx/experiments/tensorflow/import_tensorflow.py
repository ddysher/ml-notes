# From:
#   https://github.com/onnx/tutorials/blob/master/tutorials/OnnxTensorflowImport.ipynb
# with analysis.

import onnx
import warnings
from onnx_tf.backend import prepare

warnings.filterwarnings('ignore') # Ignore all the warning messages in this tutorial

#
# Now that we have an ONNX model file ready, let's import it into Tensorflow using
# ONNX-Tensorflow's import API.
#

# 'onnx.load' here basically loads .onnx file and deserializes it into ModelProto.
# 'prepare' here calls internal 'onnx_graph_to_tensorflow_rep', which walks through
# the graph (node, input, etc) and creates a tensorflow graph. For different node,
# it calls handlers which return tensorflow node, e.g. abs, sigmod, etc.
model = onnx.load('assets/super_resolution.onnx')
tf_rep = prepare(model)       # tensorflow representation of the model

#
# Now we have tf_rep, which is a python class containing four members: graph, inputs,
# outputs, and tensor_dict.
#

print(tf_rep.inputs)
print('-----')
print(tf_rep.outputs)
print('-----')
print(tf_rep.tensor_dict)

#
# Next, we will prepare an input image for inference. The steps below downloads
# an example image, resizes it to the model's expected input shape, and finally
# converts it into a numpy array.
#

import numpy as np
from IPython.display import display
from PIL import Image

img = Image.open('assets/super-res-input.jpg').resize((224, 224))
display(img)                    # show the image
img_ycbcr = img.convert("YCbCr")
img_y, img_cb, img_cr = img_ycbcr.split()
doggy_y = np.asarray(img_y, dtype=np.float32)[np.newaxis, np.newaxis, :, :]

#
# Now run inference.
#

# 'tf_rep.run' basically uses the above graph (tf_rep.graph) and calls sess.run().
big_doggy = tf_rep.run(doggy_y)._0
print(big_doggy.shape)

#
# Examine the results.
#

img_out_y = Image.fromarray(np.uint8(big_doggy[0, 0, :, :].clip(0, 255)), mode='L')
result_img = Image.merge("YCbCr", [
  img_out_y,
  img_cb.resize(img_out_y.size, Image.BICUBIC),
  img_cr.resize(img_out_y.size, Image.BICUBIC),
]).convert("RGB")
display(result_img)
result_img.save('output/super_res_output.jpg')
