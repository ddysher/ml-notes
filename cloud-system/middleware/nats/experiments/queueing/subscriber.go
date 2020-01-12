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
const queue = "Order.OrdersCreatedQueue"

func main() {
	// Create server connection
	natsConnection, err := nats.Connect(nats.DefaultURL)
	if err != nil {
		log.Fatalf("Error on nats server connection: %v", err)
	}
	log.Println("Connected to " + nats.DefaultURL)

	// Subscribe to subject. The only difference here is that we used a queue:
	// only one subscriber in the same queue will receive message.
	natsConnection.QueueSubscribe(subject, queue, func(msg *nats.Msg) {
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
