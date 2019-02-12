## Distributed Tensorflow (r1.3)

Following lists different kinds of experiments with `mnist_replica.py`, which is the official example from tensorflow.

### Distributed Basics

#### Between-graph, Asynchronous

```
python mnist_replica.py --num_gpus=0 --job_name=ps --task_index=0

python mnist_replica.py --num_gpus=0 --job_name=worker --task_index=0 --train_steps=2000
python mnist_replica.py --num_gpus=0 --job_name=worker --task_index=1 --train_steps=2000
```

#### Between-graph, Synchronous

Below setup has `replicas_to_aggregate` == `number_workers`. Global step is 1000 steps and total steps of two workers are 2000.
If we only run one worker (chief worker), we'll still be able to proceed, but there is only one step in global step after two
steps in chief worker.

```
python mnist_replica.py --num_gpus=0 --job_name=ps --task_index=0

python mnist_replica.py --num_gpus=0 --job_name=worker --task_index=0 --train_steps=1000 --sync_replicas
python mnist_replica.py --num_gpus=0 --job_name=worker --task_index=1 --train_steps=1000 --sync_replicas
```

#### Multiple PS servers

Run multiple PS servers:

```
python mnist_replica.py --num_gpus=0 --job_name=ps --ps_hosts=localhost:2222,localhost:2225 --task_index=0
python mnist_replica.py --num_gpus=0 --job_name=ps --ps_hosts=localhost:2222,localhost:2225 --task_index=1
```

Then change `sess_config` to log device placement and run worker:

```
python mnist_replica.py --num_gpus=0 --job_name=worker --ps_hosts=localhost:2222,localhost:2225 --task_index=0
```

Logs from worker shows that some variables are assigned to ps1, some are assigned to ps2, e.g.

```
...
hid_w/Adam/Initializer/zeros: (Const): /job:ps/replica:0/task:1/cpu:0
beta2_power/initial_value: (Const): /job:ps/replica:0/task:0/cpu:0
...
```

It also suggests that all workers know where are variables located and thus can update to specific ps.

### Distributed Estimator

In four different terminals, run:

```
export TF_CONFIG='{
    "cluster": {
        "ps": ["localhost:2221"],
        "chief": ["localhost:2222"],
        "worker": ["localhost:2223", "localhost:2224"]
    },
    "task": {"type": "ps", "index": 0}
}'

python estimator.py
```

```
export TF_CONFIG='{
    "cluster": {
        "ps": ["localhost:2221"],
        "chief": ["localhost:2222"],
        "worker": ["localhost:2223", "localhost:2224"]
    },
    "task": {"type": "chief", "index": 0}
}'

python estimator.py
```

```
export TF_CONFIG='{
    "cluster": {
        "ps": ["localhost:2221"],
        "chief": ["localhost:2222"],
        "worker": ["localhost:2223", "localhost:2224"]
    },
    "task": {"type": "worker", "index": 0}
}'

python estimator.py
```

```
export TF_CONFIG='{
    "cluster": {
        "ps": ["localhost:2221"],
        "chief": ["localhost:2222"],
        "worker": ["localhost:2223", "localhost:2224"]
    },
    "task": {"type": "worker", "index": 1}
}'

python estimator.py
```
