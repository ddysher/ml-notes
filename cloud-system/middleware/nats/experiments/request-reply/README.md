## NATS request reply

#### Concept

https://nats.io/documentation/concepts/nats-req-rep/

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

#### Run server and client

In one terminal:

```
go run server.go message.pb.go
```

In another terminal:

```
go run client.go message.pb.go
```
