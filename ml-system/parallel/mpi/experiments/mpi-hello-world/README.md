## MPI hello world

http://mpitutorial.com/tutorials/mpi-hello-world/

#### Installation

On MacOS

```
brew install mpich2
```

On Arch, https://aur.archlinux.org/packages/mpich/

Note Arch has pre-installed Open MPI binary.

#### Run hello world

Run single instance

```
mpicc -o mpi_hello_world mpi_hello_world.c

mpirun ./mpi_hello_world
Hello world from processor Deyuans-MacBook-Pro.local, rank 0 out of 1 processors
```

Run multiple instance. Make sure hosts name in `host_file` are all accessible, e.g.
add the following contents to `/etc/hosts`.

```
127.0.0.1 host1
127.0.0.1 host2
127.0.0.1 host3
127.0.0.1 host4
```

Then run:

```
$ mpirun -n 4 -f host_file ./mpi_hello_world
Hello world from processor Deyuans-MacBook-Pro.local, rank 0 out of 4 processors
Hello world from processor Deyuans-MacBook-Pro.local, rank 2 out of 4 processors
Hello world from processor Deyuans-MacBook-Pro.local, rank 3 out of 4 processors
Hello world from processor Deyuans-MacBook-Pro.local, rank 1 out of 4 processors
```

The output of the processes is in an arbitrary order since there is no synchronization
involved before printing.
