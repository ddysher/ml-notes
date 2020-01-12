# Frameworks

At the lowest level, there are interfaces like `blas`, `lapack` which provide basic linear algebra
routines. There are many different implementation of the interfaces, e.g. `mkl`, `cublas`. Here,
`blas` can be the basis for `lapack` in some cases.

Then based on the interfaces, we have higher-level numerical libraries like `numpy`, `eigen`, etc.
Some libraries, like `eigen`, doesn't depend a lot on blas/lapack; instead, they provide their own
alternative implementation similar to blas/lapack. On the other hand, there are also some deep
learning libraries that implement deep learning primitives using blas/lapack, and are intended to
be used for higher-level frameworks, such libraries include `mkl-dnn`, `cudnn`, etc.

At an even higher level, there are deep learning frameworks like `TensorFlow`, `PyTorch`, which
depends on many of the above libraries to implement its operation kernels, including lower-level
ones like `blas`, `mkl`, as well as higher level ones like `eigen`, `numpy`, `mkl-dnn`, etc.

At the highest level, many developer-friendly frameworks are made available, notably `keras`,
`gluon`, etc.
