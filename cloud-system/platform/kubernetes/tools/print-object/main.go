package main

import (
	"encoding/json"
	"fmt"

	api "k8s.io/kubernetes/pkg/api"
)

func main() {
	user := &api.Pod{}
	b, err := json.Marshal(user)
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println(string(b))
}
