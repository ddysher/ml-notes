<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Dataset](#dataset)
  - [Protobuf Definitions](#protobuf-definitions)
    - [Feature](#feature)
    - [Features](#features)
    - [Example](#example)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Dataset

## Protobuf Definitions

Important protocol buffer definitions:

### Feature

Each feature proto represents a feature in dataset, for example:
- in a movie recommendataion dataset, `movie_rating` is a float feature
- in an image dataset, `weight` is an int feature

Following is the fundamental feature values. Note each value is a list.

```protobuf
// Containers to hold repeated fundamental values.
message BytesList {
  repeated bytes value = 1;
}
message FloatList {
  repeated float value = 1 [packed = true];
}
message Int64List {
  repeated int64 value = 1 [packed = true];
}
```

And feature proto is simply a union of the three value types:

```proto
// Containers for non-sequential data.
message Feature {
  // Each feature can be exactly one kind.
  oneof kind {
    BytesList bytes_list = 1;
    FloatList float_list = 2;
    Int64List int64_list = 3;
  }
};
```

The definitions can be found at `tensorflow/core/example/feature.proto`.

### Features

Features is a collection of named features: it is defined as a map from feature name to feature proto.

```proto
message Features {
  // Map from feature name to feature.
  map<string, Feature> feature = 1;
};
```

The definitions can be found at `tensorflow/core/example/feature.proto`.

### Example

Each example is a single instance from a dataset, e.g. an image from image dataset, movie recommendation
of a user, etc. Example stores Features as a single attribute.

```protobuf
message Example {
  Features features = 1;
};
```

# References

- http://warmspringwinds.github.io/tensorflow/tf-slim/2016/12/21/tfrecords-guide/
- https://medium.com/mostly-ai/tensorflow-records-what-they-are-and-how-to-use-them-c46bc4bbb564
- https://www.tensorflow.org/tutorials/load_data/tf_records
