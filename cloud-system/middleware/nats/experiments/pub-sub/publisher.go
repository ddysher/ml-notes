package main

import (
	"log"
	"strconv"
	"time"

	"github.com/gogo/protobuf/proto"
	nats "github.com/nats-io/go-nats"
)

const (
	aggregate = "Order"
	event     = "OrderCreated"
)

var index int

func main() {
	// Connect to NATS server
	natsConnection, err := nats.Connect(nats.DefaultURL)
	if err != nil {
		log.Fatalf("Error on nats server connection: %v", err)
	}
	log.Println("Connected to " + nats.DefaultURL)
	defer natsConnection.Close()

	for {
		// Publish a mock order
		event := EventStore{
			AggregateId:   strconv.Itoa(index),
			AggregateType: aggregate,
			EventId:       strconv.Itoa(index),
			EventType:     event,
			EventData:     "{an order}",
		}
		subject := "Order.OrderCreated"
		data, err := proto.Marshal(&event)
		if err != nil {
			log.Fatalf("Unable to marshal %v", err)
		}

		// Publish message on subject. There is no guarantees of having the bytes
		// sent; they may still just be in the flushing queue.
		err = natsConnection.Publish(subject, data)
		if err != nil {
			log.Fatalf("Unable to publish message %v\n", err)
		}
		log.Printf("Published message with id %v on subject %v\n", index, subject)
		index = index + 1

		time.Sleep(time.Second)
	}
}
