## MPI

http://mpitutorial.com/tutorials/dynamic-receiving-with-mpi-probe-and-mpi-status/

#### Dynamic receiving

```
$ mpicc check_status.c -o check_status
$ mpirun -n 2 ./check_status
0 sent 10 numbers to 1
1 received 10 numbers from 0. Message source = 0, tag = 0
```

#### etc
