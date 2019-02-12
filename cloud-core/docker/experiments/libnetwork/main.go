// Docker libnetwork example, for concepts, see:
//   https://github.com/docker/libnetwork/blob/master/docs/design.md
//
// Sandbox:  e.g. network namespace
// Endpoint: e.g. veth
// Network:  e.g. bridge
package main

import (
	"fmt"
	"log"

	"github.com/docker/docker/pkg/reexec"
	"github.com/docker/libnetwork"
	"github.com/docker/libnetwork/config"
	"github.com/docker/libnetwork/netlabel"
	"github.com/docker/libnetwork/options"
)

func main() {
	if reexec.Init() {
		return
	}

	// Select and configure the network driver.
	networkType := "bridge"

	// Create a new controller instance.
	//
	// NetworkController object provides the entry-point into libnetwork that
	// exposes simple APIs for the users (such as Docker Engine) to allocate
	// and manage Networks.
	driverOptions := options.Generic{}
	genericOption := make(map[string]interface{})
	genericOption[netlabel.GenericData] = driverOptions
	controller, err := libnetwork.New(config.OptionDriverConfig(networkType, genericOption))
	if err != nil {
		log.Fatalf("libnetwork.New: %s", err)
	}

	// Create a network for containers to join.
	//
	// NewNetwork accepts variadic optional arguments that libnetwork and Drivers
	// can use. A Network is a group of Endpoints that are able to communicate
	// with each-other directly. Whenever a Network is created or updated, the
	// corresponding Driver will be notified of the event. Libnetwork treats
	// Network object at an abstract level to provide connectivity between a group
	// of end-points that belong to the same network and isolate from the rest.
	// The Driver performs the actual work of providing the required connectivity
	// and isolation. The connectivity can be within the same host or across
	// multiple-hosts. Hence Network has a global scope within a cluster.
	network, err := controller.NewNetwork(networkType, "network1", "")
	if err != nil {
		log.Fatalf("controller.NewNetwork: %s", err)
	}

	// Create an endpoint.
	//
	// For each new container: allocate IP and interfaces. The returned network
	// settings will be used for container infos (inspect and such), as well as
	// iptables rules for port publishing. This info is contained or accessible
	// from the returned endpoint.
	// Endpoint represents a Service Endpoint. It provides the connectivity for
	// services exposed by a container in a network with other services provided
	// by other containers in the network. Network object provides APIs to create
	// and manage endpoint. An endpoint can be attached to only one network.
	// Endpoint creation calls are made to the corresponding Driver which is
	// responsible for allocating resources for the corresponding Sandbox. Since
	// Endpoint represents a Service and not necessarily a particular container,
	// Endpoint has a global scope within a cluster as well.
	ep, err := network.CreateEndpoint("Endpoint1")
	if err != nil {
		log.Fatalf("network.CreateEndpoint: %s", err)
	}

	// Create the sandbox for the container.
	//
	// NewSandbox accepts variadic optional arguments which libnetwork can use.
	// A Sandbox contains the configuration of a container's network stack. A
	// Sandbox contains the configuration of a container's network stack. This
	// includes management of the container's interfaces, routing table and DNS
	// settings. An implementation of a Sandbox could be a Linux Network Namespace,
	// a FreeBSD Jail or other similar concept. A Sandbox may contain many
	// endpoints from multiple networks.
	sbx, err := controller.NewSandbox("container1",
		libnetwork.OptionHostname("test"),
		libnetwork.OptionDomainname("docker.io"))
	if err != nil {
		log.Fatalf("controller.NewSandbox: %s", err)
	}

	// A sandbox can join the endpoint via the join api.
	err = ep.Join(sbx)
	if err != nil {
		log.Fatalf("ep.Join: %s", err)
	}

	// libnetwork client can check the endpoint's operational data via the Info() API
	epInfo, err := ep.DriverInfo()
	if err != nil {
		log.Fatalf("ep.DriverInfo: %s", err)
	}

	macAddress, ok := epInfo[netlabel.MacAddress]
	if !ok {
		log.Fatalf("failed to get mac address from endpoint info")
	}

	fmt.Printf("Joined endpoint %s (%s) to sandbox %s (%s)\n", ep.Name(), macAddress, sbx.ContainerID(), sbx.Key())
}
