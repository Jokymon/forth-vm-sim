Implementation of stacks
------------------------

.. adr::
    :last_update: 12.9.2023
    :status: active

Problem
^^^^^^^

Forth uses two different stacks, the data stack and the return stack. For these
stacks we need to provide corresponding memory somewhere and the stack pointers
need to be initialised correctly. According to the Forth specification (citation
needed) it is left to the implementation whether these stacks are in the same
memory as dictionaries, `TIB` etc. or whether they use a separate memory.

This allows for some freedoms in the implementation of such stacks in this
Forth VM.

Options
^^^^^^^

(1) Stacks occupy the same memory as all other data
...................................................

In this variant, the implementor of a Forth has to reserve space in the
data memory that is allocated to the corresponding stacks. Before the
first stack operation is performed, they also need to initialise the stack
pointers to point to a location inside this allocated memory.

**Advantages**

 * The VM only needs one memory region that is used by everything in the
   implementation.

**Disadvantages**

 * The guiding idea of the VM was to allow for easy porting to different
   target systems. However when the stacks are placed in the same memory
   as the rest, required space and a location has to be assigned already
   when implementing a Forth system. These decisions are then fixed when
   doing the porting effort and are difficult to change.
 * Because the stacks first have to be initialised by VM code, the
   debugger can't easily determine where exactly the stack top/bottom is
   located. 

(2) Stacks are placed in dedicated memories
...........................................

In this variant, the data and return stacks are handled through dedicated
memories. The stack pointers can simply be initialised to 0x0 and both
stacks can simply grow upwards without losing generality when porting.

**Advantages**

 * No special stack initialisation is necessary.
 * Introspection into the stack gets easier for the debugger, because
   stacks can always grow in the same direction and it clear from the
   start, at what address the stack bottom is found.

**Disadvantages**

 * From the Forth perspective, access to the stack has to be handled
   through additional dedicated instructions.
 * Operations that access specific elements on the stack either require a
   series of push and pop operations or additional, dedicated assembler
   instructions.

Solution
^^^^^^^^

The decision was made for the **(2) stacks in dedicated memories** solution.
The main reasons for this are the ease of stack handling from a debugging
and initialisation perspective and the better portability to different
target systems.

For access to the stack, dedicated push and pop operations are implemented
in the virtual machine.

The push and pop operations are only implemented in the cell-sized version.
When mixing byte- and cellsized operations on the stack, it could become
difficult to keep track of whether the current top element is a byte or a
word.