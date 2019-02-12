## NATS Publish Subscribe

#### Concept

https://nats.io/documentation/concepts/nats-pub-sub/

NATS core, or NATS platfrom provides "At Most Once Delivery", i.e. a fire-and-forget
messaging system.

#### Install protoc and golang plugin

ref: github.com/golang/protobuf/protoc-gen-go

then, compile protocol

```
protoc --go_out=. *.proto
```

#### Run gnatsd

```
go get github.com/nats-io/go-nats

gnatsd
```

#### Run publisher and subscribers

In one terminal:

```
go run publisher.go order.pb.go
```


Run multiple subscribers in other terminals:

```
go run subscriber.go order.pb.go
```
