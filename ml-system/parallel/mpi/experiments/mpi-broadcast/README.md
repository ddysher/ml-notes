## MPI

http://mpitutorial.com/tutorials/mpi-broadcast-and-collective-communication/

#### My Broadcast

```
$ mpicc my_bcast.c -o my_bcast
$ mpirun -n 5 ./my_bcast
Process 0 broadcasting data 100
Process 4 received data 100 from root process
Process 3 received data 100 from root process
Process 2 received data 100 from root process
Process 1 received data 100 from root process
```

#### Compare bcast

Compare hand-written broadcast (my bcast) with built-in MPI_Bcast

```
$ mpicc compare_bcast.c -o compare_bcast
$ mpirun -n 16 ./compare_bcast 100000 10
Data size = 400000, Trials = 10
Avg my_bcast time = 0.205354
Avg MPI_Bcast time = 0.101355
```
