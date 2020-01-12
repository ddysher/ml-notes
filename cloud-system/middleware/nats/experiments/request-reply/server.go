package main

import (
	"fmt"
	"log"
	"runtime"

	"github.com/gogo/protobuf/proto"
	nats "github.com/nats-io/go-nats"
)

func main() {
	// Create server connection
	natsConnection, err := nats.Connect(nats.DefaultURL)
	if err != nil {
		log.Fatalf("Error on nats server connection: %v", err)
	}
	log.Println("Connected to " + nats.DefaultURL)

	natsConnection.Subscribe("Discovery.OrderService", func(m *nats.Msg) {
		orderServiceDiscovery := ServiceDiscovery{OrderServiceUri: "order.example.com"}
		data, err := proto.Marshal(&orderServiceDiscovery)
		if err == nil {
			natsConnection.Publish(m.Reply, data)
		}
	})

	// Keep the connection alive.
	fmt.Println("Waiting for request")
	runtime.Goexit()
}
