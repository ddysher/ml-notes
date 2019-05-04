## kubernetes labels

After creating the pods, we can use label to select subset of them:

```console
$ kubectl get pods -l environment=test --show-labels

$ kubectl get pods -l environment=prod,tier=frontend --show-labels

$ kubectl get pods -l environment!=prod --show-labels

$ kubectl get pods -l environment!=prod --show-labels

$ kubectl get pods -l 'environment in (prod,test)' --show-labels
```
