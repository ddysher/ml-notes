## NATS Queueing

#### Concept

https://nats.io/documentation/concepts/nats-queueing/

NATS supports message queueing using point-to-point (one-to-one) communication.

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

Since all subscribers are in a single queue, they will receive messages randomly.
