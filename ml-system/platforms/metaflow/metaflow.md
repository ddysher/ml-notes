<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments (01/22/2020, v2.0)](#experiments-01222020-v20)
  - [Demonstrated Features](#demonstrated-features)
  - [Run Metaflow](#run-metaflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Metaflow is a framework open sourced from Netflix for real-world data science projects.

The core of metaflow is an SDK to create and run workflow, either on local host or on the cloud,
thus combining the benefit of fast prototype on local host and massive compute resources on the
cloud. Metaflow is designed with usability in mind so that switching between the two environments
do not require code change from data scientist.

In addition, metaflow promotes reusability and reproducibility: data scientist should be able to
share and reproduce machine learning projects from each other. To achieve this, metaflow keeps track
of code and data from users, as well as other metaflow metadata.

For information on metaflow architecture, refer to:
- [basic concepts](https://docs.metaflow.org/metaflow/basics)
- [technical-overview](https://docs.metaflow.org/internals-of-metaflow/technical-overview)

# Experiments (01/22/2020, v2.0)

## Demonstrated Features

The tutorials demonstrate:
- `@step` decorator to define a Step in Flow
- metaflow parameter, which is defined as a Flow class variable and can be overriden by command line flag
- run steps in parallel and join result
- use external file via `IncludeFile`
- use external packages via `@conda` decorator, e.g. `@conda(libraries={'pandas' : '0.24.2'})`
- fan-out: e.g. `self.next(self.compute_statistics, foreach='genres')`
- use data artifacts generated from other flows, e.g. `run = Flow('MovieStatsFlow').latest_successful_run`
- run on AWS with `@batch` decorator, which eventually calls AWS python client `boto3`'s method
  `submit_job()` targeted for AWS Batch service to run computation; artifacts are saved in AWS S3
- seamlessly run on cloud without code change, by just adding command line option `--with batch`

Additional features include:
- namespace to organize results
- metadata provider to save information about runs, flows, etc; the default implementation is local
  directory `.metaflow`, and recommended ones are RDS
- when you assign anything to `self` in your Metaflow flow, the object gets automatically persisted
  in S3 as a Metaflow artifact; when branches are used and a data artifact is modified in both
  branches, user can access each artifact using branch name, or explicitly handle the ambiguity.
- default [native](https://github.com/Netflix/metaflow/blob/2.0.1/metaflow/runtime.py#L794) runtime (or scheduler)

## Run Metaflow

To experiment with metaflow, run:

```
$ pip install metaflow

$ metaflow tutorials pull
```

Every step runs in a separate local process, e.g.

```
$ python 00-helloworld/helloworld.py run
Metaflow 2.0.1 executing HelloFlow for user:deyuan
Validating your flow...
    The graph looks good!
Running pylint...
    Pylint not found, so extra checks are disabled.
2020-01-22 15:20:37.828 Workflow starting (run-id 1579677637825878):
2020-01-22 15:20:37.830 [1579677637825878/start/1 (pid 716142)] Task is starting.
2020-01-22 15:20:48.109 [1579677637825878/start/1 (pid 716142)] HelloFlow is starting.
2020-01-22 15:20:48.138 [1579677637825878/start/1 (pid 716142)] Task finished successfully.
2020-01-22 15:20:48.141 [1579677637825878/hello/2 (pid 716517)] Task is starting.
2020-01-22 15:20:58.431 [1579677637825878/hello/2 (pid 716517)] Metaflow says: Hi!
2020-01-22 15:20:58.462 [1579677637825878/hello/2 (pid 716517)] Task finished successfully.
2020-01-22 15:20:58.464 [1579677637825878/end/3 (pid 716878)] Task is starting.
2020-01-22 15:21:08.753 [1579677637825878/end/3 (pid 716878)] HelloFlow is all done.
2020-01-22 15:21:08.783 [1579677637825878/end/3 (pid 716878)] Task finished successfully.
2020-01-22 15:21:08.784 Done!
```

```
$ ps aux | grep python | grep helloworld
deyuan    715933  9.6  0.2  57196 38728 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py run
deyuan    716142  8.6  0.2  56008 37584 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py --quiet --metadata local --environment local --datastore local --event-logger nullSidecarLogger --monitor nullSidecarMonitor --datastore-root /home/deyuan/code/arsenal/ml-system/platforms/metaflow/metaflow-tutorials/.metaflow step start --run-id 1579677637825878 --task-id 1 --input-paths 1579677637825878/_parameters/0

$ ps aux | grep python | grep helloworld
deyuan    715933  2.5  0.2  57196 38768 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py run
deyuan    716517 12.5  0.2  56008 37404 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py --quiet --metadata local --environment local --datastore local --event-logger nullSidecarLogger --monitor nullSidecarMonitor --datastore-root /home/deyuan/code/arsenal/ml-system/platforms/metaflow/metaflow-tutorials/.metaflow step hello --run-id 1579677637825878 --task-id 2 --input-paths 1579677637825878/start/1

$ ps aux | grep python | grep helloworld
deyuan    715933  1.3  0.2  57196 38768 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py run
deyuan    716878 26.0  0.2  56008 37748 pts/5    S+   15:20   0:00 /home/deyuan/.pyenv/versions/3.6.7/bin/python 00-helloworld/helloworld.py --quiet --metadata local --environment local --datastore local --event-logger nullSidecarLogger --monitor nullSidecarMonitor --datastore-root /home/deyuan/code/arsenal/ml-system/platforms/metaflow/metaflow-tutorials/.metaflow step end --run-id 1579677637825878 --task-id 3 --input-paths 1579677637825878/hello/2

$ pstree -sp 716878
systemd(1)───gdm(564)─── ... ───zsh(709806)───python(715933)───python(716878)
```

All runs are versioned, metadata and artifacts are saved under `.metaflow`. For example, the metadata
of `dataframe` artifact (defined in PlayListFlow' start step) locates at `./metaflow/PlayListFlow/1579678087577554/start/1/_meta`,
in which the file `0_artifact_dataframe.json` points to data at `.metaflow/PlayListFlow/data/6b/6b9d7eaffdaccb4cb6dfd2b3a1a92a1fcf9ed6ef`.

<details><summary>The Example PlayListFlow Tree</summary><p>

```
$ tree .metaflow/PlayListFlow
.metaflow/PlayListFlow
├── 1579678087577554
│   ├── bonus_movie
│   │   ├── 2
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact_bonus.json
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact_dataframe.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678088204.json
│   │   │       ├── sysmeta_attempt-done_1579678088213.json
│   │   │       ├── sysmeta_log_location_stderr_1579678088250.json
│   │   │       ├── sysmeta_log_location_stdout_1579678088250.json
│   │   │       └── sysmeta_origin-run-id_1579678088204.json
│   │   └── _meta
│   │       └── _self.json
│   ├── end
│   │   ├── 5
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact_bonus.json
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_playlist.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678088837.json
│   │   │       ├── sysmeta_attempt-done_1579678088842.json
│   │   │       ├── sysmeta_log_location_stderr_1579678088870.json
│   │   │       ├── sysmeta_log_location_stdout_1579678088870.json
│   │   │       └── sysmeta_origin-run-id_1579678088837.json
│   │   └── _meta
│   │       └── _self.json
│   ├── genre_movies
│   │   ├── 3
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact_dataframe.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_movies.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678088206.json
│   │   │       ├── sysmeta_attempt-done_1579678088216.json
│   │   │       ├── sysmeta_log_location_stderr_1579678088253.json
│   │   │       ├── sysmeta_log_location_stdout_1579678088252.json
│   │   │       └── sysmeta_origin-run-id_1579678088206.json
│   │   └── _meta
│   │       └── _self.json
│   ├── join
│   │   ├── 4
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact_bonus.json
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_playlist.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678088529.json
│   │   │       ├── sysmeta_attempt-done_1579678088535.json
│   │   │       ├── sysmeta_log_location_stderr_1579678088563.json
│   │   │       ├── sysmeta_log_location_stdout_1579678088563.json
│   │   │       └── sysmeta_origin-run-id_1579678088529.json
│   │   └── _meta
│   │       └── _self.json
│   ├── _meta
│   │   └── _self.json
│   ├── _parameters
│   │   ├── 0
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   └── _meta
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       └── sysmeta_attempt-done_1579678087586.json
│   │   └── _meta
│   │       └── _self.json
│   └── start
│       ├── 1
│       │   ├── 0.attempt.json
│       │   ├── 0.data.json
│       │   ├── 0.DONE.lock
│       │   ├── 0.runtime.json
│       │   ├── 0.stderr.log
│       │   ├── 0.stdout.log
│       │   ├── 0.task_begin.json
│       │   ├── 0.task_end.json
│       │   └── _meta
│       │       ├── 0_artifact__current_step.json
│       │       ├── 0_artifact_dataframe.json
│       │       ├── 0_artifact__exception.json
│       │       ├── 0_artifact__foreach_num_splits.json
│       │       ├── 0_artifact__foreach_stack.json
│       │       ├── 0_artifact__foreach_var.json
│       │       ├── 0_artifact_genre.json
│       │       ├── 0_artifact_movie_data.json
│       │       ├── 0_artifact_name.json
│       │       ├── 0_artifact_recommendations.json
│       │       ├── 0_artifact__success.json
│       │       ├── 0_artifact__task_ok.json
│       │       ├── 0_artifact__transition.json
│       │       ├── _self.json
│       │       ├── sysmeta_attempt_1579678087868.json
│       │       ├── sysmeta_attempt-done_1579678087882.json
│       │       ├── sysmeta_log_location_stderr_1579678087911.json
│       │       ├── sysmeta_log_location_stdout_1579678087911.json
│       │       └── sysmeta_origin-run-id_1579678087868.json
│       └── _meta
│           └── _self.json
├── 1579678271463665
│   ├── bonus_movie
│   │   ├── 2
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact_bonus.json
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact_dataframe.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678272054.json
│   │   │       ├── sysmeta_attempt-done_1579678272063.json
│   │   │       ├── sysmeta_log_location_stderr_1579678272100.json
│   │   │       ├── sysmeta_log_location_stdout_1579678272100.json
│   │   │       └── sysmeta_origin-run-id_1579678272054.json
│   │   └── _meta
│   │       └── _self.json
│   ├── genre_movies
│   │   ├── 3
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   ├── 0.runtime.json
│   │   │   ├── 0.stderr.log
│   │   │   ├── 0.stdout.log
│   │   │   ├── 0.task_begin.json
│   │   │   ├── 0.task_end.json
│   │   │   └── _meta
│   │   │       ├── 0_artifact__current_step.json
│   │   │       ├── 0_artifact_dataframe.json
│   │   │       ├── 0_artifact__exception.json
│   │   │       ├── 0_artifact__foreach_num_splits.json
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact__foreach_var.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       ├── sysmeta_attempt_1579678272063.json
│   │   │       ├── sysmeta_attempt-done_1579678272072.json
│   │   │       ├── sysmeta_log_location_stderr_1579678272101.json
│   │   │       ├── sysmeta_log_location_stdout_1579678272101.json
│   │   │       └── sysmeta_origin-run-id_1579678272063.json
│   │   └── _meta
│   │       └── _self.json
│   ├── _meta
│   │   └── _self.json
│   ├── _parameters
│   │   ├── 0
│   │   │   ├── 0.attempt.json
│   │   │   ├── 0.data.json
│   │   │   ├── 0.DONE.lock
│   │   │   └── _meta
│   │   │       ├── 0_artifact__foreach_stack.json
│   │   │       ├── 0_artifact_genre.json
│   │   │       ├── 0_artifact_movie_data.json
│   │   │       ├── 0_artifact_name.json
│   │   │       ├── 0_artifact_recommendations.json
│   │   │       ├── 0_artifact__success.json
│   │   │       ├── 0_artifact__task_ok.json
│   │   │       ├── 0_artifact__transition.json
│   │   │       ├── _self.json
│   │   │       └── sysmeta_attempt-done_1579678271467.json
│   │   └── _meta
│   │       └── _self.json
│   └── start
│       ├── 1
│       │   ├── 0.attempt.json
│       │   ├── 0.data.json
│       │   ├── 0.DONE.lock
│       │   ├── 0.runtime.json
│       │   ├── 0.stderr.log
│       │   ├── 0.stdout.log
│       │   ├── 0.task_begin.json
│       │   ├── 0.task_end.json
│       │   └── _meta
│       │       ├── 0_artifact__current_step.json
│       │       ├── 0_artifact_dataframe.json
│       │       ├── 0_artifact__exception.json
│       │       ├── 0_artifact__foreach_num_splits.json
│       │       ├── 0_artifact__foreach_stack.json
│       │       ├── 0_artifact__foreach_var.json
│       │       ├── 0_artifact_genre.json
│       │       ├── 0_artifact_movie_data.json
│       │       ├── 0_artifact_name.json
│       │       ├── 0_artifact_recommendations.json
│       │       ├── 0_artifact__success.json
│       │       ├── 0_artifact__task_ok.json
│       │       ├── 0_artifact__transition.json
│       │       ├── _self.json
│       │       ├── sysmeta_attempt_1579678271738.json
│       │       ├── sysmeta_attempt-done_1579678271747.json
│       │       ├── sysmeta_log_location_stderr_1579678271776.json
│       │       ├── sysmeta_log_location_stdout_1579678271775.json
│       │       └── sysmeta_origin-run-id_1579678271738.json
│       └── _meta
│           └── _self.json
├── data
│   ├── 01
│   │   └── 01b168d0b2c70f906b295772af9efb98b0797cae
│   ├── 1d
│   │   └── 1deee24776cb748ed5121c932b8d39f5eb3e20f6
│   ├── 21
│   │   └── 21b5fa4b5e2ac1aac9efafe85a61b7428ac128af
│   ├── 35
│   │   └── 35e72e41a10e8e553395dab5c23e5a11352b782c
│   ├── 40
│   │   └── 407cf9400665f35591e64a9fd3650b46184c5be7
│   ├── 4c
│   │   └── 4ca058df2ea422cca260c585409d6ac9face7ebe
│   ├── 4f
│   │   └── 4f6a7da1fb3657a056a703cc1b464ee23bc72a55
│   ├── 61
│   │   └── 61361d0014813835165fe9cfd0f582885109a5a5
│   ├── 69
│   │   └── 69e77141c3eb7a8c9ce864251d70c02723f29332
│   ├── 6b
│   │   ├── 6b750ab4ebaf839efb28a4c1aa38ea2d4baccc3e
│   │   └── 6b9d7eaffdaccb4cb6dfd2b3a1a92a1fcf9ed6ef
│   ├── 81
│   │   └── 81c437e75596b0212ffa5bf4d5ca6f63abd05083
│   ├── 85
│   │   └── 8595ace28ecae5dce8427b7594f7a2fd70f1b009
│   ├── 95
│   │   └── 95a4ffc305971261da24197e27933ebcee5b661b
│   ├── 9d
│   │   └── 9d95ea4992c88b64bc214706f1e70cded6c37874
│   ├── aa
│   │   └── aaa80d531429fdb95fac39e03b4989e4564e3e48
│   ├── ab
│   │   └── abffd6d0d822486e7bb43971dff7b656c0c76a4a
│   ├── ca
│   │   └── caa40ab420354941d2127f64360105b8548b8802
│   ├── f3
│   │   └── f3627f46179fdd95bf0e83101840fd1d71b60e40
│   └── f4
│       └── f469d550cc329adf51321a82544ff9841cef7ef7
├── latest_run
└── _meta
    └── _self.json

65 directories, 281 files
```

</p></details></br>
