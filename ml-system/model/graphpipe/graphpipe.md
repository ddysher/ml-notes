<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Implementation](#implementation)
  - [Load Model](#load-model)
  - [Initialize Metadata](#initialize-metadata)
  - [Inputs/Outputs](#inputsoutputs)
  - [Handle Requests](#handle-requests)
- [Summary](#summary)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

GraphPipe's [official website](https://oracle.github.io/graphpipe/) has a concise and useful
information about the project.

# Implementation

The following implementation is based on `graphpipe-tf`, others (now `graphpipe-onnx`) works similarly.

## Load Model

graphpipe-tf first loads model uses Go API; the model is loaded either from remote url or local file
system. It will return a `SavedModel` defined in Go API.

```go
type SavedModel struct {
	Session *Session
	Graph   *Graph
}
```

## Initialize Metadata

At this stage, graphpipe initializes metadata of a model. Note instead of just using `SavedModel`
from above, it also marshals the model graph (`SavedModel.Graph`) to `tfproto.GraphDef`, which
is an internal protocol buffer.

The specification is defined as follows:

```
table MetadataResponse {
    name:string; // optional
    version:string; // optional
    server:string; // optional
    description:string; //optional
    inputs:[IOMetadata]; // required
    outputs:[IOMetadata]; // required
}
```

Note here,  `inputs/outputs` means inputs & outputs of each Node, not just the input & outputs of
the model, i.e. not just input of first & last Node.

## Inputs/Outputs

After initializing metadata, graphpipe then goes ahead and creates the inputs/outputs of the model.
Inputs and outputs can be passed in via user when launching `graphpipe-tf`; otherwise graphpipe
will use default inputs/outputs calculated when analyzing model metadata (add to default inputs if
a node is not const and has no input, etc.), i.e.

```go
func initializeMetadata(opts options, c *tfContext) *graphpipe.NativeMetadataResponse {
    ...
   	for _, node := range c.graphDef.Node {
		num := op.NumOutputs()
		for i := 0; i < num; i++ {
			if op.Type() != "Const" && t != graphpipefb.TypeNull {
				if len(node.Input) == 0 {
					c.defaultInputs = append(c.defaultInputs, name)
				} else if _, present := outputsThatAreInputs[node.Name]; !present {
					// register terminal outputs as default outputs
					c.defaultOutputs = append(c.defaultOutputs, name)
				}
			}
		}
	}
    ...
}
```

## Handle Requests

Each framework format (e.g. tensorflow, onnx) has its own logic to handle loading model and finding
`inputs/outputs`. After the two stages, graphpipe then handles serving request via a generic method
`server.goServeRaw`. The function will parse request from client, which is graphpipe defined format.
There are two types of requests: MetadataRequest and ReqInferRequest. For MetadataRequest, generic
handler will return model metadata directly. For ReqInferRequest, generic handler will call framework
specific handler (the `apply` method); before invoking `apply`, generic handle will first extract
input tnesors and output names:

```go
func getResults(c *appContext, requestContext *RequestContext, req *graphpipefb.InferRequest) ([]*NativeTensor, error) {
	inputMap, err := getInputMap(c, req)
	if err != nil {
		return nil, err
	}
	outputNames, err := getOutputNames(c, req)
	if err != nil {
		return nil, err
	}
	return c.apply(requestContext, string(req.Config()), inputMap, outputNames)
}

```

In graphpipe-tf `apply` method, it invokes model.Session to run the model with given input, i.e.

```go
func (tfc *tfContext) apply(requestContext *graphpipe.RequestContext, config string, inputs map[string]*graphpipe.NativeTensor, outputNames []string) ([]*graphpipe.NativeTensor, error) {
    ...
	tensors, err := tfc.model.Session.Run(
		inputMap,
		outputRequests,
		nil,
	)
    ...
}
```

After returning from `apply`, generic handler will serialize it and send back to clients.

# Summary

Below is the full workflow from graphpipe.

![](./assets/server_flow.png)
