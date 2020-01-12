<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)
- [Experiment dex with kubernetes](#experiment-dex-with-kubernetes)
  - [Generate certificates for dex](#generate-certificates-for-dex)
  - [Start dex server](#start-dex-server)
  - [Review what we have](#review-what-we-have)
  - [Start dex client and get id_token](#start-dex-client-and-get-id_token)
  - [Start kubernetes with oidc authentication](#start-kubernetes-with-oidc-authentication)
  - [Review what we have](#review-what-we-have-1)
- [Experiment dex with github](#experiment-dex-with-github)
- [Experiment dex with ldap](#experiment-dex-with-ldap)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Dex is an OpenID Connect server that connects to other identity providers, that is:

```
                                      -- github
                                     /
user -> client (oauth client) -> dex --- ldap
                                     \
                                      -- others
```

# Workflow

- user opens a dex client, e.g. a game server at https://game.com/login
- client shows login options and user chooses one (e.g. google, facebook), client then redirects
  user to dex's auth endpoint e.g. https://dex.com/auth. This is the 'handleAuthorization' handler
  in dex.
- dex looks at configured connector.
  - If there is only one connector, then it redirects user to https://dex.com/auth/c.ID?req=authReq.ID,
    where 'c.ID' is connector's ID
  - If there are multiple connectors, it shows a form for user to choose which login method (connector)
    to use. This is 'handleConnectorLogin' handler in dex.
- dex receives request of a connector from above redirection, and based on type of connector, it
  either uses oauth flow or password.
  - For oauth flow, it calls connector's LoginURL method, e.g. for github, it calls https://github.com/login/oauth/authorize.
    The callback registered in Github should be https://dex.com/callback, which is "handleConnectorCallback"
    handler in dex.
  - For password, it calls connector's Login method with user provided username and password, e.g.
    for ldap, dex calls ldap.Login, which queries ldap to verify username and password. Unlike oauth
    flow, this still happens in the "handleConnectorCallback" handler in dex.
- For both oauth flow and password connectors, they will all redirect user to approval page; that is,
  user successfully logged in, and decides whether to approve dex to access data or not. This is
  "handleApproval" handler in dex. If approved, this handler will call client's redirectURL and send
  code (or id_token, etc) to client.

# Experiment dex with kubernetes

*Date: dex v2.3.0 -> v2.6.1*

## Generate certificates for dex

Using dex utilities to generate certificates for dex:

```
$ cd $GOPATH/src/github.com/coreos/dex/examples/k8s
$ ./gencert.sh
$ mkdir /tmp/dex
$ mv $GOPATH/src/github.com/coreos/dex/examples/k8s/ssl/* /tmp/dex
```

This will generate server and ca certificates and keys.

## Start dex server

Run `make` in dex's root directory to compile dex, and start dex server using `experiments/config-https-dev.yaml`.
The file is derived from dex `config-dev.yaml` example, but issuer is changed to `dex.example.com`
because the certificate we generated in step one has alternative name `dex.example.com`. Before
starting dex, edit "/etc/hosts" to add `dex.example.com` dns record (point it to 127.0.0.1).  Now
start dex:

```
# dex-config.yaml is "experiments/config-https-dev".
$ ./bin/dex serve /tmp/dex-config.yaml
time="2017-08-25T03:28:50Z" level=info msg="config issuer: https://dex.example.com:5556"
time="2017-08-25T03:28:50Z" level=info msg="config storage: sqlite3"
time="2017-08-25T03:28:50Z" level=info msg="config static client: example-app"
time="2017-08-25T03:28:50Z" level=info msg="config connector: mock"
time="2017-08-25T03:28:50Z" level=info msg="config connector: local passwords enabled"
time="2017-08-25T03:28:50Z" level=info msg="keys expired, rotating"
time="2017-08-25T03:28:50Z" level=info msg="keys rotated, next rotation: 2017-08-25 09:28:50.362226444 +0000 UTC"
time="2017-08-25T03:28:50Z" level=info msg="listening (https) on 127.0.0.1:5556"
```

## Review what we have

At this moment, dex is listening at `127.0.0.1:5556 (https)`. Following is a few important setup:
- Issuer. Issuer provides identity. dex is the issuer, it can be seen as an identity provider,
  or as a component that connects to underline identity providers. Here, dex issuer address is
  "https://dex.example.com:5556", which means all clients must use this name to refer to dex.
- Static client. The config file contains a static client (id: example-app). A client, in this
  context, is a client of dex (oauth client).
- Static password. dex needs to connect to underline system, e.g. github, ldap, google, for
  authentication, so that user can login to 'example-app' through logging into these systems. Here
  we just we static password for this purpose.

## Start dex client and get id_token

Now start an example-app using following command:

```
./bin/example-app --issuer https://dex.example.com:5556 --issuer-root-ca /tmp/dex/ca.pem
```

This will run a dex client. Visit http://localhost:5555/ and use 'example-app' as its client id.
After pressing 'Login' button, browser will be redirected to https://dex.example.com:5556 (see
example-app login handler). 'example-app' has client id and client secret; it will pass this to dex.
Upon receiving request, dex will ask user to login. This typically logins to external identity provider,
for example, enter github account. Here, we enter the static password. If login succeeds, we grant
access to our 'example-app' and we'll get an id_token ("Token" field below). Following is an example
output:

```
Token:
eyJhbGciOiJSUzI1NiIsImtpZCI6IjJhNTg3ZGQ5YzljODUzYmQ5Nzc0ODNhMjhlMjVlNmFiNDIxM2QwNDcifQ.eyJpc3MiOiJodHRwczovL2RleC5leGFtcGxlLmNvbTo1NTU2Iiwic3ViIjoiQ2lRd09HRTROamcwWWkxa1lqZzRMVFJpTnpNdE9UQmhPUzB6WTJReE5qWXhaalUwTmpZU0JXeHZZMkZzIiwiYXVkIjoiZXhhbXBsZS1hcHAiLCJleHAiOjE1MDM3MTk3MzAsImlhdCI6MTUwMzYzMzMzMCwiYXpwIjoiZXhhbXBsZS1hcHAiLCJhdF9oYXNoIjoiQjlGc281VUVRNjlKdVhFMWNGQWpTZyIsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6ImFkbWluIn0.WhxBTcxkAJlr3iur95TAOFb6wDpEHpAM1JmK0W9yirUmgKH9MCUUVFklzGZhazTVzsy2zxWfPAzl0WK-EbzSI9A0VEbItGj75TAmdvMiY4-5ldAhM0kXgwWtEjrmWN0fLVgvTcC7lKRnk5h7qG_1tB-G0ipVqJEN9fS8ZqY4Ahnx4lqgKOVfvg00kcdsYRBj8ds-LxS94a1HW6cLkuiFNyo2r2EwwY8mmavc0GJ7fV6hgwTYEedF2nuzJlQ7TscwN7CauYyPdzJvjyavZKjOg545c2JsXrRYzig3XaYvTtr8lP_gZhvgTF91nxxS2HbHJqYXSQ0FwHjD5ZRix0orxA

Claims:
{
  "iss": "https://dex.example.com:5556",
  "sub": "CiQwOGE4Njg0Yi1kYjg4LTRiNzMtOTBhOS0zY2QxNjYxZjU0NjYSBWxvY2Fs",
  "aud": "example-app",
  "exp": 1503719730,
  "iat": 1503633330,
  "azp": "example-app",
  "at_hash": "B9Fso5UEQ69JuXE1cFAjSg",
  "email": "admin@example.com",
  "email_verified": true,
  "name": "admin"
}

Refresh Token:
ChlmaDNweHJxdjZqbnh0cWJwb2RpczI2ZHhmEhltcXZiaHBsdTRjc3VhczJ2c3hncHpsdXpx
```

Now 'example-app' can use this id_token to login as 'admin'. This verifies that whoever has the
token, can login to a system as 'admin' or 'admin@example.com', provided the system trusts the
issuer and has issuer's public certificate.

## Start kubernetes with oidc authentication

Now let's make kubernetes act as a client of dex.

Change "./hack/local-up-cluster.sh" to include the following options to apiserver:

```
--oidc-issuer-url="https://dex.example.com:5556" \
--oidc-client-id="example-app" \
--oidc-ca-file="/tmp/dex/ca.pem" \
--oidc-username-claim="email" \
--oidc-groups-claim="groups" \
```

Start local kubernetes and create role/rolebinding (RBAC is enabled):

```yaml
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: admin@example.com
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Make sure there is no authentication information kubeconfig:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority: /var/run/kubernetes/server-ca.crt
    server: https://localhost:6443
  name: local
contexts:
- context:
    cluster: local
  name: local
current-context: local
kind: Config
preferences: {}
```

Then run kubectl with:

```
# /tmp/config is the previous config
kubectl get pod --kubeconfig=/tmp/config --token=${id_token}
```

## Review what we have

User logged in to 'example-app' via AuthN in dex, where dex connects to underline systems (here we
just use static password). Dex verifies user identity and issues an id_token. For kubernetes, it
just uses the id_token issued to 'example-app', which includes claims containing user's identity.

# Experiment dex with github

*Date: dex v2.6.1*

Register GitHub client from GitHub, and update `config-http-github.yaml` about the client ID and
secret. Then, use the same command to start dex server:

```
# dex-config.yaml is "experiments/config-http-github".
$ ./bin/dex serve /tmp/dex-config.yaml
time="2017-08-25T03:28:50Z" level=info msg="config issuer: https://dex.example.com:5556"
time="2017-08-25T03:28:50Z" level=info msg="config storage: sqlite3"
time="2017-08-25T03:28:50Z" level=info msg="config static client: example-app"
time="2017-08-25T03:28:50Z" level=info msg="config connector: mock"
time="2017-08-25T03:28:50Z" level=info msg="config connector: local passwords enabled"
time="2017-08-25T03:28:50Z" level=info msg="keys expired, rotating"
time="2017-08-25T03:28:50Z" level=info msg="keys rotated, next rotation: 2017-08-25 09:28:50.362226444 +0000 UTC"
time="2017-08-25T03:28:50Z" level=info msg="listening (https) on 127.0.0.1:5556"
```

Similarly:

```
./bin/example-app --issuer http://127.0.0.1:5556
```

# Experiment dex with ldap

*Date: dex v2.6.1+*

- https://github.com/coreos/dex/blob/e10fddee2e79f7a0cdeba511fd5936cf19511bc9/Documentation/ldap-connector.md
