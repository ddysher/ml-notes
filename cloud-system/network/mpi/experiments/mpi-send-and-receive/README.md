## MPI

http://mpitutorial.com/tutorials/mpi-send-and-receive/

#### Send and Receive

```
$ mpicc send_recv.c -o send_recv
$ mpirun -n 2 ./send_recv
Process 0 sent number -1 to process 1
Process 1 received number -1 from process 0
```

#### etc
