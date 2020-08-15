<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)
  - [Exporting](#exporting)
  - [Predictor](#predictor)
  - [API Deployment/Configuration](#api-deploymentconfiguration)
  - [Monitoring](#monitoring)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Cortex](https://github.com/cortexlabs/cortex) is a machine learning model serving infrastructure
based on containers (and Kubernetes for large scale deployment). At the user-facing level, cortex
provides a set of opinioned APIs and workflows for working with model deployment.

Many of Cortex features are built on AWS.

# Workflow

## [Exporting](https://docs.cortex.dev/deployments/exporting)

Models are exported using standard framework tools.

## [Predictor](https://docs.cortex.dev/deployments/predictors)

Cortex user (model deployer) needs to provide a `Predictor`, which is an interface defined by Cortex.
For example:

```python
# predictor.py

class PythonPredictor:
    def __init__(self, config):
        self.model = download_model()

    def predict(self, payload):
        return self.model.predict(payload["text"])
```

Different frameworks have different Predictor interface.

## [API Deployment/Configuration](https://docs.cortex.dev/deployments/api-configuration)

Once a predictor is ready, cortex user needs to provide a `cortex.yaml`, which defines a set of
API configurations for deploying models. For example:

```yaml
# cortex.yaml

- name: sentiment-classifier
  predictor:
    type: python
    path: predictor.py
  compute:
    gpu: 1
    mem: 4G
```

To deploy the model, run:

```
$ cortex deploy

creating sentiment-classifier
```

Appending to `cortex.yaml` will add more models. Following config contains two models:

```yaml
# cortex.yaml

- name: iris-classifier
  predictor:
    type: python
    path: predictor.py
    config:
      bucket: cortex-examples
      key: sklearn/iris-classifier/model.pkl
  monitoring:
    model_type: classification
  compute:
    cpu: 0.2
    mem: 100M

- name: another-iris-classifier
  predictor:
    type: python
    path: predictor.py
    config:
      bucket: cortex-examples
      key: sklearn/iris-classifier/another-model.pkl
  monitoring:
    model_type: classification
  compute:
    cpu: 0.2
    mem: 100M
```

## [Monitoring](https://docs.cortex.dev/deployments/prediction-monitoring)

Prediction monitoring can be added to `cortex.yaml`. For example, following is a prediction
monitoring for a classification model:

```yaml
# cortex.yaml

- name: iris-classifier
  predictor:
    type: python
    path: predictor.py
    config:
      bucket: cortex-examples
      key: sklearn/iris-classifier/model.pkl
  monitoring:
    model_type: classification
```
