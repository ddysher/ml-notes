package main

import (
	"log"
	"time"

	"github.com/gogo/protobuf/proto"
	nats "github.com/nats-io/go-nats"
)

func main() {
	// Create NATS server connection
	natsConnection, err := nats.Connect(nats.DefaultURL)
	if err != nil {
		log.Fatalf("Error on nats server connection: %v", err)
	}
	log.Println("Connected to " + nats.DefaultURL)

	// The NATS client is then used to send a request on a subject named
	// “Discovery.OrderService” to get a response.
	msg, err := natsConnection.Request("Discovery.OrderService", nil, 1000*time.Millisecond)
	if err != nil {
		log.Fatalf("Error on sending request: %v", err)
	}
	if msg == nil {
		log.Fatalf("No message response received")
	}

	orderServiceDiscovery := ServiceDiscovery{}
	err = proto.Unmarshal(msg.Data, &orderServiceDiscovery)
	if err != nil {
		log.Fatalf("Error on unmarshal: %v", err)
	}
	address := orderServiceDiscovery.OrderServiceUri
	log.Println("OrderService endpoint found at:", address)
}
