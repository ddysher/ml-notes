## NNI

[NNI (Neural Network Intelligence)](https://github.com/Microsoft/nni) is a toolkit to help users
design and tune machine learning models (e.g., hyperparameters), neural network architectures, or
complex system's parameters, in an efficient and automatic way.

Users submit `Experiment` to nni: each `Experiment` contains source code and configuration, which
include tunning algorithm, search space, etc. Tunner receives search space and generates specific
configurations for each trial. The trials are then submitted to training platform like local machine,
kubernetes, etc.

For souce code, users can either:
- use `nni` SDK to assign hyperparameters, report metrics, etc
- use annotations to implicitly assign hyperparameters, nni will convert the annotations to new code for each trial

*References*

- https://github.com/Microsoft/nni/blob/master/docs/en_US/Overview.md
