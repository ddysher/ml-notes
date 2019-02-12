# MAGMA

Designed to be similar to LAPACK in functionality, data storage, and interface, the MAGMA library
allows scientists to easily port their existing software components from LAPACK to MAGMA, to take
advantage of the new hybrid architectures. MAGMA users do not have to know CUDA in order to use the
library.

There are two types of LAPACK-style interfaces. The first one, referred to as the CPU interface,
takes the input and produces the result in the CPU's memory. The second, referred to as the GPU
interface, takes the input and produces the result in the GPU's memory. In both cases, a hybrid
CPU/GPU algorithm is used. Also included is MAGMA BLAS, a complementary to CUBLAS routines.

MAGMA project also includes a MagmaDNN library. MagnaDNN provides HP data analytics and machine
learning tools using MAGMA as its computational backend.

*References*

- http://icl.cs.utk.edu/projectsfiles/magma/doxygen/
- https://bitbucket.org/account/user/icl/projects/MAG
- https://stackoverflow.com/questions/9165299/blas-equivalent-of-a-lapack-function-for-gpus
