#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
  // Initialize the MPI environment. During MPI_Init, all of MPI’s global and internal
  // variables are constructed. For example, a communicator (MPI_COMM_WORLD) is
  // formed around all of the processes that were spawned, and unique ranks are
  // assigned to each process.
  MPI_Init(NULL, NULL);

  // Get the number of processes. MPI_Comm_size returns the size of a communicator.
  // In our example, MPI_COMM_WORLD (which is constructed for us by MPI) encloses
  // all of the processes in the communicator, so this call should return the amount
  // of processes that were requested for the communicator.
  int world_size;
  MPI_Comm_size(MPI_COMM_WORLD, &world_size);

  // Get the rank of the process. MPI_Comm_rank returns the rank of a process in
  // a communicator. Each process insides of a communicator is assigned an
  // incremental rank starting from zero. The ranks of the processes are primarily
  // used for identification purposes when sending and receiving messages.
  int world_rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

  // Get the name of the processor.
  char processor_name[MPI_MAX_PROCESSOR_NAME];
  int name_len;
  MPI_Get_processor_name(processor_name, &name_len);

  // Print off a hello world message.
  printf("Hello world from processor %s, rank %d"
         " out of %d processors\n",
         processor_name, world_rank, world_size);

  // Finalize the MPI environment.
  MPI_Finalize();
}
