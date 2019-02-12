## MPI

http://mpitutorial.com/tutorials/mpi-reduce-and-allreduce/

### Concepts

**MPI_Reduce**

Reduce is a classic concept from functional programming. Data reduction involves
reducing a set of numbers into a smaller set of numbers via a function. MPI Reduce
will handle almost all of the common reductions that a programmer needs to do in
a parallel application.

**MPI_AllReduce**

Many parallel applications will require accessing the reduced results across all
processes rather than the root process. In a similar complementary style of MPI
Allgather to MPI Gather, MPI Allreduce will reduce the values and distribute the
results to all processes.

### Experiments

#### Reduce

```
$ mpicc reduce_avg.c -o reduce_avg
$ mpirun -n 4 ./reduce_avg 100
```

#### All reduce

```
$ mpicc reduce_stddev.c -o reduce_stddev
$ mpirun -n 4 ./reduce_stddev 100
```
