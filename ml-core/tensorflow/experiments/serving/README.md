## Tensorflow Serving (r1.4)

### Hello World

- https://medium.com/epigramai/tensorflow-serving-101-pt-1-a79726f7c103
- https://medium.com/epigramai/tensorflow-serving-101-pt-2-682eaf7469e7

#### Build

```
git clone --recurse-submodules https://github.com/tensorflow/serving
cd serving
bazel build -c opt //tensorflow_serving/model_servers:tensorflow_model_server
```

#### Training:

Enter 'helloworld' directory:

```
python model.py --model_dir=/tmp/simple_model --model_version=1
```

This will save our model to `/tmp/simple_model/1`.

#### Serving:

```
tensorflow_model_server --port=9000 --model_name=simple --model_base_path=/tmp/simple_model
```

#### Inference:

```
python client.py --host=localhost:9000 --model_name=simple --model_version=1
```

#### Look into SavedModel

Back to top-level:

```
python inspect_savedmodel.py --model_dir=/tmp/simple_model/1
```

#### Create new model

Enter 'helloworld' directory; edit model.py to use different placeholder name, e.g. 'a' -> 'x'

```
python model.py --model_dir=/tmp/simple_model --model_version=2
```

This will save our model to `/tmp/simple_model/2`.

Now both of the following inferences will fail:

```
python client.py --host=localhost:9000 --model_name=simple --model_version=1
python client.py --host=localhost:9000 --model_name=simple --model_version=2
```

The first one fails because model 1 is unloaded; the second one fails because
model 2 uses different tensor input alias. If we change client code's input
tensor name 'in_tensor_name' from 'a' -> 'x', the second one will succeed. Note
all the above behavior is the standard serving binary; we can customize the
behavior by building custom serving binary.

### Official basic tutorial

https://github.com/tensorflow/tensorflow/blob/r1.4/tensorflow/python/saved_model/README.md

#### Training and Export

Enter 'basics' directory, example run:

```sh
$ rm -rf /tmp/mnist_model && mkdir -p /tmp/mnist_model

$ python mnist_saved_model.py /tmp/mnist_model
$ python mnist_saved_model.py --model_version=2 /tmp/mnist_model
```

#### Serving

```sh
tensorflow_model_server --port=9000 --model_name=mnist --model_base_path=/tmp/mnist_model/
```

#### Inference

```sh
python mnist_client.py --num_tests=100 --server=localhost:9000
```

#### Look into SavedModel

Back to top-level:

```sh
python inspect_savedmodel.py
```

### Multiple Models

Create two models:

```
python helloworld/model.py --model_dir=/tmp/simple_model  --model_version=1
python helloworld/model.py --model_dir=/tmp/another_model --model_version=1
python helloworld/model.py --model_dir=/tmp/another_model --model_version=2
```

Run serving binary:

```
tensorflow_model_server --port=9000 --model_config_file=./multiple/model_config.json
```

Inference (model name comes from the config file):

```
python client.py --host=localhost:9000 --model_name=model1 --model_version=1
```
