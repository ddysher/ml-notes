# Guild

[Guild](https://github.com/guildai/guildai) is a command line toolkit to run, track, and compare
machine learning experiments. It's similar to mlflow, pipelineai with regard to running task, but
apart from typical commands like `run`, `compare`, etc, it is also capable of performing
hyperparameter tuning, e.g.

```shell
guild run train.py x=uniform[-2.0:2.0] --optimizer bayesian --max-trials 20
```

Guild requires no code change from user - it uses python ast to replace parameter variables.

*References*

- https://github.com/gar1t/2019-sysml
- https://www.sysml.cc/doc/2019/demo_26.pdf
