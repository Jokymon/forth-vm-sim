#include "vm.h"
#include <args.hxx>
#include <iostream>

int main(int argc, char* argv[])
{
    args::ArgumentParser parser("Forth VM");
    args::HelpFlag help(parser, "help", "Display this help menu", {'h', "help"});
    args::ValueFlag<std::string> binaryInput(parser, "binary", "Binary file containing byte code", {'i'});
    try {
        parser.ParseCLI(argc, argv);
    }
    catch (const args::Help&) {
        std::cout << parser;
        return 0;
    }

    Vm vm;

    vm.loadImageFromFile(args::get(binaryInput));

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
