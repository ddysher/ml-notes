#!/usr/bin/env python2.7
#
# https://medium.com/epigramai/tensorflow-serving-101-pt-2-682eaf7469e7

import argparse
import logging

from predict_client.prod_client import ProdClient

# Make logging work.
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Parse arguments.
parser = argparse.ArgumentParser(description='Process arguments.')
parser.add_argument('--host', type=str, default='localhost:9000')
parser.add_argument('--model_name', type=str, default='simple')
parser.add_argument('--model_version', type=int, default=1)
args = parser.parse_args()

client = ProdClient(args.host, args.model_name, args.model_version)
# Note in_tensor_name ‘a’ is the same ‘a’ that we used in the signature
# definition in our model. The input tensor’s data type must also match
# the one of the placeholder a in our model.
req_data = [{'in_tensor_name': 'a', 'in_tensor_dtype': 'DT_INT32', 'data': 2}]
print(client.predict(req_data))
