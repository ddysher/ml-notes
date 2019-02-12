package main

import (
	"fmt"
	"log"
	"runtime"

	"github.com/gogo/protobuf/proto"
	nats "github.com/nats-io/go-nats"
)

// Here messages are subscribed using wildcard subject “Order.>”.
const subject = "Order.>"

func main() {
	// Create server connection
	natsConnection, err := nats.Connect(nats.DefaultURL)
	if err != nil {
		log.Fatalf("Error on nats server connection: %v", err)
	}
	log.Println("Connected to " + nats.DefaultURL)

	// Subscribe to subject
	natsConnection.Subscribe(subject, func(msg *nats.Msg) {
		eventStore := EventStore{}
		err := proto.Unmarshal(msg.Data, &eventStore)
		if err != nil {
			log.Fatalf("Unable to receive message %v\n", err)
		}
		// Handle the message
		log.Printf("Received message in EventStore service: %+v\n", eventStore)
	})

	// Keep the connection alive
	fmt.Println("Waiting for events")
	runtime.Goexit()
}
