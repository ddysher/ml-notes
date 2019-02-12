# LAPACK

LAPACK (Linear Algebra Package) is a standard software library for numerical linear algebra. It
provides routines for solving systems of linear equations and linear least squares, eigenvalue
problems, and singular value decomposition. It also includes routines to implement the associated
matrix factorizations such as LU, QR, Cholesky and Schur decomposition.

LAPACK is one level higher than BLAS: BLAS only provides low-level vector & matrix operations.
For this reason, LAPACK is built on top of the BLAS to enjoy performance boost; but it can also
be compiled independent of BLAS.

Like BLAS, LAPACK is also an interface, with an reference implementation written in Fortran. Many
newer libraries implement LAPACK, e.g. MKL from intel.

*References*

- https://stackoverflow.com/questions/17858104/what-is-the-relation-between-blas-lapack-and-atlas
