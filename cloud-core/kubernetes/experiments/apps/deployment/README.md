## Kubernetes Deployment

#### Strategic merge patch

Run a deployment:

```
$ kubectl apply -f deployment-patch.yaml
...
```

To patch:

```
$ kubectl patch deployment patch-demo -p "$(cat patch-file.yaml)"
...
```

Now Pods are merged with two containers:

```
$ kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
patch-demo-6d6b8fd787-d6jdz   1/1     Running   0          106s
patch-demo-6d6b8fd787-qz9hz   1/1     Running   0          106s

$ kubectl get pods
NAME                         READY   STATUS    RESTARTS   AGE
patch-demo-c8796b6dd-9t8hb   2/2     Running   0          55s
patch-demo-c8796b6dd-ckqrc   2/2     Running   0          36s
```

This is because `containers` field of pod spec is `strategic merge patch` with `name` as the key.
The default behavior is to replace, e.g. the `toleration` field.

There are three types of merge type:
- JSON Patch
- JSON Merge Patch
- Strategic Merge Patch (default)

*Reference*

- https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/
