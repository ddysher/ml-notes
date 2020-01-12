# Security Context

https://kubernetes.io/docs/tasks/configure-pod-container/security-context/

## runAsUser & USER

If docker image contains `USER` and Kubernetes contains `runAsUser`, the `runAsUser` option will
take precedence.

```
docker build . -t busybox:user
```

Then change image to `busybox:user`, the result would be the same as not using USER.
