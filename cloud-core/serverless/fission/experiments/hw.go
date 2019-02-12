// Due to golang plugin mechanism,
// the package of function handler must be main package
package main

import (
	"net/http"
)

// Handler is the entry point for this fission function
func Handler(w http.ResponseWriter, r *http.Request) {
	msg := "Hello, world!\n"
	w.Write([]byte(msg))
}
