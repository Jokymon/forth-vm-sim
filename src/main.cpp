#include "vm.h"
#include <iostream>

int main(int argc, char* argv[])
{
    Vm vm;

    auto res = vm.interpret();

    switch (res) {
        case Vm::Error:
            std::cout << "Error during byte code interpretation\n";
            break;

        case Vm::Finished:
            std::cout << "Byte code interpretation successful\n";
            break;

        case Vm::IllegalInstruction:
            std::cout << "Interpreter hit invalid instruction\n";
            break;
    }

    return 0;
}
