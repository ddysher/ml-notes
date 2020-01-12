## NATS Clustering

#### Run NATS Cluster

https://nats.io/documentation/server/gnatsd-cluster/

```
gnatsd -p 4222 -cluster nats://localhost:4248 -D
gnatsd -p 5222 -cluster nats://localhost:5248 -routes nats://localhost:4248 -D
gnatsd -p 6222 -cluster nats://localhost:6248 -routes nats://localhost:4248 -D
```

#### Clients

Install tools:

```
export GOBIN=$HOME/code/workspace/bin
go install $GOPATH/src/github.com/nats-io/go-nats/examples/nats-pub.go
go install $GOPATH/src/github.com/nats-io/go-nats/examples/nats-sub.go
```

Subscriber can subscribe to any one of the servers; it will receive messages
whichever server receives the message:

```
nats-sub -s "nats://localhost:5222" sub.foo

nats-pub -s "nats://localhost:4222" sub.foo "hello world"
nats-pub -s "nats://localhost:5222" sub.foo "hello world"
nats-pub -s "nats://localhost:6222" sub.foo "hello world"
```

If we kill NATS instance listening at 5222, subscriber still has connections
with NATS cluster and can receive messages of wanted subject.
