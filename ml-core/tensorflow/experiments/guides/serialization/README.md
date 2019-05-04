<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Serialization](#serialization)
  - [Checkpoint](#checkpoint)
    - [Save Checkpoint](#save-checkpoint)
    - [Restore Checkpoint](#restore-checkpoint)
  - [Frozen Model](#frozen-model)
    - [Freeze Model](#freeze-model)
    - [Load Frozen Model](#load-frozen-model)
    - [Serve Frozen Model](#serve-frozen-model)
  - [SavedModel](#savedmodel)
    - [From Source](#from-source)
    - [From Checkpoint](#from-checkpoint)
    - [From Frozen Model](#from-frozen-model)
    - [Run Pretained SavedModel](#run-pretained-savedmodel)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Serialization

## Checkpoint

Checkpoint is mainly used for restarting training via saving/restore variables.

### Save Checkpoint

Run the following command to save checkpoint:

```
python checkpoint_save.py
```

The core for checkpoint is:

```
saver = tf.train.Saver()
last_ckpt = saver.save(sess, 'results/graph.ckpt')
```

Note there is not a physical file called graph.ckpt. It is the prefix of filenames created for the
checkpoint. Users only interact with the prefix instead of physical checkpoint files.

```
$ ls results
checkpoint  graph.ckpt.data-00000-of-00001  graph.ckpt.index  graph.ckpt.meta  graph.ckpt.meta.json
```

Here:
- The `.index` file holds an immutable key-value table linking a serialised tensor name and where to
  find its data in the chkp.data files
- The `.data` files hold the data (weights) itself (this one is usually quite big in size). There can
  be many data files because they can be sharded and/or created on multiple timesteps while training.

By default, `saver.save` also write_meta_graph to file `graph.ckpt.meta`, which is the protocol
buffer data for `MetaGraphDef`. The schema of the protocol buffer can be found at "tensorflow/tensorflow/core/protobuf",
and some other definitions can be found at "tensorflow/tensorflow/core/framework". MetaGraphDef
contains enough information to restart training, run inference. The behavior can be turned off by
setting write_meta_graph=False.

Note the proto definition (MetaGraphDef) is NOT SavedModel: SavedModel contains a listof MetaGraphDef.

```proto
message SavedModel {
  int64 saved_model_schema_version = 1;
  repeated MetaGraphDef meta_graphs = 2;
}
```

### Restore Checkpoint

Run the following command to restore checkpoint:

```
python checkpoint_restore.py
```

The script use `tf.train.import_meta_graph` to restore the graph from `graph.ckpt.meta` file,
thus we'll be able to find all tensors, operations.

In addition, we restore the variables with `saver.restore`, which can **only** restore variables.
Since weights (variables) have meanings only when used in session, thus we need to restore the
weights under a session. The best way to understand the restore operation is to see it simply as a
kind of initialisation.

## Frozen Model

Frozen Model typically removes all training information, converts all variables to constants. It
has only a single file, so suitable for serving and transfer to mobile or embeded devices to load,
etc.

### Freeze Model

Run the following command to freeze model:

```
python freezemodel_save.py
```

Freezing model is usually done with:

```
tf.graph_util.convert_variables_to_constants()
```

Then

```
with tf.gfile.GFile(output_graph, "wb") as f:
  f.write(output_graph_def.SerializeToString())
```

The output is `results/frozen_model.pb`, which is defined as `GraphDef`. Note here
`GraphDef = MetaGraphDef.GraphDef`.

### Load Frozen Model

Run the following command to load freezed model:

```
python freezemodel_load.py
```

Here we load the model and do a simple forward calculation. The input and output are:

```python
x = graph.get_tensor_by_name('prefix/Placeholder/inputs_placeholder:0')
y = graph.get_tensor_by_name('prefix/Accuracy/predictions:0')
```

### Serve Frozen Model

Serving frozen model creates a flask server, and for each request, runs a forward calculation.

```
python freezemodel_serve.py
```

The request looks like:

```
$ curl -X POST -H "Content-Type: application/json" http://localhost:5000/api/predict -d '{"x": [[0,1,2,3,4,5,6,7,8,9]]}'
{"y": [[false]]}

$ curl -X POST -H "Content-Type: application/json" http://localhost:5000/api/predict -d '{"x": [[0,1,2,3,4,5,6,7,8,9],[5,5,5,5,5,5,5,5,5,5]]}'
{"y": [[false], [true]]}
```

## SavedModel

SavedModel contains all information of a model, thus we can restart training, do inference, etc.

### From Source

Run the following command to create SavedModel:

```
python savedmodel_from_source.py
```

The script uses `tf.saved_model.simple_save()` to create model. Pay attention to the `inputs` and
`outputs` parameters, which are required signature for SavedModel.

Internally, `simple_save()` uses the same logic to create SavedModel, i.e.
- Use `saver.save()` to save variables
- Use `saver.export_meta_graph` to export meta graph

It then adds the graph to SavedModel. In addition, signature_def and tags are added to the SavedModel
as well. Each SavedModel can have multiple signatures, each has a unique name. In simple_save, the
default one is used, i.e. `signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY`.

### From Checkpoint

Run the following command to create SavedModel:

```
python savedmodel_from_checkpoint.py
```

The core flow is:
- import meta graph (MetaGraphDef)
- restore variables
- figure out signature
- then save model

We can use `saved_model_cli` to inspect the model:

```
$ saved_model_cli show --dir /tmp/tfckptmodel --all

MetaGraphDef with tag-set: 'serve' contains the following SignatureDefs:

signature_def['serving_default']:
  The given SavedModel SignatureDef contains the following input(s):
    inputs['inputs_1'] tensor_info:
        dtype: DT_FLOAT
        shape: (-1, 10)
        name: Placeholder/inputs_placeholder:0
  The given SavedModel SignatureDef contains the following output(s):
    outputs['output1'] tensor_info:
        dtype: DT_BOOL
        shape: (-1, 1)
        name: Accuracy/predictions:0
  Method name is: tensorflow/serving/predict
```

```
$ saved_model_cli run --dir /tmp/tfckptmodel --tag_set serve --signature_def serving_default --input_exprs="inputs_1=[[0,1,2,3,4,5,6,7,8,9]]"
Result for output key output1:
[[False]]
```

### From Frozen Model

Run the following command to create SavedModel:

```
python savedmodel_from_frozen.py
```

The core flow is:
- read the graph (GraphDef)
- load into current graph
- then save model

Note since all variables are converted to constants during freezing, `variables` directory is empty
for this SavedModel.

### Run Pretained SavedModel

Run the following command to load and run pretrained model:

```
python savedmodel_pretrained.py
```

Information like 'serve', 'input_tensor:0', etc, can be retrieved via `saved_model_cli`, e.g.

```
saved_model_cli show --dir pretrainedresnet/1 --all
```

# End-to-end Example

For an end-to-end example, refer to https://sthalles.github.io/serving_tensorflow_models

# References

- https://stackoverflow.com/questions/33759623/tensorflow-how-to-save-restore-a-model
- https://blog.metaflow.fr/tensorflow-saving-restoring-and-mixing-multiple-models-c4c94d5d7125
