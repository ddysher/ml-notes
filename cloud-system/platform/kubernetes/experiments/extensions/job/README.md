### Kubernetes 1.2 job

`kubectl create -f job.yaml --kubeconfig=$HOME/.kube/config-gce`
`kubectl get pods -a --show-labels --kubeconfig=$HOME/.kube/config-gce`

`kubectl create -f job-parallel.yaml --kubeconfig=$HOME/.kube/config-gce`
`kubectl get pods -a --show-labels --kubeconfig=$HOME/.kube/config-gce`

Remainings are examples from kubernetes example folder.

In work-queue-1, Pod consumes a work item then exits;
In work-queue-2 (haven't tried), Pod consumes multiple work items then exits.
