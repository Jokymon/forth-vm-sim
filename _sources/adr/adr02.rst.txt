Choice of programming languages
-------------------------------

.. adr::
    :last_update: 6.7.2023
    :status: active

Problem
^^^^^^^

For the implementation of the virtual machine and the assembler, fitting
programming languages need to be chosen. Since this project is pretty
much free standing and has no dependencies on any other library, framework
or application and since there will most likely only ever be one developer,
the constraints aren't very tight.

Options
^^^^^^^

**C++** is a compiled, system level, mixed paradigm programming language. It is
well suited for high performance applications and for embedded software development
with ressource constraints. The main developer is very familiar with this language
and has used it for over a decade so far.

**Python** is a compiled/interpreted, VM-based, object oriented scripting language.
It is well suited for fast prototyping and is widely spread in the AI/ML community.
The main developer is very familiar with this language and has used it for over a
decade so far.

**Rust** is a compiled, system level, mixed paradigm programming language. It is
well suited for security sensible and high performance applications. It also
allows for bare metal embedded programming using a reduced standard library.
The main developer is fairly familiar with this language but has never developed
any major application with it.

**Java** is a compiled mixed paradigm programming language running on a virtual
machine. It is well suited for platform independent backend programming.
The main developer is fairly familiar with this language but has never developed
any major application with it.

**JavaScript** Is an interpreted, object oriented programming language running in
a virtual machine, usually inside a browser. It is the goto-language for web
applications and allows for platform independent programming.
The main developer is familiar with the core concepts of the language and has
implemented a few very small web applications that involve some JavaScript code.

**C#** Is a compiled language running on a virtual machine similar to Java. It
is also well suited for platform independent software development.
The main developer has never written any C# code and is mostly unfamiliar with
the language.

**Many others.** Beyond the languages listed above, many more languages would be
potential candidates for this project. However since the main developer is not very
or not at all familiar with them, they were excluded from the beginning.

Solution
^^^^^^^^

Because the focus of this project was to explore Forth systems, the
implementation languages should not put too much burden on the development.
Therefore languages familiar to the main developer were chosen.

**C++ and Python**

The reasoning for chosing C++ for the virtual machine was, that it would be
closer to any target system (closer to C/machine language) and that it could
potentially even be used to port this entire system to a small MCU.

The reasoning for chosing Python for the assembler was, that Python is very
well suited for string/language processing and due to its scripting nature,
allows for very fast development cycles.