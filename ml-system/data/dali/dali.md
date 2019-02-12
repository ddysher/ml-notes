## DALI

DALI is a data pipeline library from NVIDIA to solve a couple issues:
- inconsistent data preprocessing in different frameworks
- CPU bottleneck for training with large amount of data

To simply put, DALI can be seen as a solution for data augmentation primarily for image tasks.
[Supported operations](https://docs.nvidia.com/deeplearning/sdk/dali-developer-guide/docs/supported_ops.html)
include:
- image transformation like resizing, sphere, etc
- data loading for TFRecords, LMDB (Caffe), RecordIO (MXNet), etc

*References*

- https://devblogs.nvidia.com/fast-ai-data-preprocessing-with-nvidia-dali
- https://docs.nvidia.com/deeplearning/sdk/dali-developer-guide/docs/index.html
