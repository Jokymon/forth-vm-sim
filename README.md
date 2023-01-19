Forth VM Simulator
==================

The goal of this project is to implement a handy environment for playing around with concepts,
the language and the system "Forth". Many Forth-implementations for various micro controllers
and platforms exist, but for me, to try and better understand what is actually necessary and
how it works, I wanted to create my own simple virtual machine to implement my own Forth system.

So far, you will find these major components in this project:

  - A custom virtual machine for running and debugging binaries (implemented in C++)
  - A Forth to binary compiler to turn "high-level" Forth words and some assembly code into
    binary images that can be run by the VM (implemented in Python)
  - Parts of a Forth system implementation inspired by ideas from JonesForth and eForth
    (implemented my own custom language mix of VM assembly and Forth words called 'fvs'-files)

More detailed documentation can be found as ReStructured text in the `doc`-folder.

Getting started
---------------

To get started with this project, you will need a C++ compiler with C++11 support, a CMake
version >= 3.23 and a Python installation version >=3.8. Then you need to compile the VM so
that you can run any compiled Forth VM binaries.

Under Windows, a MinGW version 8.1.0 posix SEH for example is proven to work

To build the VM run

```
mkdir build
cd build
cmake ..
cmake --build .
```

For Ubuntu
^^^^^^^^^^

```
sudo apt-get install libncurses5-dev libncursesw5-dev
```

Issues
------

For wavedrom the Python library xcffib needs to be uninstalled
