## Kubernetes ingress (v1.2)

Mostly following kubernetes/contrib/ingress repository (As of 03/31/2016). Assume a stock k8s cluster.

- Create a default backend service

`kubectl create -f default-backend-rc.yaml`
`kubectl expose rc default-http-backend --port=80 --target-port=8080 --name=default-http-backend`

Note the default backend service is hard-coded in 'nginx-ingress-rc.yaml with value 'default/default-http-backend',
so we must use namespace 'default' and name 'default-http-backend'. The default server comes from contrib/404-server.

- Create ingress controller

`kubectl create -f nginx-ingress-rc.yaml`

This will create a default ingress controller without customization (here, customization means customize nginx
configurations).
