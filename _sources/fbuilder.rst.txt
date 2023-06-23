FBuilder
========

FBuilder is an assembler and a language specifically designed for the implementation of Forth 
systems. The assembler is implemented in Python and converts fvs (Forth VM source) files into
binary images that can be run by the virtual machine. 

The fvs- or Fbuilder- language supports a mix of assembly and Forth source code. For Forth only
compiled words are supported, it is not possible to use any of the immediate words like ``IF``, 
``BEGIN`` or ``REPEAT``.

An Example
----------

The following example only uses machine instructions from the VM and the Fbuilder language to
implement a simple hello world programm. The meaning of individual code lines are explained below.

.. code-block::
    :linenos:

    const FKT_EMIT = 0x2
    const FKT_TERMINATE = 0xf0

    codeblock
        mov %acc1, :hello
        mov %acc2, %acc1
    next_char:
        mov.b %acc1, [%acc2++]
        ifkt FKT_EMIT

        mov %acc1, :hello_end
        sub %acc1, %acc1, %acc2
        jz :terminate
        jmp :next_char
    terminate:
        ifkt FKT_TERMINATE

    hello:
        db "Hello world"
        db #10
        db #13
    hello_end:
    end

The **lines 1-2** define the constants to use in the ``ifkt`` instructions for emitting a
character on the screen and for terminating the VM.

On **line 4** a code block for our hello world application is started. This block is
closed again on **line 23**.

In **lines 5 and 6** we copy the address of the ``"Hello world"`` text, defined from **lines
18 to 22**,  into the ``%acc2`` register. Notice that we need to move the value through the
``%acc1`` register, because we can't move immediate values directly into ``%acc1``.

In **line 8** we fetch one character of the text indirectly through register ``%acc2`` and
store it in register ``%acc1``. Right after the access, the ``%acc2`` is incremented to
point to the next character in the text. Using an interface function we then output this
character from register ``%acc1`` in **line 9**.

On **lines 11 and 12** we calculate the difference between the current character position
stored in register ``%acc2`` and the end of the text, marked with the label ``hello_end``.
This difference then ends up in register ``%acc1``.

Using the calculated difference in register ``%acc1`` we then decide whether to jump on 
**line 13**. If the value in the register equals zero, we jump to the ``terminate`` label
in order to finish outputing of the text. If the value is not equal to zero, execution
simply continues on the next line.

On this next, **line 14**, we unconditionally jump back to **line 7** to output the
next character.

Finally on **line 16** we terminate the virtual machine using another interface function.

The **lines 19-21** define the text data that we want to output.

The codeblock is compiled to memory location ``0x0`` in the generated binary image. This
image can then be loaded by the virtual machine which starts running at address ``0x0``.