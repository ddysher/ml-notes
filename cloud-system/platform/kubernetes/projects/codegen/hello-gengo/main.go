package main

import "fmt"

// +genset=true
type User struct {
	Name string
	Age  int
}

func main() {
	user := User{
		Name: "example",
		Age:  30,
	}
	fmt.Printf("%v\n", user)
}
