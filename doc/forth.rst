Forth overview
==============

Internals
---------

Every Forth word has a similar structure in memory and is implemented as a series of fields arranged one
after the other. Most Forth implementations use the same fields, however the order of the fields may
differ. The following diagram shows the fields and the arrangement used in this implementation.

.. image:: images/general_word.svg

The fields in detail are

    * ``link`` - A 32-bit address to the ``link``-field of the previous word in the dictionary. For
      the first word, this address is the null pointer.
    * ``flags&len`` - A 8-bit field containing flags for this word (the meaning of the flags can be
      defined by the implementation) and a 5-bit value with the length of the word name.
    * ``name`` - Varying length field containing the name of the word. The length in bytes is stored
      in the ``len`` field.
    * ``CFA`` - Code Field Address of this word. This is a 32-bit address pointing to the assembly
      code, implementing this word.
    * ``PFA`` - Parameter Field Adress. This field contains parameters relevant to this word and can
      be of varying length or even missing completely.

Depending on the type of word and the type of Forth implementation, the exact content of a word's
definition may vary. In the following sections the descriptions assume an indirect threaded code (ITC)
model of a Forth implementation.

Native word
^^^^^^^^^^^

Native words are implement purely in the assembly language of the target architecture. In this project
the target architecture is the Forth VM and the FBuilder language.

.. image:: images/code_word.svg

The ``CFA`` field simply points to the address of the ``PFA``. The ``PFA`` field contains the
assembly code implementing this word. The last part of the code is implemented by the ``$NEXT``-
macro which jumps to the next word.

Colon word
^^^^^^^^^^

Colon words are usually created through the Forth compiling word ``:``.

.. image:: images/colon_word.svg

The ``CFA`` field points to a special piece of code, usually called ``DOCOL``. The ``PFA``
field contains a list of ``CFA``-addresses making up the words of this definition. The
function of ``DOCOL`` is to iterate through the addresses in the ``PFA`` field and execute
them one by one. The last word in the word list must be the CFA of the ``EXIT`` word. This
acts as a form of return statement for this colon word.