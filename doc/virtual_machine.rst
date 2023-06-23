VM Internals
============

System
------

The virtual machine is a 32-bit, little endian, byte code interpreter. The guiding idea was to provide as few different instructions 
as possible so that they can easily be mapped to real processor architectures. It contains a simple 32-bit integer arithemtic ALU, a
simple memory interface to access code and data memory, 8 32-bit registers and the carry flag.

The following registers represent the state of processor

+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Register | Function                                                                                                                                                                            |
+==========+=====================================================================================================================================================================================+
| PC       | Program Counter; This register points at the currently executed assembler instruction.                                                                                              |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| IP       | Instruction Pointer;                                                                                                                                                                                 |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| WP       | Word Pointer;                                                                                                                                                                                 |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| RSP      | Return Stack Pointer;                                                                                                                                                               |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DSP      | Data Stack Pointer;                                                                                                                                                                 |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ACC1     | Accumulator 1; This register is intended as a general purpose register for various calculations. The accumulator 1 is the only register that can be loaded from an immediate value. |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ACC2     | Accumulator 2;                                                                                                                                                                      |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| RET      | Return Pointer;                                                                                                                                                                     |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Carry    | The carry flag; This flag can only be affected by the arithmetic operations add and sub.                                                                                            |
|          | The flag is used by the jc jump instruction to conditionally jump based on over- or underflow                                                                                       |
|          | in the last add or sub operation.                                                                                                                                                   |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Instruction set
---------------

The virtual machine implements a simple byte-code instruction set with variable amounts of parameters. The instruction mnemonics, their encoding, possible parameters and the semantics are explained in this section.

Operand types
^^^^^^^^^^^^^

+--------------+--------------------------------------------------------------------------+
| Abbreviation | Explanation                                                              |
+==============+==========================================================================+
| `imm5`       | 5-bit immediate value                                                    |
+--------------+--------------------------------------------------------------------------+
| `imm8`       | 8-bit immediate value                                                    |
+--------------+--------------------------------------------------------------------------+
| `imm16`      | 16-bit immediate value                                                   |
+--------------+--------------------------------------------------------------------------+
| `imm32`      | 32-bit immediate value                                                   |
+--------------+--------------------------------------------------------------------------+
| `label`      | 32-bit jump target address                                               |
+--------------+--------------------------------------------------------------------------+
| `reg`        | A register                                                               |
+--------------+--------------------------------------------------------------------------+
| `regi`       | Register or register indirect expression                                 |
+--------------+--------------------------------------------------------------------------+
| `regi_op`    | Register or register indirect expression with pre- or postfix operations |
+--------------+--------------------------------------------------------------------------+

Encodings
^^^^^^^^^

In most cases when registers need to be encoded in the opcodes, the following mapping is used.

+-----------+----------+
| Register  | Encoding |
+===========+==========+
| ``%ip``   | 0x0      |
+-----------+----------+
| ``%wp``   | 0x1      |
+-----------+----------+
| ``%rsp``  | 0x2      |
+-----------+----------+
| ``%dsp``  | 0x3      |
+-----------+----------+
| ``%acc1`` | 0x4      |
+-----------+----------+
| ``%acc2`` | 0x5      |
+-----------+----------+
| ``%ret``  | 0x6      |
+-----------+----------+
| ``%pc``   | 0x7      |
+-----------+----------+

All number types comprising of more than one byte are stored in little-endian format.

.. list-table::
    :header-rows: 1

    * - Encoding
      - Description

    * - ``u16``
      - A 16-bit unsigned integer value in little-endian encoding

    * - ``u32``
      - A 32-bit unsigned integer value in little-endian encoding

    * - ``reg``
      - A register as encoded above; This encoding is only used as summand
        in encodings and therefore doesn't have a specified bit length

    * - ``rr``
      - .. wavedrom:: images/encoding_rr.json

        - ``DI_T`` Flag to indicate whether the target register is used
          direct or indirect. A ``1`` means indirect.
        - ``reg_tgt`` The target register encoded as described above.
        - ``DI_S`` Flag to indicate whether the source register is used
          direct or indirect. A ``1`` means indirect.
        - ``reg_src`` The source register encoded as described above.

    * - ``3r``
      - .. wavedrom:: images/encoding_3r.json

        - ``reg_tgt`` The target register encoded as described above
        - ``reg_src1`` The first source register encoded as described above
        - ``reg_src2`` The second source register encoded as described above

    * - ``rop``
      - .. wavedrom:: images/encoding_rop.json

        - ``DI`` Flag to indicate what operation is to be performed on the
          target register. A ``1`` means decrement, ``0`` means increment.
        - ``PP`` Flag to indicate whether the operation is performed before
          before indirectly accessing memory or after. A ``1`` means pre
          operation, a ``0`` means post operation.
        - ``reg_tgt`` The register encoded as described above used as target
          indication.
        - ``reg_src`` The register encoded as described above used as source
          indication.

    * - ``ri5``
      - .. wavedrom:: images/encoding_ri5.json

        - ``reg`` The affected register encoded as described above.
        - ``val5`` A 5-bit immediate value.

ADD - Add
---------

.. table::
    :widths: 15 25 70

    +-----------+---------------------------------------+-------------------------+
    | Opcode    | Mnemonic                              | Description             |
    +===========+=======================================+=========================+
    | 30 `/3r`  | ADD `reg_tgt`, `reg_src1`, `reg_src2` | Add values in registers |
    +-----------+---------------------------------------+-------------------------+

This instruction adds the registers ``reg_src1`` and ``reg_src2`` together and stores
the result in the register ``reg_tgt``. The addition is performed unsigned.

In case of overflows, the carry flag is set. Otherwise the carry flag is cleared.

CALL - Call
-----------

.. table::
    :widths: 15 25 70

    +-----------+-----------------+--------------------------------------------------+
    | Opcode    | Mnemonic        | Description                                      |
    +===========+=================+==================================================+
    | 73 `/u32` | CALL `label`    | Jump to immediate address and store the          |
    |           |                 | following address in the ``%ret`` register.      |
    +-----------+-----------------+--------------------------------------------------+


IFKT - Interface functions
--------------------------

.. table::
    :widths: 15 25 70

    +-----------+--------------+---------------------------------------------+
    | Opcode    | Mnemonic     | Description                                 |
    +===========+==============+=============================================+
    | FE `/u16` | IFKT `imm16` | Calling virtual machine interface functions |
    +-----------+--------------+---------------------------------------------+

Allows calling certain functions special to the virtual machine.

The virtual machine currently support the following interface functions.

.. table::
    :widths: 15 20 65

    +------+---------------+-------------------------------------------------------+
    | Code | Short Name    | Function description                                  |
    +======+===============+=======================================================+
    | 0x01 | ``INPUT``     | Read one character from the keyboard and store the    |
    |      |               | ASCII code in the ``%acc1``` register.                |
    +------+---------------+-------------------------------------------------------+
    | 0x02 | ``OUTPUT``    | Using the byte value at the least significant         |
    |      |               | position in register ``%acc1``, print one character.  |
    +------+---------------+-------------------------------------------------------+
    | 0xF0 | ``TERMINATE`` | Terminate the virtual machine.                        |
    +------+---------------+-------------------------------------------------------+
    | 0xF2 | ``DUMP_M``    | Dump all values between the addresses specified in    |
    |      |               | the registers ``%acc1`` and ``%acc2``. The beginning  |
    |      |               | address is also dumped but not the ending. The values |
    |      |               | will always be dumped in the order from the smaller   |
    |      |               | address to the larger, no matter in what register     |
    |      |               | they are stored.                                      |
    +------+---------------+-------------------------------------------------------+

ILLEGAL - Illegal instruction
-----------------------------

.. table::
    :widths: 15 25 70

    +--------+----------+---------------------+
    | Opcode | Mnemonic | Description         |
    +========+==========+=====================+
    | FF     | ILLEGAL  | Illegal instruction |
    +--------+----------+---------------------+

In general any instruction not explicitly defined is considered to be an
illegal instruction and causes the VM to abort interpretation. However for test
purposes, the mnemonic ``illegal`` and the opcode ``0xFF`` are explicitly
declared to be illegal instructions and shall remain so even with future
instruction set extensions.

JC - Jump if carry
------------------

.. table::
    :widths: 15 25 70

    +-----------+-----------------+--------------------------------------------------+
    | Opcode    | Mnemonic        | Description                                      |
    +===========+=================+==================================================+
    | 72 `/u32` | JC `label`      | Jump to immediate address when carry flag is set |
    +-----------+-----------------+--------------------------------------------------+

The carry flag can only be set and cleared by performing an ``ADD`` or ``SUB``
instruction. The ``JC`` instruction jumps to an immediate address when this carry
flag is set.

JMP - Jump unconditionally
--------------------------

.. table::
    :widths: 15 25 70

    +-------------+-------------+-------------------------------------------------+
    | Opcode      | Mnemonic    | Description                                     |
    +=============+=============+=================================================+
    | 60 + `/reg` | JMP [`reg`] | Jump to register indirect                       |
    +-------------+-------------+-------------------------------------------------+
    | 68 + `/reg` | JMP `reg`   | Jump to register direct                         |
    +-------------+-------------+-------------------------------------------------+
    | 70 `/u32`   | JMP `label` | Jump to immediate address                       |
    +-------------+-------------+-------------------------------------------------+

The register indirect jump instructions will use the register content to read a
32-bit value from the memory. Then execution jumps to the address given by this
32-bit value. Any one of the known registers can serve as register indirect
source. In case of the ``%pc`` register this may not have any meaningful purpose.

The register direct jump instruction will directly jump to the 32-bit address
location specified in the given register. Any one of the known registers can serve
as the register direct source.

The immediate address jump instruction will jump directly to the 32-bit immediate
value given as the operand of the instruction.

JZ - Jump if zero
-----------------

.. table::
    :widths: 15 25 70

    +-----------+-----------------+----------------------------------------------+
    | Opcode    | Mnemonic        | Description                                  |
    +===========+=================+==============================================+
    | 71 `/u32` | JZ `label`      | Jump to immediate address when %acc1 is zero |
    +-----------+-----------------+----------------------------------------------+

With ``JZ`` a jump to an immediate address is performed if the value of the
accumulator register ``%acc1`` has the value ``0x0``.

MOV - Move
----------

.. table::
    :widths: 15 25 70

    +-----------+------------------------+---------------------------------------------------------------------+
    | Opcode    | Mnemonic               | Description                                                         |
    +===========+========================+=====================================================================+
    | 20 `/rr`  | MOV.W `regi`, `regi`   | Move register to register word sized                                |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 21 `/rr`  | MOV.B `regi`, `regi`   | Move register to register byte sized                                |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 22 `/rop` | MOV.W `regi_op`, `reg` | Move register to register indirect memory with operation word sized |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 23 `/rop` | MOV.B `reg`, `regi_op` | Move register indirect memory to register with operation byte sized |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 24 `/rop` | MOV.W `reg`, `regi_op` | Move register indirect memory to register with operation word sized |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 25 `/rop` | MOV.B `reg`, `regi_op` | Move register indirect memory to register with operation byte sized |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 26 `/u32` | MOV.W %acc1, `imm32`   | Move an immediate 32-bit value to register acc1                     |
    +-----------+------------------------+---------------------------------------------------------------------+
    | 27 `/u32` | MOV.W %acc2, `imm32`   | Move an immediate 32-bit value to register acc2                     |
    +-----------+------------------------+---------------------------------------------------------------------+

The virtual machine support three different types of move operations.

The first type of move operations supports registers and register-indexed memory
locations. All registers and combinations of register and register-indexing are
supported. For example in the following instruction

.. code-block::

  MOV.W [%acc1], %wp

the content of register ``%wp`` is stored into the memory location specified by
the ``%acc1`` register.

For this type of move operations, byte-sized and word-sized moves are supported.
In case of byte-sized moves, only the least significant byte of the 32-bit register
is stored in memory or read from memory.

The second type of move operations are either a move operation from a register to
a register-indexed memory location or from a register-indexed memory to a register.
However the register used for the memory access will additionally be changed by
either incrementing or decrementing, either before or after accessing the memory.
For example in the following instruction

.. code-block::

  MOV.W [%dsp++], %acc1


the content of register ``%acc1`` is stored in the memory location specified by
the ``%dsp`` register. After storing the value, the value of the ``%dsp`` register
is incremented by ``4`` to point to the next word in memory. These registers are
meant for pushing register values onto stacks and popping them again.

For the third type of move operations, only the ``%acc1`` and ``%acc2`` registers 
can be used. It allows for storing immediate 32-bit values into the register. For 
example in the following instruction

.. code-block:: 

  MOV.W %acc1, #0x12345678

the immediate value ``0x12345678`` is stored into the ``%acc1`` register.

NOP - No Operation
------------------

.. table::
    :widths: 15 25 70

    +--------+----------+--------------+
    | Opcode | Mnemonic | Description  |
    +========+==========+==============+
    | 00     | NOP      | No operation |
    +--------+----------+--------------+

This instruction has no effect and can be used to fill memory.

OR - arithmetic or
------------------

.. table::
    :widths: 15 25 70

    +-----------+---------------------------------------+-------------------------------------------------+
    | Opcode    | Mnemonic                              | Description                                     |
    +===========+=======================================+=================================================+
    | 34 `/3r`  | OR `reg_tgt`, `reg_src1`, `reg_src2`  | or arithmetically values in registers           |
    +-----------+---------------------------------------+-------------------------------------------------+

This instruction ors ``reg_src2`` with ``reg_src1`` and stores the result in 
register ``reg_tgt``. The or is performed arithemtically and thus the bits are
affected individually.

SRA - Shift Right Arithmetically
--------------------------------

.. table::
    :widths: 15 25 70

    +-----------+---------------------+-------------------------------------------------------------------+
    | Opcode    | Mnemonic            | Description                                                       |
    +===========+=====================+===================================================================+
    | 3C `/ri5` | SRA.W `reg`, `imm5` | Arithmetically shift the given register right by the given amount |
    +-----------+---------------------+-------------------------------------------------------------------+

Shift the given register arithmetically right by the given 5-bit immediate value.
It shifts the most significant bit, number 31, into the following less significant
bits.

SUB - Subtract
--------------

.. table::
    :widths: 15 25 70

    +-----------+---------------------------------------+------------------------------+
    | Opcode    | Mnemonic                              | Description                  |
    +===========+=======================================+==============================+
    | 32 `/3r`  | SUB `reg_tgt`, `reg_src1`, `reg_src2` | Subtract values in registers |
    +-----------+---------------------------------------+------------------------------+

This instruction subtracts ``reg_src2`` from ``reg_src1`` and stores the result in 
register ``reg_tgt``. The subtraction is performed unsigned.

In case of underflows, the carry flag is set. Otherwise the carry flag is cleared.

XOR - arithmetic exclusive or
-----------------------------

.. table::
    :widths: 15 25 70

    +-----------+---------------------------------------+-------------------------------------------------+
    | Opcode    | Mnemonic                              | Description                                     |
    +===========+=======================================+=================================================+
    | 38 `/3r`  | XOR `reg_tgt`, `reg_src1`, `reg_src2` | exclusive or arithmetically values in registers |
    +-----------+---------------------------------------+-------------------------------------------------+

This instruction xors ``reg_src2`` with ``reg_src1`` and stores the result in 
register ``reg_tgt``. The xor is performed arithemtically and thus the bits are
affected individually.

