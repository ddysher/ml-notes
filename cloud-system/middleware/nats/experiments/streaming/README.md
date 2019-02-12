## NATS Streaming

Fetch source:

```sh
go get github.com/nats-io/nats-streaming-server
go get github.com/nats-io/go-nats-streaming
```

Start server:

```sh
$ nats-streaming-server
```

Send a few messages:

```sh
cd $GOPATH/src/github.com/nats-io/go-nats-streaming/examples/stan-pub

go run main.go foo "msg 1"
go run main.go foo "msg 2"
go run main.go foo "msg 3"
```

Receive all messages later from a subscriber:

```
cd $GOPATH/src/github.com/nats-io/go-nats-streaming/examples/stan-sub

go run main.go --all -c test-cluster -id myID foo
```
