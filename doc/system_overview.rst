System Overview
===============

This system consists of three components as shown in the following diagram.

.. uml::
   :caption: System overview

   [Virtual machine] as vm <<C++>>
   [fbuilder] <<Python>>
   [eForth] as eforth <<fvs>>

   fbuilder -> vm: builds images for
   fbuilder -> eforth: builds
   eforth -> vm: runs on

.. table::
   :widths: 20 80

   +-----------------+-------------------------------------------------------------------------------------+
   | Component       |                                                                                     |
   +=================+=====================================================================================+
   | Virtual machine | A virtual machine, implemented in C++ with an instruction set specifically designed |
   |                 | for the implementation of Forth systems. The machine should provide the minimum     |
   |                 | required for implementing a Forth but also be very close to a hardware              |
   |                 | implementable CPU. This is with the idea of eventually creating a converter for     |
   |                 | VM assembly into as many different MCU architectures as possible.                   |
   +-----------------+-------------------------------------------------------------------------------------+
   | Fbuilder        | A compiler for turning source files into binary images that can run on the virtual  |
   |                 | machine. The compiler is written in Python and understands a special language that  |
   |                 | was design to support a mix of virtual machine assembly and Forth words.            |
   +-----------------+-------------------------------------------------------------------------------------+
   | eForth          | An implementation of a Forth system. The system is implemented in the fbuilder      |
   |                 | language to develop and proof the concept of this project. As basis, the eForth86   |
   |                 | implementation by C. H. Ting is used.                                               |
   +-----------------+-------------------------------------------------------------------------------------+

