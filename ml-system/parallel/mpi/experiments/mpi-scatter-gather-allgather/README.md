## MPI

http://mpitutorial.com/tutorials/mpi-scatter-gather-and-allgather/

### Concepts

**MPI_Scatter**

MPI Scatter splits data to chunks, and send chunks to different processes; each process will
receive a portion of original data. This is a one-to-many pattern.

**MPI_Gather**

MPI Gather is the inverse of MPI Scatter. Instead of spreading elements from one process to many
processes, MPI Gather takes elements from many processes and gathers them to one single process.
This routine is highly useful to many parallel algorithms, such as parallel sorting and searching.
This is a many-to-one pattern.

**MPI_Allgather**

Oftentimes it is useful to be able to send many elements to many processes (i.e. a many-to-many
communication pattern). MPI Allgather has this characteristic. Given a set of elements distributed
across all processes, MPI Allgather will gather all of the elements to all the processes.

As an example, if there are three processes X, Y, Z, each holds data A, B, C. With MPI Gather, X
will receive A,B,C, while Y and Z do not receive any data. With MPI Allgather, both X, Y, and Z
will receive A,B,C.

### Experiments

#### Average number

```
$ mpicc avg.c -o avg
$ mpirun -n 4 ./avg 100
Avg of all elements is 0.503672
Avg computed across original data is 0.503672
```

#### All average

```
$ mpicc all_avg.c -o all_avg
$ mpirun -n 4 ./all_avg 100
Avg of all elements from proc 0 is 0.499092
Avg of all elements from proc 1 is 0.499092
Avg of all elements from proc 2 is 0.499092
Avg of all elements from proc 3 is 0.499092
```
