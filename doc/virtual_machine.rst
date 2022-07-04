VM Internals
============

Instruction set
---------------

The virtual machine implements a simple byte-code instruction set with variable amounts of parameters. The instruction mnemonics, their encoding, possible parameters and the semantics are explained in this section.

Operand types
^^^^^^^^^^^^^

All number types comprising of more than one byte are stored in little-endian format.

+--------------+--------------------------------------------------------------------------+
| Abbreviation | Explanation                                                              |
+==============+==========================================================================+
| `imm8`       | 8-bit immediate value                                                    |
+--------------+--------------------------------------------------------------------------+
| `imm16`      | 16-bit immediate value                                                   |
+--------------+--------------------------------------------------------------------------+
| `regi`       | Register or register indirect expression                                 |
+--------------+--------------------------------------------------------------------------+
| `regi_op`    | Register or register indirect expression with pre- or postfix operations |
+--------------+--------------------------------------------------------------------------+

Encodings
^^^^^^^^^

In most cases when registers need to be encoded in the opcodes, the following mapping is used.

 * `u16` - unsigned 16-bit immediate operand in little endian encoding
 * `rr` - encoding for operations between two registers
 * `rop` - encoding for operations between a direct register and indirect
   register with prefix or postfix operations

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
| ``%pc``   | 0x7      |
+-----------+----------+

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

MOV - Move
----------

.. table::
    :widths: 15 25 70

    +-----------+----------------------+---------------------------------------------+
    | Opcode    | Mnemonic             | Description                                 |
    +===========+======================+=============================================+
    | 20 `/rr`  | MOV `regi`, `regi`   | Move register to register word sized        |
    +-----------+----------------------+---------------------------------------------+
    | 21 `/rr`  | MOV.B `regi`, `regi` | Move register to register byte sized        |
    +-----------+----------------------+---------------------------------------------+

mov reg, reg
mov [reg], reg
mov reg, [reg]
mov [reg], [reg]

movi reg, imm32/imm8
movi [reg], imm32/imm8

mov [rsp++], reg   // pushr reg
mov reg, [--rsp]   // popr reg
mov [rdp++], reg   // pushd reg
mov reg, [--rdp]   // popd reg

The ``mov`` instruction is meant for all sorts of stack operations. The encoding was chosen because of the following reasons:

 * instead of using the two 4-bit nibbles for source and target register encodings, the source and target registers are encoded as 3-bit values 
   in the lowest 6 bits of the operand. Unlike ``mov``, we can't encode all possible "configurations" of source and target together with the
   register values in one 8-bit operand.
 * the only possible combinations are one indirect operand with post/prefix-operation and one immediate register operand, therefore we keep
   the configuration of the indirect operand in the highest 2 bits of the operand
 * the direction, respectively the configuration of source and target operands is encoded in the opcode; either it is an direct to indirect
   move in which case the target register is interpreted as indirect post/pre- increment or decrement or it is an indirect to direct
   move where the source register gets all the configurations

JMP - Jump instructions
-----------------------

jmp [reg]
jmp imm32 (?)

Mathematical instructions
-------------------------

add,
sub,
mod
