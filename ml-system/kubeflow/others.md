<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Katib](#katib)
  - [Related Projects](#related-projects)
    - [advisor](#advisor)
- [Fairing](#fairing)
  - [Implementation](#implementation)
- [Pipeline](#pipeline)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Katib

In google vizier, client uses SDK to query vizier for suggestions (trial), use the trial to run
training, then report metrics back to server. However, in katib (very early, v0.1.0), everything
is done via study config. Running a trial is done in katib instead of users launching training
themselves - the suggestioned parameters are passed as container entrypoint. See this [blog](http://gaocegege.com/Blog/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0/katib).

## Related Projects

### [advisor](https://github.com/tobegit3hub/advisor)

The project is a very simple system implementing vizier API. At its core, it is a web application
with a few endpoints, i.e. CRUD studies, suggestions, etc. Following is the API in advisor:

```python
client = AdvisorClient()

# Create the study
study_configuration = {
  "goal": "MAXIMIZE",
  "maxTrials": 5,
  "maxParallelTrials": 1,
  "params": [
    {
      "parameterName": "hidden1",
      "type": "INTEGER",
      "minValue": 40,
      "maxValue": 400,
      "scallingType": "LINEAR"
    }
  ]
}
study = client.create_study("Study", study_configuration)

# Get suggested trials
trials = client.get_suggestions(study, 3)

# Training ...


# Complete the trial
client.complete_trial(trial, trial_metrics)
```

When calling 'create_study', the object is saved to backend; when calling 'get_suggestions',
corresponding algorithm is invoked to calculate trial suggestions; when 'complete_trial' is called,
the trial status is updated to completed and saved to backend. Users are responsible to train
their model based on trial suggestions and provide the objective value.

# Fairing

Fairing allows launching training jobs from python code using decorator. It can check if the code
is running in notebook, and if so, it will convert notebook to python code using `nbconvert`.
Under the hook, the python code will be built into a docker image and submit to kubeflow.

## Implementation

User defines a class with a decorator, then creates an object from the class and call its train method.

```python
@Train(package={'name': 'fairing-mnist', 'repository': '<your-repository-name>', 'publish': True})
class MyModel(object):
    def train(self):
      pass

if __name__ == '__main__':
    model = MyModel()
    model.train()
```

The `Train` decorator is a class decorator with the following content:

```python
# @Train decorator
class Train(object):
    def __init__(self, package, tensorboard=None, architecture=BasicArchitecture(), strategy=BasicTrainingStrategy()):
        self.trainer = Trainer(package, tensorboard, architecture, strategy)

    def __call__(self, cls):
        class UserClass(cls):
            # self refers to the Train instance
            # user_class is equivalentto self in the UserClass instance
            def __init__(user_class):
                user_class.is_training_initialized = False

            def __getattribute__(user_class, attribute_name):
                # Overriding train in order to minimize the changes necessary in the user
                # code to go from local to remote execution.
                # That way, by simply commenting or uncommenting the Train decorator
                # Model.train() will execute either on the local setup or in kubernetes

                if attribute_name != 'train' or user_class.is_training_initialized:
                    return super(UserClass, user_class).__getattribute__(attribute_name)

                if attribute_name == 'train' and not is_runtime_phase():
                    return super(UserClass, user_class).__getattribute__('_deploy_training')

                print(type(self))
                print(type(user_class))
                user_class.is_training_initialized = True
                self.trainer.start_training(user_class)
                return super(UserClass, user_class).__getattribute__('_noop_attribute')

            def _noop_attribute(user_class):
                pass

            def _deploy_training(user_class):
                self.trainer.deploy_training()


        return UserClass
```

The inner `UserClass` is the wrapper class on top of MyModel - all function calls go through the
`__call__` method. There are two methods worth mentioning, one is the `train()` method that calls
user code (MyModel.train) to start training, and `deploy_train()` method which creates a dockerfile,
build it (directly issue docker build command) and deploy training tfjob to kubernetes.

# Pipeline

Kubeflow pipeline describes a machine learning workflow including all of the components in the
workflow and how they combine in the form of a graph.

It consists of:
- Kubernetes operators to run workflow (wrap around argo)
- Python SDK
- Backend and Frontend
- Database

*References*

- https://github.com/amygdala/code-snippets/blob/master/ml/kubeflow-pipelines/README_github_summ.md
