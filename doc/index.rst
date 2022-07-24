Welcome to Forth virtual machine's documentation!
=================================================

This project implements a small Forth experimentation environment. The project
is meant for learning about the Forth internals, playing around with it and
hopefully eventually for porting a Forth environment to a baremetal system on
an MCU.

The project consists of the following components:

 * A virtual machine with a simple, Forth-specific instruction set, implemented
   in C++
 * A compiler/assembler for compiling assembly and Forth code to binary images
   used by the virtual macihine, implemented in Python

Scope of the project
--------------------

The guiding goals of this project when making design decisions are as follows

 * Support for various threading strategies (at least for DTC and ITC)
 * Possibility to port the sources to an MCU architecture
 * Simple debugger to verify own Forth system implementations

The following items are explicitly not in scope of this project

 * Embeddable virtual machine
 * 100% Forth standard compliance

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   system_overview
   forth
   virtual_machine
   design_decisions


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
