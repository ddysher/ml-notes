// Author: Wes Kendall
// Copyright 2011 www.mpitutorial.com
// This code is provided freely with the tutorials on mpitutorial.com. Feel
// free to modify it for your own use. Any distribution of the code must
// either provide a link to www.mpitutorial.com or keep this header intact.
//
// MPI_Send, MPI_Recv example. Communicates the number -1 from process 0
// to process 1.
//

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
  // Initialize the MPI environment.
  MPI_Init(NULL, NULL);

  // Find out rank, size. rank will be different on different process,
  // while size is the same across all processes.
  int world_rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
  int world_size;
  MPI_Comm_size(MPI_COMM_WORLD, &world_size);

  // We are assuming at least 2 processes for this task.
  if (world_size < 2) {
    fprintf(stderr, "World size must be greater than 1 for %s\n", argv[0]);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  // MPI_Send and MPI_Recv signature:
  //
  // MPI_Send(
  //   void* data,
  //   int count,
  //   MPI_Datatype datatype,
  //   int destination,
  //   int tag,
  //   MPI_Comm communicator)
  //
  // MPI_Recv(
  //   void* data,
  //   int count,
  //   MPI_Datatype datatype,
  //   int source,
  //   int tag,
  //   MPI_Comm communicator,
  //   MPI_Status* status)
  //
  // data - pointer to data buffer
  // count - exact number of data to send, and MAXIMUM number of data to receive
  // datatype - type of data, predefined in MPI
  // source/destination - rank of process to send/receive message
  // tag - identification of message
  // communicator - communicator of the two processes
  // status - information about the received message

  int number;
  if (world_rank == 0) {
    // If we are rank 0, set the number to be sent to '-1' and send it to process
    // 1. The message is tagged with 0 and uses 'MPI_COMM_WORLD' as communicator.
    // A communicator defines a group of processes that have the ability to communicate
    // with one another; here we use "MPI_COMM_WORLD" where all processes are part of.
    number = -1;
    MPI_Send(&number, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
    printf("Process 0 sent number %d to process 1\n", number);
  } else if (world_rank == 1) {
    // If we are rank 1, receive the number. MPI_Recv will block for a message
    // with a matching tag and sender.
    MPI_Recv(&number, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    printf("Process 1 received number %d from process 0\n", number);
  }

  MPI_Finalize();
}
