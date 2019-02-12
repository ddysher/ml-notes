package main

import (
	"bytes"
	"fmt"

	tf "github.com/tensorflow/tensorflow/tensorflow/go"
)

const (
	ModePath string = "/tmp/mnist_model/1"
)

func main() {
	model, _, err := loadModel(ModePath)
	if err != nil {
		fmt.Errorf("Failed to load '%s': %v", model, err)
		return
	}

	for _, op := range model.Graph.Operations() {
		fmt.Printf("%v, %v, %v, %v\n", op.Name(), op.Type(), op.NumInputs(), op.NumOutputs())
	}
}

func loadModel(path string) (*tf.SavedModel, []byte, error) {
	model, err := tf.LoadSavedModel(path, []string{"serve"}, nil)
	if err != nil {
		fmt.Printf("Failed to load '%s': %v\n", err)
		return nil, nil, err
	}
	buf := &bytes.Buffer{}
	model.Graph.WriteTo(buf)
	return model, buf.Bytes(), nil
}
