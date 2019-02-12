<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview & Concepts](#overview--concepts)
  - [Communicator](#communicator)
  - [Rank](#rank)
  - [Tag](#tag)
  - [Point-to-point communication](#point-to-point-communication)
  - [Collective communication](#collective-communication)
  - [Scatter, [All]Gather, [All]Reduce](#scatter-allgather-allreduce)
- [Projects](#projects)
  - [mpiexec (mpirun)](#mpiexec-mpirun)
  - [slurm](#slurm)
  - [MPICH](#mpich)
  - [Open MPI](#open-mpi)
  - [MPMD](#mpmd)
- [Comparison](#comparison)
  - [MPI vs MapReduce](#mpi-vs-mapreduce)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview & Concepts

Message Passing Interface (MPI) is a standardized and portable message-passing standard designed by
a group of researchers from academia and industry to function on a wide variety of parallel computing
architectures. The standard defines the syntax and semantics of a core of library routines useful to
a wide range of users writing portable message-passing programs in C, C++, and Fortran.

## Communicator

A communicator defines a group of processes that have the ability to communicate with one another.

## Rank

In communicator, each is assigned a unique rank, and they explicitly communicate with one another
by their ranks.

## Tag

The foundation of communication is built upon send and receive operations among processes. A process
may send a message to another process by providing the rank of the process and a unique tag to
identify the message.

## Point-to-point communication

Communications which involve one sender and receiver are known as point-to-point communications.

## Collective communication

Communications that involve all processes. Mixtures of point-to-point and collective communications
can be used to create highly complex parallel programs.

## Scatter, [All]Gather, [All]Reduce

Refer to experiments.

# Projects

## mpiexec (mpirun)

Both are used to launch MPI jobs; they are actually alias to each other. mpiexec uses remote shell
program to create new processes on selected nodes.

## [slurm](https://slurm.schedmd.com/)

The Slurm Workload Manager (formerly known as Simple Linux Utility for Resource Management or SLURM),
or Slurm, is a free and open-source job scheduler for Linux and Unix-like kernels, used by many of
the world's supercomputers and computer clusters. While mpiexec is simple and sufficient for simple
programs; Slurm is commonly used to schedule jobs of complex MPI programs.

## MPICH

MPICH, formerly known as MPICH2, is a freely available, portable implementation of MPI, a standard
for message-passing for distributed-memory applications used in parallel computing.

## Open MPI

Open MPI is a Message Passing Interface (MPI) library project combining technologies and resources
from several other projects (FT-MPI, LA-MPI, LAM/MPI, and PACX-MPI).

## MPMD

Usually, MPI share a single program and depends on communicator, rank, etc to divide tasks. A multiple
program multiple data (MPMD) application uses two or more programs to functionally decompose a problem.
This style can be used to simplify the application source and reduce the size of spawned processes.

ref: https://www.ibm.com/support/knowledgecenter/en/SSF4ZA_9.1.4/pmpi_guide/running_mpmd_apps_mpi.html

# Comparison

## MPI vs MapReduce

You could understand Map-Reduce as a subset of MPI-functionality, as it kind of resembles MPIs
collective operations with user-defined functions. Thus you can use MPI instead of Map-Reduce but
not vice-versa, as in MPI you can describe many more operations. The main advantage of Map-Reduce
seems to be this concentration on this single parallel concept, thereby reducing interfaces that
you need to learn in order to use it.

ref: [stackoverflow](https://stackoverflow.com/questions/9418782/comparision-between-mpi-standard-and-map-reduce-programming-model)
