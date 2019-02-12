# Census Example

This example uses a simple Tensorflow model to predict income based on census data.
The code is based on [this example](https://github.com/GoogleCloudPlatform/cloudml-samples/tree/master/census) by Google Cloud ML.

The example supports:
 - training on CPU (**no GPU**)
 - distributed training with Tensorflow

To perform a training run, execute (in this directory):
```
riseml train
```
Note: The default command downloads the training data from inside the container on each run.

To perform distributed training:
```
riseml train -f riseml_dist.yml
```


To perform hyperparameter optimization as well as distributed training:
```
riseml train -f riseml_dist_hyper.yml
```

Feel free to adjust the `riseml*.yml` to your needs, e.g., change resource requirements.


## Training Data

The training data uses the [Census Income Dataset](https://archive.ics.uci.edu/ml/datasets/Census+Income) from the UCI Machine Learning Repository.
The data is part of this code repository, only since it is so small.
