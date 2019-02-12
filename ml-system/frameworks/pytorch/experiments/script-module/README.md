# Script Module

The experiments are based on [PyTorch tutorials: Load PyTorch in C++ (and JIT)](https://pytorch.org/tutorials/advanced/cpp_export.html).

Create module via tracing or scripting:

```shell
$ python torchscript.py
$ python tracing.py
```

Then run the following to build an example C++ application (torch library v1.1 is installed via pip
install torch, there is no need to download libtorch again):

```shell
mkdir build
cd build
cmake -DCMAKE_PREFIX_PATH=$HOME/.pyenv/versions/3.6.7/lib/python3.6/site-packages/torch ..
make
```
