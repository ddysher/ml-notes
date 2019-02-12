package main

import (
	"fmt"

	api "k8s.io/kubernetes/pkg/api"
	client "k8s.io/kubernetes/pkg/client/unversioned"
)

func main() {
	client, _ := client.NewInCluster()

	var ops api.ListOptions
	if services, err := client.Services("kube-system").List(ops); err != nil {
		fmt.Printf("Error listing services: %v", err)
	} else {
		fmt.Printf("Listed all services: %v", services)
	}
}
