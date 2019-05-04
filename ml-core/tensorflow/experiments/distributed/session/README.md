# Session

Unlike local session, where each seesion has its own variablesIn contrast, when you are using
distributed sessions, variable state is managed by `resource containers` located on the cluster
itself, not by the sessions.

Run two PSes, with no worker:

```
python ps_0.py
python ps_1.py
```

Run a simple client, talking to each of them. Note the second call returns `2.0`.

```
python simple_client.py grpc://localhost:2221 init
1.0

python simple_client.py grpc://localhost:2222
2.0
```
