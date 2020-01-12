# BLAS

The BLAS (Basic Linear Algebra Subprograms) are routines that provide standard building blocks for
performing basic vector and matrix operations.
- The Level 1 BLAS perform scalar, vector and vector-vector operations
- The Level 2 BLAS perform matrix-vector operations
- The Level 3 BLAS perform matrix-matrix operations.

There are many different implementation of BLAS, including MLK, OpenBLAS, cuBLAS, etc. Because the
BLAS are efficient, portable, and widely available, they are commonly used in the development of
high quality linear algebra software, e.g. LAPACK.

**Sparse BLAS**

The Sparse BLAS interface also defines 3 levels for sparse vector & matrix operations.

*References*

- http://www.netlib.org/blas/
- https://math.nist.gov/spblas/
- https://stackoverflow.com/questions/1303182/how-does-blas-get-such-extreme-performance
- https://petewarden.com/2015/04/20/why-gemm-is-at-the-heart-of-deep-learning/
