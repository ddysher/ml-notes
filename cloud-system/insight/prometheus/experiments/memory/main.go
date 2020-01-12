package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	func2()
}

// func1 only consumes userspace memory.
func func1() {
	memoryTicker := time.NewTicker(time.Millisecond * 5)
	leak := make(map[int][]byte)
	i := 0

	go func() {
		for range memoryTicker.C {
			leak[i] = make([]byte, 1024)
			i++
		}
	}()

	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":8081", nil)
}

// func2 consumes userspace memory as well as kernel memory (cache).
func func2() {
	memoryTicker := time.NewTicker(time.Millisecond * 5)
	leak := make(map[int][]byte)
	i := 0

	go func() {
		for range memoryTicker.C {
			leak[i] = make([]byte, 1024)
			i++
		}
	}()

	fileTicker := time.NewTicker(time.Millisecond * 5)
	go func() {
		home, _ := os.UserHomeDir()
		f, _ := os.Create(fmt.Sprintf("%s/file", home))
		buffer := make([]byte, 1024)
		defer f.Close()

		for range fileTicker.C {
			f.Write(buffer)
			f.Sync()
		}
	}()

	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":8081", nil)
}
